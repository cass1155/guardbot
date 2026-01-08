import re

def check_regex(text: str, pattern: str) -> bool:
    try:
        return bool(re.search(pattern, text, re.IGNORECASE))
    except re.error:
        return False

def check_link(text: str) -> bool:
    # Simple link regex
    url_pattern = r"(https?://[^\s]+)|(www\.[^\s]+)"
    return bool(re.search(url_pattern, text))

def check_caps(text: str, threshold: float = 0.7) -> bool:
    if len(text) < 5:
        return False
    caps_count = sum(1 for c in text if c.isupper())
    return (caps_count / len(text)) > threshold

def check_keywords(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False

def check_crypto(text: str) -> bool:
    # Common crypto address patterns
    patterns = [
        r"\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b", # BTC
        r"\b0x[a-fA-F0-9]{40}\b", # ETH/BSC/Polygon
        r"\bT[A-Za-z1-9]{33}\b" # TRX
    ]
    for p in patterns:
        if re.search(p, text):
            return True
    return False

def check_phone(text: str) -> bool:
    # Simple phone regex (international format)
    pattern = r"\+?[\d\s\-\(\)]{7,}"
    # Refine to avoid false positives (requires at least 7 digits)
    digits = re.sub(r"\D", "", text)
    return len(digits) >= 7 and bool(re.search(pattern, text))

def check_media(message) -> bool:
    # Check if message has media content (photo, video, document, etc.)
    return bool(message.photo or message.video or message.document or message.voice or message.audio)

