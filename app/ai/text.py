import unicodedata


def normalize_message(text: str) -> str:
    """Normalize text for guardrails while preserving punctuation and words."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(normalized.split())
