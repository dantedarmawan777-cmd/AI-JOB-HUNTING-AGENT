"""
Candidate profile loader and intelligence helper.
Loads candidate profile from JSON and provides lookup utilities for auto-fill and matching.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from config import config
from src.core.logger import get_logger
from src.core.models import CandidateProfile

logger = get_logger(__name__)

_PROFILE_CACHE: Optional[CandidateProfile] = None


def load_candidate_profile(profile_path: Optional[Path | str] = None) -> CandidateProfile:
    """
    Load candidate profile from JSON configuration file.
    Cached after first load.
    """
    global _PROFILE_CACHE
    if _PROFILE_CACHE is not None and not profile_path:
        return _PROFILE_CACHE

    target_path = Path(profile_path) if profile_path else config.candidate_profile_path
    if not target_path.exists():
        raise FileNotFoundError(f"Candidate profile file not found at: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    profile = CandidateProfile(**data)
    if not profile_path:
        _PROFILE_CACHE = profile
    logger.info("Loaded candidate profile for: %s (%s)", profile.full_name, profile.title)
    return profile


def get_cv_path_for_language(language: str = "EN", profile: Optional[CandidateProfile] = None) -> Optional[Path]:
    """
    Retrieve the absolute Path to the CV PDF file corresponding to the specified language ('EN' or 'ID').
    Automatically falls back to local data/resumes directory if absolute path is not found.
    """
    if profile is None:
        profile = load_candidate_profile()

    lang_upper = language.upper()
    cv_str = profile.cv_files.get(lang_upper) or profile.cv_files.get("EN")
    if cv_str:
        p = Path(cv_str)
        if p.exists():
            return p

    # Fallback to repository data/resumes directory
    local_fallback = config.db_path.parent / "resumes" / f"Aditya_Darmawan_CV_Career_{lang_upper}.pdf"
    if local_fallback.exists():
        return local_fallback

    logger.warning("CV file path specified in profile does not exist: %s", cv_str)
    return Path(cv_str) if cv_str else None
