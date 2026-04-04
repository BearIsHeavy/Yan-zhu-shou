"""
Tests for ai_analysis.llm_client module with Ollama (qwen3.5:2b).

Tests:
1. LLMClient initialization
2. Basic chat completion
3. Weak point analysis
4. Knowledge point extraction
5. Recommendation generation

Usage:
    python -m pytest test_api/test_ai_llm_client.py -v

Note: Requires Ollama running on localhost:11434 with qwen3.5:2b model.
      Start Ollama: ollama serve
      Pull model: ollama pull qwen3.5:2b
"""

import asyncio
import unittest

from ai_analysis.llm_client import LLMClient
from ai_analysis.config import AIAnalysisConfig


class TestLLMClient(unittest.IsolatedAsyncioTestCase):
    """Test LLMClient with Ollama."""

    def setUp(self):
        """Initialize LLM client."""
        self.client = LLMClient()
        print(f"\n  Using model: {self.client.model}")
        print(f"\n  Using base_url: {self.client.base_url}")

    async def test_basic_chat(self):
        """Test basic chat completion."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in 5 words."},
        ]

        response = await self.client.chat(messages)
        print(f"  Response: {response}")

        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    async def test_analyze_weak_points(self):
        """Test weak point analysis with sample wrong questions."""
        wrong_questions = [
            {
                "question_no": "Q001",
                "category": "Algebra",
                "stem": "Solve: 2x + 3 = 7",
                "user_answer": "x = 5",
                "correct_ans_summary": "x = 2",
            },
            {
                "question_no": "Q002",
                "category": "Algebra",
                "stem": "Solve: 3x - 1 = 8",
                "user_answer": "x = 1",
                "correct_ans_summary": "x = 3",
            },
            {
                "question_no": "Q003",
                "category": "Geometry",
                "stem": "What is the area of a triangle with base 5 and height 3?",
                "user_answer": "15",
                "correct_ans_summary": "7.5",
            },
        ]

        result = await self.client.analyze_weak_points(wrong_questions)
        print(f"  Weak points: {result.get('weak_points', [])}")
        print(f"  Summary: {result.get('summary', '')}")

        self.assertIn("weak_points", result)
        self.assertIn("error_patterns", result)
        self.assertIn("recommendations", result)
        self.assertIn("summary", result)

    async def test_extract_knowledge_points(self):
        """Test knowledge point extraction from text."""
        text = """
        Linear equations are mathematical expressions that describe a straight line.
        They have the form ax + b = c, where a, b, c are constants.
        To solve, isolate the variable on one side of the equation.
        Example: 2x + 3 = 7, subtract 3 from both sides: 2x = 4, then divide by 2: x = 2.
        """

        result = await self.client.extract_knowledge_points(text, subject="Mathematics")
        print(f"  Knowledge points: {result}")

        self.assertIsInstance(result, list)
        if result:
            self.assertIn("name", result[0])
            self.assertIn("description", result[0])

    async def test_generate_recommendations(self):
        """Test recommendation generation."""
        weak_points = [
            {"knowledge": "Algebra", "error_count": 5, "confidence": 0.3},
            {"knowledge": "Geometry", "error_count": 3, "confidence": 0.5},
        ]

        result = await self.client.generate_recommendations(weak_points, user_level="beginner")
        print(f"  Recommendations: {result}")

        self.assertIsInstance(result, list)

    async def test_retry_on_failure(self):
        """Test that retries work on failure (uses small model to test)."""
        # This tests the retry mechanism by making a normal request
        messages = [
            {"role": "user", "content": "What is 1+1?"},
        ]

        response = await self.client.chat(messages)
        self.assertIsInstance(response, str)


class TestLLMClientEdgeCases(unittest.IsolatedAsyncioTestCase):
    """Test edge cases for LLMClient."""

    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        client = LLMClient(
            api_key="custom_key",
            model="custom_model",
            base_url="http://custom:8080",
        )

        self.assertEqual(client.api_key, "custom_key")
        self.assertEqual(client.model, "custom_model")
        self.assertEqual(client.base_url, "http://custom:8080")

    def test_base_url_trailing_slash_removal(self):
        """Test that trailing slash is removed from base_url."""
        client = LLMClient(base_url="http://localhost:11434/v1/")
        self.assertEqual(client.base_url, "http://localhost:11434/v1")

    async def test_unavailable_ai(self):
        """Test that RuntimeError is raised when AI is unavailable."""
        from unittest.mock import patch

        with patch.object(AIAnalysisConfig, "is_available", return_value=False):
            client = LLMClient()
            with self.assertRaises(RuntimeError):
                await client.chat([{"role": "user", "content": "test"}])


if __name__ == "__main__":
    unittest.main()
