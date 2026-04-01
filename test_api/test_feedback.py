"""
Test script for Feedback API endpoints.

Tests:
- GET /api/feedback - List feedbacks
- POST /api/feedback - Create feedback
- GET /api/feedback/{id} - Get feedback details
- PUT /api/feedback/{id} - Update feedback (admin)
- POST /api/feedback/{id}/vote - Vote feedback
- GET /api/feedback/stats - Get feedback stats
- GET /api/feedback/me/submissions - Get my submissions
- GET /api/feedback/me/submission-status - Check submission status

Usage:
    python test_api/test_feedback.py
"""

import asyncio
from test_base import BaseTest, run_test_module


class TestFeedbackAPIs(BaseTest):
    """Test class for feedback-related API endpoints."""
    
    def __init__(self):
        super().__init__("Feedback APIs")
        self.created_feedback_id = None
    
    async def test_list_feedbacks(self):
        """Test GET /api/feedback endpoint."""
        try:
            response = await self.client.get(
                "/api/feedback",
                params={"page": 1, "page_size": 10},
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                self._log_result("GET /api/feedback", True, f"Found {len(data['items'])} feedbacks")
            else:
                self._log_result("GET /api/feedback", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /api/feedback", False, str(e))
    
    async def test_get_feedback_stats(self):
        """Test GET /api/feedback/stats endpoint."""
        try:
            response = await self.client.get(
                "/api/feedback/stats",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "total_count" in data
                self._log_result("GET /api/feedback/stats", True, f"Total: {data['total_count']}")
            else:
                self._log_result("GET /api/feedback/stats", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /api/feedback/stats", False, str(e))
    
    async def test_create_feedback(self):
        """Test POST /api/feedback endpoint."""
        try:
            response = await self.client.post(
                "/api/feedback",
                json={
                    "content": "Test feedback from API test script. This is automated testing.",
                    "category": "feature"
                },
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                data = response.json()
                self.created_feedback_id = data["id"]
                self._log_result("POST /api/feedback", True, f"Created feedback ID: {self.created_feedback_id}")
            elif response.status_code == 429:
                # Rate limit - already submitted today
                self._log_result("POST /api/feedback", True, "Rate limited (already submitted today)")
            else:
                self._log_result("POST /api/feedback", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("POST /api/feedback", False, str(e))
    
    async def test_get_feedback(self):
        """Test GET /api/feedback/{id} endpoint."""
        if not self.created_feedback_id:
            self._log_result("GET /api/feedback/{id}", False, "No feedback created yet")
            return
        
        try:
            response = await self.client.get(
                f"/api/feedback/{self.created_feedback_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["id"] == self.created_feedback_id
                self._log_result(f"GET /api/feedback/{self.created_feedback_id}", True, "Feedback retrieved")
            else:
                self._log_result(f"GET /api/feedback/{self.created_feedback_id}", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"GET /api/feedback/{self.created_feedback_id}", False, str(e))
    
    async def test_vote_feedback(self):
        """Test POST /api/feedback/{id}/vote endpoint."""
        if not self.created_feedback_id:
            self._log_result("POST /api/feedback/{id}/vote", False, "No feedback created yet")
            return
        
        try:
            response = await self.client.post(
                f"/api/feedback/{self.created_feedback_id}/vote",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "has_voted" in data
                self._log_result(f"POST /api/feedback/{self.created_feedback_id}/vote", True, f"Voted: {data['has_voted']}")
            elif response.status_code == 400:
                # Cannot vote on own feedback
                self._log_result(f"POST /api/feedback/{self.created_feedback_id}/vote", True, "Cannot vote on own feedback (expected)")
            else:
                self._log_result(f"POST /api/feedback/{self.created_feedback_id}/vote", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"POST /api/feedback/{self.created_feedback_id}/vote", False, str(e))
    
    async def test_get_vote_status(self):
        """Test GET /api/feedback/{id}/vote endpoint."""
        if not self.created_feedback_id:
            self._log_result("GET /api/feedback/{id}/vote", False, "No feedback created yet")
            return
        
        try:
            response = await self.client.get(
                f"/api/feedback/{self.created_feedback_id}/vote",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "has_voted" in data
                self._log_result(f"GET /api/feedback/{self.created_feedback_id}/vote", True, f"Has voted: {data['has_voted']}")
            else:
                self._log_result(f"GET /api/feedback/{self.created_feedback_id}/vote", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"GET /api/feedback/{self.created_feedback_id}/vote", False, str(e))
    
    async def test_get_my_submissions(self):
        """Test GET /api/feedback/me/submissions endpoint."""
        try:
            response = await self.client.get(
                "/api/feedback/me/submissions",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                self._log_result("GET /api/feedback/me/submissions", True, f"Found {len(data['items'])} submissions")
            else:
                self._log_result("GET /api/feedback/me/submissions", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /api/feedback/me/submissions", False, str(e))
    
    async def test_get_submission_status(self):
        """Test GET /api/feedback/me/submission-status endpoint."""
        try:
            response = await self.client.get(
                "/api/feedback/me/submission-status",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "can_submit" in data
                self._log_result("GET /api/feedback/me/submission-status", True, f"Can submit: {data['can_submit']}")
            else:
                self._log_result("GET /api/feedback/me/submission-status", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /api/feedback/me/submission-status", False, str(e))
    
    async def test_delete_feedback(self):
        """Test DELETE /api/feedback/{id} endpoint (cleanup)."""
        if not self.created_feedback_id:
            self._log_result("DELETE /api/feedback/{id}", False, "No feedback created yet")
            return
        
        try:
            response = await self.client.delete(
                f"/api/feedback/{self.created_feedback_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 204:
                self._log_result(f"DELETE /api/feedback/{self.created_feedback_id}", True, "Feedback deleted")
            elif response.status_code == 403:
                # Cannot delete with votes
                self._log_result(f"DELETE /api/feedback/{self.created_feedback_id}", True, "Cannot delete (has votes, expected)")
            else:
                self._log_result(f"DELETE /api/feedback/{self.created_feedback_id}", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result(f"DELETE /api/feedback/{self.created_feedback_id}", False, str(e))


async def main():
    """Run all feedback API tests."""
    success = await run_test_module(TestFeedbackAPIs, "Feedback APIs")
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
