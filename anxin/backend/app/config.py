"""Centralized, typed application settings.

All secrets are loaded server-side only (from environment variables / a local
.env file that is git-ignored). Nothing in this module is ever sent to the
frontend bundle -- see app/routers/verify.py, which never echoes GONKA_API_KEY
or raw upstream payloads back to the client.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Gonka Router ---
    gonka_api_key: str = Field(default="", alias="GONKA_API_KEY")
    gonka_base_url: str = Field(default="https://api.gonkarouter.io", alias="GONKA_BASE_URL")
    gonka_chat_path: str = Field(default="/v1/chat/completions", alias="GONKA_CHAT_PATH")
    gonka_receipt_path: str = Field(default="/v1/receipts/{request_id}", alias="GONKA_RECEIPT_PATH")

    gonka_model_a: str = Field(default="deepseek-ai/DeepSeek-V4-Flash-0731", alias="GONKA_MODEL_A")
    gonka_model_a_label: str = Field(default="DeepSeek", alias="GONKA_MODEL_A_LABEL")
    gonka_model_b: str = Field(default="MiniMaxAI/MiniMax-M2.7", alias="GONKA_MODEL_B")
    gonka_model_b_label: str = Field(default="MiniMax", alias="GONKA_MODEL_B_LABEL")

    gonka_mock_mode: bool = Field(default=True, alias="GONKA_MOCK_MODE")
    # Decentralized inference is slower than a single hosted endpoint, and both
    # pinned models are reasoning-capable. These defaults bound the worst case
    # at roughly 90s per stage (2 attempts x 45s) while leaving normal calls
    # plenty of headroom. frontend/lib/api.ts must stay above this.
    gonka_timeout_seconds: float = Field(default=45.0, alias="GONKA_TIMEOUT_SECONDS")
    gonka_max_retries: int = Field(default=1, alias="GONKA_MAX_RETRIES")
    # Reasoning tokens count against this. Too low and the JSON answer gets
    # truncated mid-object (finish_reason="length") and fails validation.
    gonka_max_tokens: int = Field(default=2000, alias="GONKA_MAX_TOKENS")

    # Both spellings of the dev origin. A browser treats http://localhost:3000
    # and http://127.0.0.1:3000 as DIFFERENT origins, so allowing only one makes
    # the app fail with an opaque network error depending purely on which URL
    # the user happened to type. Costs nothing to allow both in development.
    cors_allow_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ALLOW_ORIGINS"
    )

    max_input_chars: int = Field(default=4000, alias="MAX_INPUT_CHARS")
    max_image_bytes: int = Field(default=8_000_000, alias="MAX_IMAGE_BYTES")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def gonka_configured(self) -> bool:
        return bool(self.gonka_api_key) and not self.gonka_mock_mode


@lru_cache
def get_settings() -> Settings:
    return Settings()
