"""
Base test utilities for API testing.

Provides common functionality for all test modules:
- HTTP client setup
- Authentication handling
- Test result reporting
"""

import httpx
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime


class BaseTest:
    """Base class for all API tests."""
    
    BASE_URL = "http://127.0.0.1:8000"
    TEST_EMAIL = "test@example.com"
    TEST_PASSWORD = "123456"
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.access_token: Optional[str] = None
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0
        )
        self.results: list = []
    
    async def login(self) -> bool:
        """
        Login with test credentials and store access token.
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            response = await self.client.post(
                "/users/login",
                data={
                    "username": self.TEST_EMAIL,
                    "password": self.TEST_PASSWORD,
                    "grant_type": "password"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self._log_result("login", True, "Login successful")
                return True
            else:
                self._log_result("login", False, f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self._log_result("login", False, f"Login error: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    def _log_result(self, endpoint: str, success: bool, message: str):
        """Log test result."""
        self.results.append({
            "endpoint": endpoint,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def print_results(self):
        """Print test results summary."""
        print(f"\n{'='*60}")
        print(f"Test Module: {self.module_name}")
        print(f"{'='*60}")
        
        passed = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - passed
        
        for result in self.results:
            status = "✓ PASS" if result["success"] else "✗ FAIL"
            print(f"  {status} - {result['endpoint']}: {result['message']}")
        
        print(f"\n{'='*60}")
        print(f"Summary: {passed} passed, {failed} failed, {len(self.results)} total")
        print(f"{'='*60}\n")
        
        return failed == 0
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.client.aclose()


async def run_test_module(test_class, module_name: str) -> bool:
    """
    Run a test module and return success status.
    
    Args:
        test_class: Test class (not instance)
        module_name: Name of the module for reporting
        
    Returns:
        True if all tests passed, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Running: {module_name}")
    print(f"{'='*60}\n")
    
    tester = test_class()
    try:
        # Login first
        if not await tester.login():
            print(f"Failed to login. Skipping {module_name} tests.")
            return False
        
        # Run all test_* methods
        test_methods = [m for m in dir(tester) if m.startswith('test_') and callable(getattr(tester, m))]
        
        for method_name in test_methods:
            try:
                method = getattr(tester, method_name)
                if asyncio.iscoroutinefunction(method):
                    await method()
                else:
                    method()
            except Exception as e:
                tester._log_result(method_name, False, f"Exception: {e}")
        
        # Print results
        success = tester.print_results()
        return success
        
    finally:
        await tester.cleanup()
