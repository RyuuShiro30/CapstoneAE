import unicodedata


def normalize_message(text: str) -> str:
    """Normalize Unicode, case, and spaces while retaining Indonesian words."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(normalized.split())
