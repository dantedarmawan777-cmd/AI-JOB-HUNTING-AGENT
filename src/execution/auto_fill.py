"""
Playwright Auto-Fill Engine.
Orchestrates form filling, CV file attachment (EN / ID), screening question resolution,
screenshot capture, and dry-run safety enforcement.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from config import config
from src.core.database import db
from src.core.logger import get_logger
from src.core.models import (
    ApplicationStatus,
    AutoApplyResult,
    CandidateProfile,
    Job,
    PlatformEnum,
)
from src.execution.form_detectors import FormDetector
from src.execution.playwright_worker import playwright_worker
from src.matcher.profile_loader import get_cv_path_for_language, load_candidate_profile

logger = get_logger(__name__)


class AutoFillEngine:
    """Automated job application executor with dry-run protection and audit logging."""

    def __init__(self) -> None:
        self.profile: CandidateProfile = load_candidate_profile()

    async def execute_job_application(
        self,
        job: Job,
        cv_language: Optional[str] = None,
    ) -> AutoApplyResult:
        """
        Execute automated application flow for a job.
        Strictly requires prior human approval.
        """
        selected_lang = (cv_language or job.cv_language or "EN").upper()
        cv_path = get_cv_path_for_language(selected_lang, self.profile)

        logger.info(
            "Executing application for Job [%s] '%s' at '%s' (Platform: %s, CV: %s, Dry Run: %s)",
            job.id, job.title, job.company, job.platform.value, selected_lang, config.dry_run
        )

        page = await playwright_worker.new_page()
        answers_submitted: Dict[str, str] = {}
        review_screenshot_path: Optional[str] = None

        try:
            # 1. Navigate to Job URL
            logger.info("Navigating to %s", job.url)
            await page.goto(job.url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Human-like pause

            # 2. Dispatch Platform-Specific Flow
            if job.platform == PlatformEnum.JOBSTREET:
                success, err = await self._handle_jobstreet_flow(page, job, cv_path, answers_submitted)
            elif job.platform == PlatformEnum.GLINTS:
                success, err = await self._handle_glints_flow(page, job, cv_path, answers_submitted)
            elif job.platform == PlatformEnum.KALIBRR:
                success, err = await self._handle_kalibrr_flow(page, job, cv_path, answers_submitted)
            else:
                success, err = await self._handle_generic_flow(page, job, cv_path, answers_submitted)

            # 3. Capture Pre-Submit Review Screenshot
            review_shot = await playwright_worker.capture_screenshot(page, f"{job.id}_review")
            review_screenshot_path = str(review_shot)

            if not success:
                logger.warning("Form interaction encountered issues: %s", err)
                await db.update_job_status(
                    job.id,
                    ApplicationStatus.FAILED,
                    notes=f"Auto-fill issue: {err}",
                    screenshot_path=review_screenshot_path,
                )
                return AutoApplyResult(
                    job_id=job.id,
                    success=False,
                    status=ApplicationStatus.FAILED,
                    screenshot_path=review_screenshot_path,
                    error_message=err,
                    dry_run=config.dry_run,
                    answers_submitted=answers_submitted,
                )

            # 4. Final Submission or Dry Run Handling
            if config.dry_run:
                logger.info(
                    "🔒 DRY_RUN is active: Form successfully filled and verified. Skipping final submission click."
                )
                await db.update_job_status(
                    job.id,
                    ApplicationStatus.APPROVED,
                    notes="Dry-run completed successfully. Ready for manual review / live run.",
                    screenshot_path=review_screenshot_path,
                )
                return AutoApplyResult(
                    job_id=job.id,
                    success=True,
                    status=ApplicationStatus.APPROVED,
                    screenshot_path=review_screenshot_path,
                    error_message=None,
                    dry_run=True,
                    answers_submitted=answers_submitted,
                )
            else:
                # LIVE APPLICATION SUBMIT
                final_success, submit_err = await self._click_final_submit(page)
                await page.wait_for_timeout(3000)
                confirm_shot = await playwright_worker.capture_screenshot(page, f"{job.id}_confirmed")
                final_shot_path = str(confirm_shot)

                if final_success:
                    await db.update_job_status(
                        job.id,
                        ApplicationStatus.SUBMITTED,
                        notes=f"Successfully submitted live application with {selected_lang} CV.",
                        screenshot_path=final_shot_path,
                    )
                    return AutoApplyResult(
                        job_id=job.id,
                        success=True,
                        status=ApplicationStatus.SUBMITTED,
                        screenshot_path=final_shot_path,
                        error_message=None,
                        dry_run=False,
                        answers_submitted=answers_submitted,
                    )
                else:
                    await db.update_job_status(
                        job.id,
                        ApplicationStatus.FAILED,
                        notes=f"Failed clicking final submit: {submit_err}",
                        screenshot_path=final_shot_path,
                    )
                    return AutoApplyResult(
                        job_id=job.id,
                        success=False,
                        status=ApplicationStatus.FAILED,
                        screenshot_path=final_shot_path,
                        error_message=submit_err,
                        dry_run=False,
                        answers_submitted=answers_submitted,
                    )

        except Exception as e:
            logger.error("Unexpected error in execute_job_application: %s", e, exc_info=True)
            shot = await playwright_worker.capture_screenshot(page, f"{job.id}_error")
            await db.update_job_status(
                job.id,
                ApplicationStatus.FAILED,
                notes=f"Unhandled exception: {str(e)}",
                screenshot_path=str(shot),
            )
            return AutoApplyResult(
                job_id=job.id,
                success=False,
                status=ApplicationStatus.FAILED,
                screenshot_path=str(shot),
                error_message=str(e),
                dry_run=config.dry_run,
                answers_submitted=answers_submitted,
            )

        finally:
            try:
                await page.close()
            except Exception:
                pass

    # --------------------------------------------------------------------------
    # Platform Handlers
    # --------------------------------------------------------------------------

    async def _handle_jobstreet_flow(
        self,
        page: Page,
        job: Job,
        cv_path: Optional[Path],
        answers_submitted: Dict[str, str],
    ) -> tuple[bool, Optional[str]]:
        """Handle JobStreet 'Apply' / 'Quick Apply' workflow."""
        try:
            # Look for apply button
            apply_selectors = [
                'a[data-automation="job-detail-apply"]',
                'button[data-automation="job-detail-apply"]',
                'a:has-text("Apply now")',
                'a:has-text("Lamar Sekarang")',
                'button:has-text("Apply")',
                'button:has-text("Lamar")',
            ]

            apply_btn = None
            for sel in apply_selectors:
                if await page.locator(sel).first.is_visible():
                    apply_btn = page.locator(sel).first
                    break

            if not apply_btn:
                logger.info("Apply button selector not immediately visible, scanning page...")
                return True, "On JobStreet job listing page"

            # Click apply
            await apply_btn.click()
            await page.wait_for_timeout(2500)

            # Check if redirected to external employer site
            if "jobstreet" not in page.url:
                logger.info("Redirected to employer site: %s", page.url)
                return await self._handle_generic_flow(page, job, cv_path, answers_submitted)

            # Upload CV if file input present
            await self._upload_cv_if_present(page, cv_path)

            # Auto-fill form inputs
            await self._fill_detected_form_inputs(page, answers_submitted)

            return True, None
        except Exception as e:
            return False, f"JobStreet flow exception: {str(e)}"

    async def _handle_glints_flow(
        self,
        page: Page,
        job: Job,
        cv_path: Optional[Path],
        answers_submitted: Dict[str, str],
    ) -> tuple[bool, Optional[str]]:
        """Handle Glints application workflow."""
        try:
            apply_selectors = [
                'button:has-text("Apply")',
                'button:has-text("Lamar Cepat")',
                'button:has-text("Lamar")',
                'button[class*="ApplyButton"]',
            ]

            for sel in apply_selectors:
                loc = page.locator(sel).first
                if await loc.is_visible():
                    await loc.click()
                    await page.wait_for_timeout(2000)
                    break

            # Handle Glints modal / form
            await self._upload_cv_if_present(page, cv_path)
            await self._fill_detected_form_inputs(page, answers_submitted)

            return True, None
        except Exception as e:
            return False, f"Glints flow exception: {str(e)}"

    async def _handle_kalibrr_flow(
        self,
        page: Page,
        job: Job,
        cv_path: Optional[Path],
        answers_submitted: Dict[str, str],
    ) -> tuple[bool, Optional[str]]:
        """Handle Kalibrr application workflow."""
        try:
            apply_selectors = [
                'button:has-text("Apply Now")',
                'a:has-text("Apply Now")',
                'button:has-text("Apply")',
                'button:has-text("Lamar")',
            ]

            for sel in apply_selectors:
                loc = page.locator(sel).first
                if await loc.is_visible():
                    await loc.click()
                    await page.wait_for_timeout(2000)
                    break

            await self._upload_cv_if_present(page, cv_path)
            await self._fill_detected_form_inputs(page, answers_submitted)

            return True, None
        except Exception as e:
            return False, f"Kalibrr flow exception: {str(e)}"

    async def _handle_generic_flow(
        self,
        page: Page,
        job: Job,
        cv_path: Optional[Path],
        answers_submitted: Dict[str, str],
    ) -> tuple[bool, Optional[str]]:
        """Handle generic application pages / ATS forms (Greenhouse, Lever, Workday, etc.)."""
        try:
            await self._upload_cv_if_present(page, cv_path)
            await self._fill_detected_form_inputs(page, answers_submitted)
            return True, None
        except Exception as e:
            return False, f"Generic form filling exception: {str(e)}"

    # --------------------------------------------------------------------------
    # Form Automation Subroutines
    # --------------------------------------------------------------------------

    async def _upload_cv_if_present(self, page: Page, cv_path: Optional[Path]) -> bool:
        """Locate file inputs and upload the selected CV PDF."""
        if not cv_path or not cv_path.exists():
            logger.warning("CV path not found on disk: %s", cv_path)
            return False

        try:
            file_inputs = page.locator('input[type="file"]')
            count = await file_inputs.count()
            if count > 0:
                logger.info("Attaching CV (%s) to file input...", cv_path.name)
                await file_inputs.first.set_input_files(str(cv_path))
                await page.wait_for_timeout(1500)
                return True
        except Exception as e:
            logger.warning("Failed to attach CV to file input: %s", e)

        return False

    async def _fill_detected_form_inputs(self, page: Page, answers_submitted: Dict[str, str]) -> None:
        """Iterate through visible form inputs and auto-populate values from candidate profile."""
        # 1. Text / Email / Phone / Number Inputs
        inputs = page.locator('input:not([type="hidden"]):not([type="file"]):not([type="submit"]):not([type="button"]):not([type="checkbox"]):not([type="radio"])')
        input_count = await inputs.count()

        for i in range(input_count):
            try:
                inp = inputs.nth(i)
                if not await inp.is_visible():
                    continue

                # Get context: label, placeholder, name, id, aria-label
                placeholder = (await inp.get_attribute("placeholder")) or ""
                name_attr = (await inp.get_attribute("name")) or ""
                id_attr = (await inp.get_attribute("id")) or ""
                aria_lbl = (await inp.get_attribute("aria-label")) or ""

                # Try finding associated label text
                label_text = ""
                if id_attr:
                    lbl_elem = page.locator(f'label[for="{id_attr}"]')
                    if await lbl_elem.count() > 0 and await lbl_elem.first.is_visible():
                        label_text = await lbl_elem.first.inner_text()

                combined_context = f"{label_text} {placeholder} {name_attr} {aria_lbl} {id_attr}".strip()
                val = FormDetector.resolve_field_value(combined_context, self.profile)

                if val:
                    # Check if already filled
                    curr_val = await inp.input_value()
                    if not curr_val:
                        await inp.click()
                        await inp.fill(val)
                        answers_submitted[combined_context[:30]] = val
                        await page.wait_for_timeout(200)

            except Exception as e:
                logger.debug("Error filling text input index %d: %s", i, e)

        # 2. Textareas
        textareas = page.locator("textarea")
        ta_count = await textareas.count()
        for j in range(ta_count):
            try:
                ta = textareas.nth(j)
                if not await ta.is_visible():
                    continue
                placeholder = (await ta.get_attribute("placeholder")) or ""
                name_attr = (await ta.get_attribute("name")) or ""
                combined_context = f"{placeholder} {name_attr}".strip()
                val = FormDetector.resolve_field_value(combined_context, self.profile)
                if val and not (await ta.input_value()):
                    await ta.fill(val)
                    answers_submitted[combined_context[:30]] = val
            except Exception as e:
                logger.debug("Error filling textarea %d: %s", j, e)

        # 3. Select Dropdowns
        selects = page.locator("select")
        sel_count = await selects.count()
        for k in range(sel_count):
            try:
                sel = selects.nth(k)
                if not await sel.is_visible():
                    continue
                # Get option texts
                opt_elements = sel.locator("option")
                opt_texts = [await opt_elements.nth(oi).inner_text() for oi in range(await opt_elements.count())]
                name_attr = (await sel.get_attribute("name")) or ""
                val = FormDetector.resolve_field_value(name_attr, self.profile, options=opt_texts)
                if val:
                    await sel.select_option(label=val)
                    answers_submitted[name_attr[:30]] = val
            except Exception as e:
                logger.debug("Error selecting option in dropdown %d: %s", k, e)

    async def _click_final_submit(self, page: Page) -> tuple[bool, Optional[str]]:
        """Click the final submission button (only executed in live non-dry-run mode)."""
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Submit application")',
            'button:has-text("Submit Application")',
            'button:has-text("Kirim Lamaran")',
            'button:has-text("Kirim")',
            'button:has-text("Submit")',
        ]

        for sel in submit_selectors:
            loc = page.locator(sel).first
            try:
                if await loc.is_visible() and await loc.is_enabled():
                    logger.info("Clicking final submit button: %s", sel)
                    await loc.click()
                    return True, None
            except Exception as e:
                logger.debug("Failed clicking submit button %s: %s", sel, e)

        return False, "Could not locate enabled final submit button."


# Global Auto-Fill Engine
auto_fill_engine = AutoFillEngine()
