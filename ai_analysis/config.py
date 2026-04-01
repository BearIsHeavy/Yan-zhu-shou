"""
Configuration for AI Analysis module.

Loads settings from environment variables with sensible defaults.
"""

import os
from typing import Optional


class AIAnalysisConfig:
    """AI Analysis configuration."""
    
    # LLM Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # Analysis Settings
    MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "4000"))
    TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    MAX_RETRIES: int = int(os.getenv("AI_MAX_RETRIES", "3"))
    
    # Feature Flags
    ENABLED: bool = os.getenv("AI_ANALYSIS_ENABLED", "true").lower() == "true"
    ASYNC_PROCESSING: bool = os.getenv("AI_ASYNC_PROCESSING", "true").lower() == "true"
    
    # Cache Settings
    CACHE_TTL: int = int(os.getenv("AI_CACHE_TTL", "3600"))  # 1 hour
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if AI analysis is available (has API key)."""
        return cls.ENABLED and bool(cls.OPENAI_API_KEY)
    
    @classmethod
    def get_model_info(cls) -> dict:
        """Get current model information."""
        return {
            "model": cls.OPENAI_MODEL,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
            "available": cls.is_available(),
        }
