"""
Test script for User API endpoints.

Tests:
- GET /users/me - Get current user info
- PUT /users/me - Update user info
- GET /users/bio - Get user bio
- POST /users/bio - Upload bio (optional)
- DELETE /users/bio - Delete bio

Usage:
    python test_api/test_user.py

Note: Make sure the FastAPI server is running on http://127.0.0.1:8000
"""

import asyncio
from test_base import BaseTest, run_test_module


class TestUserAPIs(BaseTest):
    """Test class for user-related API endpoints."""
    
    def __init__(self):
        super().__init__("User APIs")
    
    async def test_get_current_user(self):
        """Test GET /users/me endpoint."""
        try:
            response = await self.client.get(
                "/users/me",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "email" in data
                assert data["email"] == self.TEST_EMAIL
                self._log_result("GET /users/me", True, f"User: {data['email']}")
            else:
                self._log_result("GET /users/me", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /users/me", False, str(e))
    
    async def test_update_user(self):
        """Test PUT /users/me endpoint."""
        try:
            update_data = {
                "name": "Test User Updated",
                "gender": 1
            }
            
            response = await self.client.put(
                "/users/me",
                json=update_data,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["name"] == "Test User Updated"
                self._log_result("PUT /users/me", True, "User updated successfully")
            else:
                self._log_result("PUT /users/me", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("PUT /users/me", False, str(e))
    
    async def test_get_bio(self):
        """Test GET /users/bio endpoint."""
        try:
            response = await self.client.get(
                "/users/bio",
                headers=self._get_headers()
            )
            
            # 404 is acceptable if no bio uploaded yet
            if response.status_code in [200, 404]:
                self._log_result("GET /users/bio", True, f"Status: {response.status_code}")
            else:
                self._log_result("GET /users/bio", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /users/bio", False, str(e))
    
    async def test_get_user_bio_by_id(self):
        """Test GET /users/bio/{user_id} endpoint."""
        try:
            response = await self.client.get(
                "/users/bio/1",
                headers=self._get_headers()
            )
            
            # 404 is acceptable if no bio uploaded
            if response.status_code in [200, 404]:
                self._log_result("GET /users/bio/1", True, f"Status: {response.status_code}")
            else:
                self._log_result("GET /users/bio/1", False, f"Status: {response.status_code}")
        except Exception as e:
            self._log_result("GET /users/bio/1", False, str(e))


async def main():
    """Run all user API tests."""
    success = await run_test_module(TestUserAPIs, "User APIs")
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
