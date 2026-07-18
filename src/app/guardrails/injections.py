import re

INJECTION_PATTERNS = [
    r"ignore (all |the |any )?(previous|prior|above|earlier) instructions",
    r"disregard (all |the |any )?(previous|prior|above|earlier)",
    r"forget (everything|all|what) (you|i told you|your instructions)",
    r"you are now",
    r"act as (if you were|though you)",
    r"new instructions?\s*:",
    r"system prompt",
    r"reveal (your|the) (instructions|prompt|rules|system message)",
    r"override (your|the) (rules|instructions|guidelines)",
    r"pretend (you are|to be)",
    r"jailbreak",
    r"dan mode",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_injection(query: str) -> dict:
    matched = [p.pattern for p in _compiled if p.search(query)]
    return {
        "flagged": len(matched) > 0,
        "matched_patterns": matched,
    }

