"""
Gemini AI Assistant for Job-Hunting Agent.
Provides intelligent conversational interface, contextual analysis, and dynamic cover letter generation
grounded in Aditya Darmawan's 15+ years credit risk career history and current database status.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx

from config import config
from src.core.database import db
from src.core.logger import get_logger
from src.core.models import ApplicationStatus, Job
from src.matcher.profile_loader import load_candidate_profile

logger = get_logger("gemini_assistant")

SYSTEM_PROMPT = """
Kamu adalah "Antigravity Job Copilot", asisten AI karir & rekrutmen pribadi untuk Aditya Darmawan (@Xpressoooo).
Tugasmu adalah membantu Aditya dalam proses pencarian kerja, evaluasi lowongan, persiapan pengajuan lamaran, pembuatan cover letter kontekstual, dan mengontrol bot otomatisasi lowongan kerja via Telegram.

Profil Utama Aditya Darmawan:
- Pengalaman: 15+ tahun di bidang Senior Credit Risk, SME & Commercial Lending Underwriting.
- Riwayat Institusi: Aspire SEA (FinTech Lending, 6 tahun - kalibrasi scorecard digital, SME loan & corporate cards), Maybank (Best Sales Person RO SME UpCountry 2014), CIMB Niaga (Account Officer - analisis DSCR, spreading laporan keuangan), Bank Mega.
- Target Gaji: IDR 25.000.000 - 35.000.000 / bulan (negotiable).
- Lokasi: Jakarta / Tarakan (Hybrid/On-site) atau Remote.

Gaya Komunikasi:
- Ramah, profesional, lugas, santai, dan cerdas (panggil "Bos" atau "Pak Aditya").
- Bahasa Indonesia yang luwes dan natural.
- Selalu factual (Zero-Slop), jangan mengarang pengalaman yang tidak ada di profil resmi.
- Jika pengguna meminta ringkasan lowongan atau status lamaran, gunakan DATA SISTEM yang dilampirkan.
"""


class GeminiAssistant:
    def __init__(self) -> None:
        self.api_key = config.google_api_key
        self.models_to_try = [
            config.gemini_model,
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-flash-latest",
        ]
        self.history: List[Dict[str, Any]] = []

    async def _gather_system_context(self, user_text: str) -> Dict[str, Any]:
        """Fetch real-time database metrics, pending jobs, and candidate profile info."""
        profile = load_candidate_profile()
        stats = await db.get_statistics()
        pending_jobs = await db.get_pending_approvals(limit=5)

        context: Dict[str, Any] = {
            "candidate": {
                "name": profile.full_name,
                "title": profile.title,
                "years_experience": profile.total_years_experience,
                "locations": profile.locations,
                "expected_salary": f"IDR {profile.salary_expectation.expected_min:,} - {profile.salary_expectation.expected_target:,}",
            },
            "pipeline_statistics": stats,
            "shortlisted_pending_jobs": [
                {
                    "id": j.id,
                    "title": j.title,
                    "company": j.company,
                    "location": j.location,
                    "salary": j.get_display_salary(),
                    "score": j.match_result.score if j.match_result else 0,
                    "url": j.url,
                }
                for j in pending_jobs
            ],
        }

        # Check if user mentioned a specific job ID
        match = re.search(r"\b(job_[a-f0-9]+|gli_[a-f0-9]+|kal_[a-f0-9]+)\b", user_text.lower())
        if match:
            job_id = match.group(1)
            job = await db.get_job_by_id(job_id)
            if job:
                context["referenced_job"] = {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "salary": job.get_display_salary(),
                    "description": job.description[:1000],
                    "status": job.status.value,
                    "match_score": job.match_result.score if job.match_result else None,
                    "rationale": job.match_result.reasoning if job.match_result else None,
                }

        return context

    async def chat(self, user_text: str) -> str:
        """Process natural language message from Telegram user with Gemini context injection."""
        context_data = await self._gather_system_context(user_text)

        prompt_with_context = f"""[DATA SISTEM REAL-TIME]:
{json.dumps(context_data, indent=2, ensure_ascii=False)}

[PESAN DARI PENGGUNA (@{config.allowed_user})]:
"{user_text}"

Tanggapi pesan dengan bahasa yang komunikatif, profesional, dan relevan sesuai data sistem di atas."""

        # Maintain short conversational history
        self.history.append({"role": "user", "parts": [{"text": prompt_with_context}]})
        if len(self.history) > 6:
            self.history = self.history[-6:]

        payload = {
            "contents": self.history,
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "generationConfig": {
                "temperature": 0.6,
                "maxOutputTokens": 800,
            },
        }

        if not self.api_key:
            logger.warning("Google API Key not set, using fallback generator.")
            return self._generate_fallback_response(user_text, context_data)

        for model in self.models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        reply = "".join([p.get("text", "") for p in parts if "text" in p]).strip()
                        if reply:
                            self.history.append({"role": "model", "parts": [{"text": reply}]})
                            return reply
                    else:
                        logger.warning("Gemini model %s returned status %d: %s", model, res.status_code, res.text[:100])
            except Exception as e:
                logger.warning("Gemini model %s error: %s, trying fallback...", model, e)

        return self._generate_fallback_response(user_text, context_data)

    def _generate_fallback_response(self, user_text: str, context: Dict[str, Any]) -> str:
        """Deterministic template response when offline."""
        t = user_text.lower()
        stats = context.get("pipeline_statistics", {})
        pending = context.get("shortlisted_pending_jobs", [])

        if any(w in t for w in ["halo", "hi", "start", "menu", "help"]):
            return (
                f"👋 **Halo Bos @{config.allowed_user}! Antigravity Job Copilot Siap!**\n\n"
                f"📊 **Ringkasan Pipeline Lamaran:**\n"
                f"• Total Lowongan Terpindai: {stats.get('total', 0)}\n"
                f"• Menunggu Approval (Shortlisted): {len(pending)}\n"
                f"• Rata-rata Match Score: {stats.get('avg_match_score', 0):.1f}%\n\n"
                f"Anda bisa tanya seputar lowongan, minta evaluasi CV, atau klik tombol interaktif di kartu lowongan!"
            )
        elif any(w in t for w in ["status", "lowongan", "list", "antrean", "pending"]):
            if not pending:
                return "✅ Belum ada lowongan baru yang menunggu approval saat ini, Bos. Semua lowongan sudah diproses atau difilter."
            msg = "📋 **Lowongan Menunggu Approval Anda:**\n\n"
            for j in pending[:3]:
                msg += f"• **{j['title']}** @ {j['company']}\n  Skor: {j['score']}% | Gaji: {j['salary']}\n  ID: `{j['id']}`\n\n"
            return msg
        else:
            return (
                f"Siap, Bos! Pesan Anda: *\"{user_text}\"*\n\n"
                f"Saat ini ada **{len(pending)}** lowongan dengan skor kecocokan tinggi (>=75%) di antrean. "
                f"Silakan tinjau kartu notifikasi Telegram untuk melakukan Approve & Auto-Apply atau Skip."
            )


gemini_assistant = GeminiAssistant()
