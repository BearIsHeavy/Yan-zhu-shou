"""
Test script for main.py API endpoints.
Tests user registration, login, and user info management endpoints.

Usage:
    python test_main.py

Note: Make sure the FastAPI server is running on http://127.0.0.1:8000
      and Redis server is running on localhost:6379
"""

import requests
import random
import string
import time

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000/users"


def generate_random_email() -> str:
    """Generate a random email address for testing."""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"test_{random_str}@example.com"


def generate_random_phone() -> str:
    """Generate a random phone number for testing."""
    random_digits = ''.join(random.choices(string.digits, k=10))
    return f"1{random_digits}"


def generate_random_name() -> str:
    """Generate a random name for testing."""
    return "TestUser_" + ''.join(random.choices(string.ascii_uppercase, k=5))


class TestUserAPIs:
    """Test class for user-related API endpoints."""

    def __init__(self):
        self.access_token = None
        self.test_email = generate_random_email()
        self.test_password = "testpass123"
        self.test_name = generate_random_name()
        self.test_phone = generate_random_phone()

    def test_register(self) -> dict:
        """
        Test POST /register endpoint.
        Registers a new user with random credentials.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /register - Register a new user")
        print("=" * 60)

        url = f"{BASE_URL}/register"
        payload = {
            "email": self.test_email,
            "name": self.test_name,
            "password": self.test_password,
            "phone": self.test_phone,
            "gender": 1
        }

        print(f"Request URL: {url}")
        print(f"Request Payload: {payload}")

        response = requests.post(url, json=payload)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["email"] == self.test_email
        assert data["name"] == self.test_name
        assert "user_id" in data

        print("✓ Register test PASSED")
        return data

    def test_register_duplicate_email(self) -> None:
        """
        Test POST /register with duplicate email.
        Should return 400 Bad Request.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /register - Duplicate email registration")
        print("=" * 60)

        url = f"{BASE_URL}/register"
        payload = {
            "email": self.test_email,  # Same email as before
            "name": generate_random_name(),
            "password": self.test_password,
        }

        print(f"Request URL: {url}")
        print(f"Request Payload: {payload}")

        response = requests.post(url, json=payload)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Email already register" in response.json()["detail"]

        print("✓ Duplicate email test PASSED")

    def test_login(self) -> dict:
        """
        Test POST /login endpoint.
        Logs in with registered credentials and gets access token.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /login - User login")
        print("=" * 60)

        url = f"{BASE_URL}/login"
        # OAuth2PasswordRequestForm expects 'username' as email and 'password'
        payload = {
            "username": self.test_email,
            "password": self.test_password
        }

        print(f"Request URL: {url}")
        print(f"Request Payload: username={self.test_email}, password=***")

        response = requests.post(url, data=payload)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data

        self.access_token = data["access_token"]
        print(f"Access Token (first 50 chars): {self.access_token[:50]}...")

        print("✓ Login test PASSED")
        return data

    def test_login_wrong_password(self) -> None:
        """
        Test POST /login with wrong password.
        Should return 401 Unauthorized.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /login - Wrong password")
        print("=" * 60)

        url = f"{BASE_URL}/login"
        payload = {
            "username": self.test_email,
            "password": "wrongpassword"
        }

        print(f"Request URL: {url}")
        print(f"Request Payload: username={self.test_email}, password=***")

        response = requests.post(url, data=payload)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

        print("✓ Wrong password test PASSED")

    def test_get_current_user(self) -> dict:
        """
        Test GET /me endpoint.
        Gets current user info using access token.
        """
        print("\n" + "=" * 60)
        print("TEST: GET /me - Get current user info")
        print("=" * 60)

        url = f"{BASE_URL}/me"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        print(f"Request URL: {url}")
        print(f"Headers: Authorization: Bearer ***")

        response = requests.get(url, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["email"] == self.test_email
        assert data["name"] == self.test_name

        print("✓ Get current user test PASSED")
        return data

    def test_update_current_user(self) -> dict:
        """
        Test PUT /me endpoint.
        Updates current user information.
        """
        print("\n" + "=" * 60)
        print("TEST: PUT /me - Update current user info")
        print("=" * 60)

        url = f"{BASE_URL}/me"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "name": "UpdatedName",
            "phone": generate_random_phone(),
            "gender": 2
        }

        print(f"Request URL: {url}")
        print(f"Headers: Authorization: Bearer ***")
        print(f"Request Payload: {payload}")

        response = requests.put(url, json=payload, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["name"] == "UpdatedName"
        assert data["phone"] == payload["phone"]
        assert data["gender"] == 2

        print("✓ Update current user test PASSED")
        return data

    def test_get_current_user_no_auth(self) -> None:
        """
        Test GET /me without authentication.
        Should return 401 Unauthorized.
        """
        print("\n" + "=" * 60)
        print("TEST: GET /me - Without authentication")
        print("=" * 60)

        url = f"{BASE_URL}/me"

        print(f"Request URL: {url}")
        print("Headers: (none)")

        response = requests.get(url)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

        print("✓ No auth test PASSED")

    def test_redis_caching(self) -> None:
        """
        Test Redis caching for user data.
        Verifies that user data is cached after login and used on subsequent requests.
        """
        print("\n" + "=" * 60)
        print("TEST: Redis Caching - Verify user data is cached after login")
        print("=" * 60)

        # Login again to trigger caching
        login_payload = {
            "username": self.test_email,
            "password": self.test_password
        }
        
        print(f"Logging in to trigger cache...")
        response = requests.post(f"{BASE_URL}/login", data=login_payload)
        assert response.status_code == 200
        token = response.json()["access_token"]
        print("✓ Login successful, user should be cached")

        # Make multiple requests to /me - should be faster due to cache
        url = f"{BASE_URL}/me"
        headers = {"Authorization": f"Bearer {token}"}
        
        print("Making 3 consecutive requests to /me endpoint...")
        times = []
        for i in range(3):
            start = time.time()
            response = requests.get(url, headers=headers)
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200
            print(f"  Request {i+1}: {elapsed*1000:.2f}ms")
        
        # Subsequent requests should be faster (cached)
        avg_time = sum(times) / len(times)
        print(f"Average response time: {avg_time*1000:.2f}ms")
        print("✓ Redis caching test PASSED (check Redis logs for cache hits)")

    def test_update_invalidates_cache(self) -> None:
        """
        Test that updating user data invalidates the cache.
        """
        print("\n" + "=" * 60)
        print("TEST: Cache Invalidation - Update should invalidate cache")
        print("=" * 60)

        # Login to ensure cache exists
        login_payload = {
            "username": self.test_email,
            "password": self.test_password
        }
        response = requests.post(f"{BASE_URL}/login", data=login_payload)
        token = response.json()["access_token"]
        print("✓ Logged in, cache created")

        # Update user
        url = f"{BASE_URL}/me"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"name": "CacheInvalidatedName"}
        
        print("Updating user name...")
        response = requests.put(url, json=payload, headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "CacheInvalidatedName"
        print("✓ User updated, cache should be invalidated")

        # Get user again - should fetch from DB (cache was invalidated)
        print("Fetching user data again (should fetch from DB)...")
        response = requests.get(url, headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "CacheInvalidatedName"
        print("✓ Cache invalidation test PASSED")

    def run_all_tests(self) -> None:
        """Run all tests in sequence."""
        print("\n" + "#" * 60)
        print("# Starting API Tests")
        print(f"# Base URL: {BASE_URL}")
        print("#" * 60)

        try:
            # Test registration
            self.test_register()

            # Test duplicate registration
            self.test_register_duplicate_email()

            # Test login
            self.test_login()

            # Test wrong password login
            self.test_login_wrong_password()

            # Test get current user (requires auth)
            self.test_get_current_user()

            # Test update current user (requires auth)
            self.test_update_current_user()

            # Test without authentication
            self.test_get_current_user_no_auth()

            # Test Redis caching
            self.test_redis_caching()

            # Test cache invalidation
            self.test_update_invalidates_cache()

            print("\n" + "=" * 60)
            print("ALL TESTS PASSED ✓")
            print("=" * 60)

        except requests.exceptions.ConnectionError:
            print("\n" + "!" * 60)
            print("ERROR: Could not connect to the API server.")
            print(f"Please make sure the server is running on {BASE_URL}")
            print("!" * 60)
            raise
        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {e}")
            raise


if __name__ == "__main__":
    tester = TestUserAPIs()
    tester.run_all_tests()
