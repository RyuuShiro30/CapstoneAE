import os
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuration shared by the API and the chatbot service."""

    cors_origins: tuple[str, ...] = ("*",)
    cors_allow_credentials: bool = True
    intent_min_confidence: float = 0.60
    external_timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        if not 0 <= self.intent_min_confidence <= 1:
            raise ValueError("CHAT_INTENT_MIN_CONFIDENCE must be between 0 and 1.")
        if (
            not isfinite(self.external_timeout_seconds)
            or self.external_timeout_seconds <= 0
        ):
            raise ValueError(
                "CHAT_EXTERNAL_TIMEOUT_SECONDS must be positive and finite."
            )

    @classmethod
    def from_env(cls) -> "Settings":
        """Load server settings from the process environment."""
        origins = os.getenv("CHAT_CORS_ORIGINS", "*").split(",")
        credentials = os.getenv("CHAT_CORS_ALLOW_CREDENTIALS", "true").strip().lower()
        if credentials not in {"true", "false"}:
            raise ValueError("CHAT_CORS_ALLOW_CREDENTIALS must be true or false.")
        return cls(
            cors_origins=tuple(filter(None, map(str.strip, origins))),
            cors_allow_credentials=credentials == "true",
            intent_min_confidence=float(
                os.getenv("CHAT_INTENT_MIN_CONFIDENCE", "0.60")
            ),
            external_timeout_seconds=float(
                os.getenv("CHAT_EXTERNAL_TIMEOUT_SECONDS", "2.0")
            ),
        )
