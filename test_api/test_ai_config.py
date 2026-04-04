"""
Tests for ai_analysis.config module.

Tests:
1. Environment variable loading
2. Default values
3. is_available() logic
4. get_model_info() output
"""

import os
import unittest
from unittest.mock import patch

from ai_analysis.config import AIAnalysisConfig


class TestAIAnalysisConfig(unittest.TestCase):
    """Test AIAnalysisConfig class."""

    def test_default_values(self):
        """Test that default values are set correctly when env vars are missing."""
        # Reload module to pick up current env
        import importlib
        from ai_analysis import config
        importlib.reload(config)
        from ai_analysis.config import AIAnalysisConfig as ReloadedConfig

        # With current .env, these should be set
        self.assertEqual(ReloadedConfig.OPENAI_BASE_URL, "http://localhost:11434/v1")
        self.assertEqual(ReloadedConfig.OPENAI_MODEL, "qwen3.5:2b")
        self.assertEqual(ReloadedConfig.OPENAI_API_KEY, "ollama")

    def test_is_available(self):
        """Test is_available() returns True when properly configured."""
        self.assertTrue(AIAnalysisConfig.is_available())

    def test_is_available_disabled(self):
        """Test is_available() returns False when ENABLED is False."""
        with patch.object(AIAnalysisConfig, "ENABLED", False):
            self.assertFalse(AIAnalysisConfig.is_available())

    def test_is_available_no_key(self):
        """Test is_available() returns False when API key is empty."""
        with patch.object(AIAnalysisConfig, "OPENAI_API_KEY", ""):
            self.assertFalse(AIAnalysisConfig.is_available())

    def test_get_model_info(self):
        """Test get_model_info() returns correct structure."""
        info = AIAnalysisConfig.get_model_info()

        self.assertIsInstance(info, dict)
        self.assertEqual(info["model"], "qwen3.5:2b")
        self.assertEqual(info["max_tokens"], 4000)
        self.assertEqual(info["temperature"], 0.7)
        self.assertTrue(info["available"])

    def test_enabled_true(self):
        """Test ENABLED is True when env var is 'true'."""
        self.assertTrue(AIAnalysisConfig.ENABLED)

    def test_async_processing(self):
        """Test ASYNC_PROCESSING default."""
        self.assertTrue(AIAnalysisConfig.ASYNC_PROCESSING)

    def test_cache_ttl(self):
        """Test CACHE_TTL default."""
        self.assertEqual(AIAnalysisConfig.CACHE_TTL, 3600)

    def test_max_retries(self):
        """Test MAX_RETRIES default."""
        self.assertEqual(AIAnalysisConfig.MAX_RETRIES, 3)


if __name__ == "__main__":
    unittest.main()
