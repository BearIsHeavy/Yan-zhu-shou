"""
Test script for Mistake Notebook API endpoints.

Tests:
- GET /mistake-notebook/questions - List wrong questions
- GET /mistake-notebook/categories - Get categories
- GET /mistake-notebook/stats - Get statistics
- POST /practice/submit-answer - Submit answer
- POST /mistake-notebook/questions/{id}/master - Mark as mastered
- POST /mistake-notebook/questions/{id}/unmaster - Mark as not mastered

Usage:
    python test_api/test_mistake.py
"""

import asyncio
from test_base import BaseTest, run_test_module


class TestMistakeAPIs(BaseTest):
    """Test class for mistake notebook-related API endpoints."""
    
    def __init__(self):
        super().__init__("Mistake Notebook APIs")
    
    async def test_get_categories(self):
        """Test GET /mistake-notebook/categories endpoint."""
        try:
            response = await self.client.get(
                "/mistake-notebook/categories",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                self._log_result("GET /mistake-notebook/categories", True, f"Found {len(data)} categories")
            else:
                self._log_result("GET /mistake-notebook/categories", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /mistake-notebook/categories", False, str(e))
    
    async def test_get_stats(self):
        """Test GET /mistake-notebook/stats endpoint."""
        try:
            response = await self.client.get(
                "/mistake-notebook/stats",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "total_wrong" in data
                self._log_result("GET /mistake-notebook/stats", True, f"Total wrong: {data['total_wrong']}")
            else:
                self._log_result("GET /mistake-notebook/stats", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /mistake-notebook/stats", False, str(e))
    
    async def test_get_wrong_questions(self):
        """Test GET /mistake-notebook/questions endpoint."""
        try:
            response = await self.client.get(
                "/mistake-notebook/questions",
                params={"page": 1, "size": 10},
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "data" in data
                self._log_result("GET /mistake-notebook/questions", True, f"Found {len(data['data'])} questions")
            else:
                self._log_result("GET /mistake-notebook/questions", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /mistake-notebook/questions", False, str(e))
    
    async def test_submit_answer(self):
        """Test POST /practice/submit-answer endpoint."""
        try:
            # Try to submit an answer for question 1 (may not exist)
            response = await self.client.post(
                "/practice/submit-answer",
                json={
                    "question_no": 1,
                    "user_answer": "A",
                    "time_spent_seconds": 30
                },
                headers=self._get_headers()
            )
            
            if response.status_code in [200, 404]:
                # 404 is acceptable if question doesn't exist
                self._log_result("POST /practice/submit-answer", True, f"Status: {response.status_code}")
            else:
                self._log_result("POST /practice/submit-answer", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("POST /practice/submit-answer", False, str(e))
    
    async def test_start_practice_session(self):
        """Test POST /practice/start-session endpoint."""
        try:
            response = await self.client.post(
                "/practice/start-session",
                json={
                    "bank_id": 1,
                    "question_count": 5
                },
                headers=self._get_headers()
            )
            
            # 404 is acceptable if no question bank exists
            if response.status_code in [200, 404]:
                self._log_result("POST /practice/start-session", True, f"Status: {response.status_code}")
            else:
                self._log_result("POST /practice/start-session", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("POST /practice/start-session", False, str(e))


async def main():
    """Run all mistake notebook API tests."""
    success = await run_test_module(TestMistakeAPIs, "Mistake Notebook APIs")
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
