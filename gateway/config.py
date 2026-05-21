"""
Gateway Configuration.

Settings can be overridden via environment variables.
"""

import os
from typing import Optional


class Settings:
    """Gateway configuration loaded from environment variables."""

    def __init__(self):
        # API Keys (comma-separated list of valid keys)
        # In production, this would be a database or secret manager
        self.api_keys = os.getenv(
            "API_KEYS",
            "sk-test-key-1,sk-test-key-2"
        ).split(",")

        # Rate limiting (requests per minute per API key)
        self.rate_limit_rpm = int(os.getenv("RATE_LIMIT_RPM", "60"))

        # Model to backend URL mapping
        # Format: model_name -> backend_url
        self.model_backends = {
            "mock": os.getenv("BACKEND_MOCK_URL", "http://mock-backend:8000"),
            "mock-v1": os.getenv("BACKEND_MOCK_URL", "http://mock-backend:8000"),
            # Future backends:
            # "llama-7b": os.getenv("BACKEND_VLLM_URL", "http://vllm-backend:8000"),
            # "mistral": os.getenv("BACKEND_MISTRAL_URL", "http://mistral-backend:8000"),
        }


settings = Settings()


def get_backend_url(model: str) -> Optional[str]:
    """Get the backend URL for a given model name."""
    return settings.model_backends.get(model)
