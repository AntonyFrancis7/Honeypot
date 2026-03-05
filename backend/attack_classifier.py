import re
from typing import List, Set


SQLI_PATTERNS: List[re.Pattern] = [
    re.compile(r"'\s*or\s*1=1", re.IGNORECASE),
    re.compile(r"union\s+select", re.IGNORECASE),
    re.compile(r"information_schema", re.IGNORECASE),
]

XSS_PATTERNS: List[re.Pattern] = [
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"onerror\s*=", re.IGNORECASE),
    re.compile(r"onload\s*=", re.IGNORECASE),
]

LFI_PATTERNS: List[re.Pattern] = [
    re.compile(r"\.\.\/\.\.\/\.\.\/", re.IGNORECASE),
    re.compile(r"/etc/passwd", re.IGNORECASE),
]

SCANNER_KEYWORDS: List[str] = ["nmap", "sqlmap", "nikto", "wpscan", "dirbuster"]


def classify_attack(payload: str, user_agent: str | None = None) -> Set[str]:
    """
    Classify attack types based on payload and optional user agent.
    Returns a set of labels like {'SQLi', 'XSS'}.
    """
    labels: Set[str] = set()
    data = payload or ""

    # SQL Injection
    if any(p.search(data) for p in SQLI_PATTERNS):
        labels.add("SQLi")

    # XSS
    if any(p.search(data) for p in XSS_PATTERNS):
        labels.add("XSS")

    # LFI / Path Traversal
    if any(p.search(data) for p in LFI_PATTERNS):
        labels.add("LFI")

    # Automated Scanners
    if user_agent:
        ua_lower = user_agent.lower()
        if any(keyword in ua_lower for keyword in SCANNER_KEYWORDS):
            labels.add("Scanner")

    return labels

