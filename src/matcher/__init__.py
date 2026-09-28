"""
Matcher package exports.
"""

from src.matcher.blacklist import BlacklistFilter, ExclusionResult, default_blacklist
from src.matcher.matcher import JobMatcher, default_matcher

# Backward compatibility aliases
MatcherEngine = JobMatcher

__all__ = [
    "BlacklistFilter",
    "ExclusionResult",
    "default_blacklist",
    "JobMatcher",
    "default_matcher",
    "MatcherEngine",
]
