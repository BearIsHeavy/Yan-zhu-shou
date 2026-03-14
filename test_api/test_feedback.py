"""
Test script for feedback API endpoints.
Tests feedback submission, voting, and management endpoints.

Usage:
    python test_feedback.py

Note: Make sure the FastAPI server is running on http://127.0.0.1:8000
      and Redis server is running on localhost:6379
"""

import requests
import random
import string
import time

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000/api/feedback"
USERS_URL = "http://127.0.0.1:8000/users"


def generate_random_email() -> str:
    """Generate a random email address for testing."""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"feedback_{random_str}@example.com"


def generate_random_name() -> str:
    """Generate a random name for testing."""
    return "FeedbackUser_" + ''.join(random.choices(string.ascii_uppercase, k=5))


class TestFeedbackAPIs:
    """Test class for feedback-related API endpoints."""

    def __init__(self):
        self.user1_token = None
        self.user2_token = None
        self.user1_email = generate_random_email()
        self.user2_email = generate_random_email()
        self.password = "testpass123"
        self.feedback_id = None

    def _register_and_login(self, email: str) -> str:
        """Register a new user and login, return access token."""
        # Register
        register_payload = {
            "email": email,
            "name": generate_random_name(),
            "password": self.password,
        }
        response = requests.post(f"{USERS_URL}/register", json=register_payload)
        if response.status_code != 200:
            # User might already exist, try login
            pass
        
        # Login
        login_payload = {
            "username": email,
            "password": self.password
        }
        response = requests.post(f"{USERS_URL}/login", data=login_payload)
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]

    def setup_users(self) -> None:
        """Setup two test users."""
        print("\n" + "=" * 60)
        print("SETUP: Creating test users")
        print("=" * 60)
        
        self.user1_token = self._register_and_login(self.user1_email)
        self.user2_token = self._register_and_login(self.user2_email)
        
        print(f"User 1 created: {self.user1_email}")
        print(f"User 2 created: {self.user2_email}")
        print("✓ Setup complete")

    def test_submit_feedback(self) -> dict:
        """
        Test POST /feedback - Submit new feedback.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /feedback - Submit new feedback")
        print("=" * 60)

        url = BASE_URL
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        payload = {
            "content": "The app crashes when I try to upload large files. Please fix this bug.",
            "category": "bug"
        }

        print(f"Request URL: {url}")
        print(f"Request Payload: {payload}")

        response = requests.post(url, json=payload, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["content"] == payload["content"]
        assert data["category"] == payload["category"]
        assert data["status"] == "pending"
        assert "id" in data
        
        self.feedback_id = data["id"]
        print(f"✓ Feedback created with ID: {self.feedback_id}")
        return data

    def test_submit_feedback_rate_limit(self) -> None:
        """
        Test POST /feedback - Rate limiting (1 per day).
        """
        print("\n" + "=" * 60)
        print("TEST: POST /feedback - Rate limiting")
        print("=" * 60)

        url = BASE_URL
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        payload = {
            "content": "This is a second feedback submission on the same day.",
            "category": "feature"
        }

        print(f"Request URL: {url}")
        print(f"Request Payload: {payload}")

        response = requests.post(url, json=payload, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 429, f"Expected 429, got {response.status_code}"
        assert "once every" in response.json()["detail"].lower()

        print("✓ Rate limit test PASSED")

    def test_list_feedbacks(self) -> dict:
        """
        Test GET /feedback - List all feedbacks.
        """
        print("\n" + "=" * 60)
        print("TEST: GET /feedback - List all feedbacks")
        print("=" * 60)

        url = BASE_URL
        params = {"page": 1, "page_size": 10}

        print(f"Request URL: {url}")
        print(f"Params: {params}")

        response = requests.get(url, params=params)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) >= 1

        print("✓ List feedbacks test PASSED")
        return data

    def test_list_feedbacks_filter_status(self) -> None:
        """
        Test GET /feedback with status filter.
        """
        print("\n" + "=" * 60)
        print("TEST: GET /feedback?status=pending - Filter by status")
        print("=" * 60)

        url = BASE_URL
        params = {"status_filter": "pending", "page": 1, "page_size": 10}

        response = requests.get(url, params=params)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "pending"

        print("✓ Filter by status test PASSED")

    def test_list_feedbacks_filter_category(self) -> None:
        """
        Test GET /feedback with category filter.
        """
        print("\n" + "=" * 60)
        print("TEST: GET /feedback?category=bug - Filter by category")
        print("=" * 60)

        url = BASE_URL
        params = {"category": "bug", "page": 1, "page_size": 10}

        response = requests.get(url, params=params)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category"] == "bug"

        print("✓ Filter by category test PASSED")

    def test_get_feedback(self) -> dict:
        """
        Test GET /feedback/{id} - Get feedback by ID.
        """
        print("\n" + "=" * 60)
        print(f"TEST: GET /feedback/{self.feedback_id} - Get feedback by ID")
        print("=" * 60)

        url = f"{BASE_URL}/{self.feedback_id}"
        headers = {"Authorization": f"Bearer {self.user1_token}"}

        response = requests.get(url, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["id"] == self.feedback_id
        assert "has_voted" in data

        print("✓ Get feedback test PASSED")
        return data

    def test_vote_feedback(self) -> dict:
        """
        Test POST /feedback/{id}/vote - Vote on feedback.
        """
        print("\n" + "=" * 60)
        print(f"TEST: POST /feedback/{self.feedback_id}/vote - Vote on feedback")
        print("=" * 60)

        url = f"{BASE_URL}/{self.feedback_id}/vote"
        headers = {"Authorization": f"Bearer {self.user2_token}"}

        response = requests.post(url, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["has_voted"] == True
        assert data["vote_count"] >= 1

        print("✓ Vote feedback test PASSED")
        return data

    def test_vote_toggle(self) -> None:
        """
        Test POST /feedback/{id}/vote - Toggle vote (remove vote).
        """
        print("\n" + "=" * 60)
        print(f"TEST: POST /feedback/{self.feedback_id}/vote - Toggle vote off")
        print("=" * 60)

        url = f"{BASE_URL}/{self.feedback_id}/vote"
        headers = {"Authorization": f"Bearer {self.user2_token}"}

        # Vote again to toggle off
        response = requests.post(url, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert data["has_voted"] == False

        print("✓ Vote toggle test PASSED")

    def test_vote_own_feedback(self) -> None:
        """
        Test POST /feedback/{id}/vote - Cannot vote on own feedback.
        """
        print("\n" + "=" * 60)
        print(f"TEST: POST /feedback/{self.feedback_id}/vote - Vote on own feedback (should fail)")
        print("=" * 60)

        url = f"{BASE_URL}/{self.feedback_id}/vote"
        headers = {"Authorization": f"Bearer {self.user1_token}"}  # User 1 owns the feedback

        response = requests.post(url, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "cannot vote on your own feedback" in response.json()["detail"].lower()

        print("✓ Vote own feedback test PASSED")

    def test_get_vote_status(self) -> None:
        """
        Test GET /feedback/{id}/vote - Get vote status.
        """
        print("\n" + "=" * 60)
        print(f"TEST: GET /feedback/{self.feedback_id}/vote - Get vote status")
        print("=" * 60)

        url = f"{BASE_URL}/{self.feedback_id}/vote"
        headers = {"Authorization": f"Bearer {self.user2_token}"}

        response = requests.get(url, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert "has_voted" in data
        assert "vote_count" in data

        print("✓ Get vote status test PASSED")

    def test_update_feedback_status(self) -> dict:
        """
        Test PUT /feedback/{id} - Update feedback status (developer action).
        """
        print("\n" + "=" * 60)
        print(f"TEST: PUT /feedback/{self.feedback_id} - Update feedback status")
        print("=" * 60)

        url = f"{BASE_URL}/{self.feedback_id}"
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        payload = {
            "status": "in_progress",
            "developer_response": "We are looking into this issue. Thanks for reporting!"
        }

        print(f"Request URL: {url}")
        print(f"Request Payload: {payload}")

        response = requests.put(url, json=payload, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["developer_response"] == payload["developer_response"]

        print("✓ Update feedback test PASSED")
        return data

    def test_get_feedback_stats(self) -> dict:
        """
        Test GET /feedback/stats - Get feedback statistics.
        """
        print("\n" + "=" * 60)
        print("TEST: GET /feedback/stats - Get feedback statistics")
        print("=" * 60)

        url = f"{BASE_URL}/stats"
        headers = {"Authorization": f"Bearer {self.user1_token}"}

        response = requests.get(url, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert "total_count" in data
        assert "by_status" in data
        assert "by_category" in data

        print("✓ Get feedback stats test PASSED")
        return data

    def test_get_my_feedback(self) -> dict:
        """
        Test GET /feedback/me/submissions - Get user's own feedback.
        """
        print("\n" + "=" * 60)
        print("TEST: GET /feedback/me/submissions - Get my feedback")
        print("=" * 60)

        url = f"{BASE_URL}/me/submissions"
        headers = {"Authorization": f"Bearer {self.user1_token}"}

        response = requests.get(url, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

        print("✓ Get my feedback test PASSED")
        return data

    def test_get_submission_status(self) -> dict:
        """
        Test GET /feedback/me/submission-status - Check submission status.
        """
        print("\n" + "=" * 60)
        print("TEST: GET /feedback/me/submission-status - Check submission status")
        print("=" * 60)

        url = f"{BASE_URL}/me/submission-status"
        headers = {"Authorization": f"Bearer {self.user1_token}"}

        response = requests.get(url, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert "can_submit" in data
        assert data["can_submit"] == False  # Should be False due to rate limit

        print("✓ Get submission status test PASSED")
        return data

    def test_get_feedback_not_found(self) -> None:
        """
        Test GET /feedback/{id} - Non-existent feedback.
        """
        print("\n" + "=" * 60)
        print("TEST: GET /feedback/999999 - Non-existent feedback")
        print("=" * 60)

        url = f"{BASE_URL}/999999"
        headers = {"Authorization": f"Bearer {self.user1_token}"}

        response = requests.get(url, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        print("✓ Not found test PASSED")

    def test_delete_feedback(self) -> None:
        """
        Test DELETE /feedback/{id} - Delete feedback (author, no votes).
        """
        print("\n" + "=" * 60)
        print("TEST: DELETE /feedback/{id} - Create and delete feedback")
        print("=" * 60)

        # Create a new feedback to delete
        url = BASE_URL
        headers = {"Authorization": f"Bearer {self.user2_token}"}
        payload = {
            "content": "This feedback will be deleted immediately.",
            "category": "other"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        feedback_id = response.json()["id"]
        print(f"Created feedback with ID: {feedback_id}")

        # Delete it
        delete_url = f"{BASE_URL}/{feedback_id}"
        response = requests.delete(delete_url, headers=headers)

        print(f"Response Status Code: {response.status_code}")

        assert response.status_code == 204, f"Expected 204, got {response.status_code}"

        # Verify it's deleted
        get_response = requests.get(delete_url, headers=headers)
        assert get_response.status_code == 404

        print("✓ Delete feedback test PASSED")

    def test_sort_feedbacks(self) -> None:
        """
        Test GET /feedback with different sort options.
        """
        print("\n" + "=" * 60)
        print("TEST: GET /feedback?sort_by=created_at - Sort by created_at")
        print("=" * 60)

        url = BASE_URL
        params = {"sort_by": "created_at", "page": 1, "page_size": 10}

        response = requests.get(url, params=params)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200

        print("✓ Sort feedbacks test PASSED")

    def run_all_tests(self) -> None:
        """Run all tests in sequence."""
        print("\n" + "#" * 60)
        print("# Starting Feedback API Tests")
        print(f"# Base URL: {BASE_URL}")
        print("#" * 60)

        try:
            # Setup
            self.setup_users()

            # Test feedback submission
            self.test_submit_feedback()
            
            # Test rate limiting
            self.test_submit_feedback_rate_limit()

            # Test listing feedbacks
            self.test_list_feedbacks()
            self.test_list_feedbacks_filter_status()
            self.test_list_feedbacks_filter_category()

            # Test getting single feedback
            self.test_get_feedback()

            # Test voting
            self.test_vote_feedback()
            self.test_vote_toggle()
            self.test_vote_own_feedback()
            self.test_get_vote_status()

            # Test updating feedback
            self.test_update_feedback_status()

            # Test stats
            self.test_get_feedback_stats()

            # Test user-specific endpoints
            self.test_get_my_feedback()
            self.test_get_submission_status()

            # Test error cases
            self.test_get_feedback_not_found()

            # Test deletion
            self.test_delete_feedback()

            # Test sorting
            self.test_sort_feedbacks()

            print("\n" + "=" * 60)
            print("ALL FEEDBACK TESTS PASSED ✓")
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
    tester = TestFeedbackAPIs()
    tester.run_all_tests()
