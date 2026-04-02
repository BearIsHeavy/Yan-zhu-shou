"""
Test script for Question Bank API endpoints.

Tests:
- GET /question_banks - List question banks
- POST /question_banks/book - Create question bank
- GET /question_banks/{id} - Get question bank details
- GET /question_banks/{id}/questions - Get questions
- DELETE /question_banks/{id} - Delete question bank

Usage:
    python test_api/test_question.py
"""

import asyncio
from test_base import BaseTest, run_test_module


class TestQuestionAPIs(BaseTest):
    """Test class for question bank-related API endpoints."""
    
    def __init__(self):
        super().__init__("Question Bank APIs")
        self.created_bank_id = None
    
    async def test_get_question_banks(self):
        """Test GET /question_banks endpoint."""
        try:
            response = await self.client.get(
                "/question_banks",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                self._log_result("GET /question_banks", True, f"Found {len(data)} question banks")
            else:
                self._log_result("GET /question_banks", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /question_banks", False, str(e))
    
    async def test_create_question_bank(self):
        """Test POST /question_banks/book endpoint."""
        try:
            response = await self.client.post(
                "/question_banks/book",
                json={
                    "name": f"Test Question Bank",
                    "is_public": False,
                    "description": "Test question bank created by API test"
                },
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.created_bank_id = data["bank_id"]
                self._log_result("POST /question_banks/book", True, f"Created bank ID: {self.created_bank_id}")
            elif response.status_code == 400:
                # Already exists
                self._log_result("POST /question_banks/book", True, "Bank already exists")
            else:
                self._log_result("POST /question_banks/book", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("POST /question_banks/book", False, str(e))
    
    async def test_get_question_bank(self):
        """Test GET /question_banks/{id} endpoint."""
        # Use existing bank first
        bank_id = self.get_first_question_bank_id() or self.created_bank_id
        
        if not bank_id:
            self._log_result("GET /question_banks/{id}", False, "No bank available")
            return
        
        try:
            response = await self.client.get(
                f"/question_banks/{bank_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["bank_id"] == bank_id
                self._log_result(f"GET /question_banks/{bank_id}", True, "Bank retrieved")
            else:
                self._log_result(f"GET /question_banks/{bank_id}", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"GET /question_banks/{bank_id}", False, str(e))
    
    async def test_get_bank_questions(self):
        """Test GET /question_banks/{id}/questions endpoint."""
        # Use existing bank first
        bank_id = self.get_first_question_bank_id() or self.created_bank_id
        
        if not bank_id:
            self._log_result("GET /question_banks/{id}/questions", False, "No bank available")
            return
        
        try:
            response = await self.client.get(
                f"/question_banks/{bank_id}/questions",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                self._log_result(f"GET /question_banks/{bank_id}/questions", True, f"Found {len(data)} questions")
            else:
                self._log_result(f"GET /question_banks/{bank_id}/questions", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"GET /question_banks/{bank_id}/questions", False, str(e))
    
    async def test_delete_question_bank(self):
        """Test DELETE /question_banks/{id} endpoint (cleanup)."""
        # Only delete banks we created in this test session
        if not self.created_bank_id:
            self._log_result("DELETE /question_banks/{id}", True, "Skipped (no test bank created)")
            return
        
        try:
            response = await self.client.delete(
                f"/question_banks/{self.created_bank_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                self._log_result(f"DELETE /question_banks/{self.created_bank_id}", True, "Bank deleted")
            else:
                self._log_result(f"DELETE /question_banks/{self.created_bank_id}", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"DELETE /question_banks/{self.created_bank_id}", False, str(e))


async def main():
    """Run all question bank API tests."""
    success = await run_test_module(TestQuestionAPIs, "Question Bank APIs")
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
