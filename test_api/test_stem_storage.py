"""
Test script for Stem Storage Logic.
Tests that stems > 255 bytes are stored in StemText table with '###' marker,
and stems <= 255 bytes are stored directly in the stem column.

Usage:
    python test_api/test_stem_storage.py

Note: Make sure the FastAPI server is running on http://127.0.0.1:8000
      and Redis server is running on localhost:6379
"""

import httpx
import random
import string
import json
import os
import tempfile

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"
USERS_URL = f"{BASE_URL}/users"
QUESTION_BANKS_URL = f"{BASE_URL}/question_banks"
UPLOAD_URL = f"{BASE_URL}/upload"

STEM_MARKER = "###"


def generate_random_email() -> str:
    """Generate a random email address for testing."""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"stem_test_{random_str}@example.com"


def generate_random_phone() -> str:
    """Generate a random phone number for testing."""
    random_digits = ''.join(random.choices(string.digits, k=10))
    return f"1{random_digits}"


def generate_random_name() -> str:
    """Generate a random name for testing."""
    return "StemTestUser_" + ''.join(random.choices(string.ascii_uppercase, k=5))


class TestStemStorage:
    """Test class for stem storage logic."""

    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.test_email = generate_random_email()
        self.test_password = "testpass123"
        self.test_name = generate_random_name()
        self.test_phone = generate_random_phone()
        self.question_bank_id = None
        self.client = httpx.Client(timeout=30.0)

    def register_and_login(self) -> None:
        """Register a new user and login to get access token."""
        print("\n" + "=" * 60)
        print("SETUP: Register and Login")
        print("=" * 60)

        # Register
        register_payload = {
            "email": self.test_email,
            "name": self.test_name,
            "password": self.test_password,
            "phone": self.test_phone,
            "gender": 1
        }
        response = self.client.post(f"{USERS_URL}/register", json=register_payload)
        print(f"Register: {response.status_code}")

        # Login
        login_payload = {
            "username": self.test_email,
            "password": self.test_password
        }
        response = self.client.post(f"{USERS_URL}/login", data=login_payload)
        assert response.status_code == 200, f"Login failed: {response.status_code}"

        self.access_token = response.json()["access_token"]
        print(f"✓ Logged in successfully")

    def test_create_question_bank(self) -> dict:
        """Create a question bank for testing."""
        print("\n" + "=" * 60)
        print("SETUP: Create Question Bank")
        print("=" * 60)

        url = f"{QUESTION_BANKS_URL}/book"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "name": f"Stem Storage Test Bank",
            "is_public": False,
            "description": "Test bank for stem storage logic"
        }

        response = self.client.post(url, json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        self.question_bank_id = data["bank_id"]
        print(f"✓ Question bank created with ID: {self.question_bank_id}")
        return data

    def test_stem_boundary_255_bytes(self) -> None:
        """
        Test stem storage at the 255-byte boundary.
        - 255 bytes or less: stored directly
        - 256 bytes or more: stored in StemText with marker
        """
        print("\n" + "=" * 60)
        print("TEST: Stem Storage Boundary (255 bytes)")
        print("=" * 60)

        url = f"{UPLOAD_URL}/question"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Test with exactly 255 bytes (should be stored directly)
        stem_255 = "A" * 255
        print(f"\nTesting with 255 bytes stem...")
        print(f"Stem length: {len(stem_255.encode('utf-8'))} bytes")

        form_data = {
            'bank_id': str(self.question_bank_id),
            'category': 'Boundary Test',
            'stem': stem_255,
            'qus_type': '1',
            'options': json.dumps({"A": "A", "B": "B"}),
            'is_public': 'false'
        }

        response = self.client.post(url, headers=headers, data=form_data)
        assert response.status_code == 200
        result = response.json()
        
        # Should NOT have marker (stored directly)
        assert result["stem"] == stem_255, f"Expected stem to be stored directly"
        assert not result["stem"].startswith(STEM_MARKER)
        print(f"✓ 255 bytes: Stored directly (no marker)")

        # Test with 256 bytes (should use StemText)
        stem_256 = "A" * 256
        print(f"\nTesting with 256 bytes stem...")
        print(f"Stem length: {len(stem_256.encode('utf-8'))} bytes")

        form_data = {
            'bank_id': str(self.question_bank_id),
            'category': 'Boundary Test',
            'stem': stem_256,
            'qus_type': '1',
            'options': json.dumps({"A": "A", "B": "B"}),
            'is_public': 'false'
        }

        response = self.client.post(url, headers=headers, data=form_data)
        assert response.status_code == 200
        result = response.json()
        
        # Should have marker (stored in StemText)
        assert result["stem"] == STEM_MARKER, f"Expected '{STEM_MARKER}' marker, got: {result['stem']}"
        print(f"✓ 256 bytes: Stored in StemText table (marker used)")

    def test_stem_unicode_characters(self) -> None:
        """
        Test stem storage with Unicode characters.
        Unicode characters may take multiple bytes in UTF-8.
        """
        print("\n" + "=" * 60)
        print("TEST: Stem Storage with Unicode Characters")
        print("=" * 60)

        url = f"{UPLOAD_URL}/question"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Chinese characters (3 bytes each in UTF-8)
        # 100 Chinese characters = 300 bytes > 255
        stem_chinese = "这是一个测试问题。" + "中" * 100
        stem_bytes = len(stem_chinese.encode('utf-8'))
        print(f"Chinese stem length: {stem_bytes} bytes")

        form_data = {
            'bank_id': str(self.question_bank_id),
            'category': 'Unicode Test',
            'stem': stem_chinese,
            'qus_type': '1',
            'options': json.dumps({"A": "A", "B": "B"}),
            'is_public': 'false'
        }

        response = self.client.post(url, headers=headers, data=form_data)
        assert response.status_code == 200
        result = response.json()
        
        if stem_bytes > 255:
            assert result["stem"] == STEM_MARKER
            print(f"✓ Unicode stem > 255 bytes: Stored in StemText table")
        else:
            assert result["stem"] == stem_chinese
            print(f"✓ Unicode stem <= 255 bytes: Stored directly")

    def test_stem_with_emoji(self) -> None:
        """
        Test stem storage with emoji characters.
        Emojis typically take 4 bytes in UTF-8.
        """
        print("\n" + "=" * 60)
        print("TEST: Stem Storage with Emoji Characters")
        print("=" * 60)

        url = f"{UPLOAD_URL}/question"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Emoji characters (4 bytes each in UTF-8)
        stem_emoji = "Question with emoji: " + "😀" * 70
        stem_bytes = len(stem_emoji.encode('utf-8'))
        print(f"Emoji stem length: {stem_bytes} bytes")

        form_data = {
            'bank_id': str(self.question_bank_id),
            'category': 'Emoji Test',
            'stem': stem_emoji,
            'qus_type': '1',
            'options': json.dumps({"A": "A", "B": "B"}),
            'is_public': 'false'
        }

        response = self.client.post(url, headers=headers, data=form_data)
        assert response.status_code == 200
        result = response.json()
        
        if stem_bytes > 255:
            assert result["stem"] == STEM_MARKER
            print(f"✓ Emoji stem > 255 bytes: Stored in StemText table")
        else:
            assert result["stem"] == stem_emoji
            print(f"✓ Emoji stem <= 255 bytes: Stored directly")

    def test_csv_with_mixed_stem_lengths(self) -> None:
        """
        Test CSV upload with mixed stem lengths.
        """
        print("\n" + "=" * 60)
        print("TEST: CSV Upload with Mixed Stem Lengths")
        print("=" * 60)

        # Create CSV with various stem lengths
        long_stem = "X" * 300  # > 255 bytes
        csv_content = f"""category,stem,qus_type,options,correct_ans_summary,full_answer,explanation
Math,"Short question",1,"{{""A"": ""1"", ""B"": ""2""}}","A","1","Simple"
Science,"{long_stem}",1,"{{""A"": ""A"", ""B"": ""B""}}","A","Answer","Explanation"
English,"Medium length question that is still under 255 bytes",1,"{{""A"": ""X"", ""B"": ""Y""}}","B","Answer","Note"
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()

        try:
            url = f"{UPLOAD_URL}/csv"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            with open(temp_file.name, 'rb') as f:
                files = {'file': ('test_mixed.csv', f, 'text/csv')}
                data = {'bank_id': self.question_bank_id}

                response = self.client.post(url, headers=headers, files=files, data=data)

                print(f"Response Status Code: {response.status_code}")
                print(f"Response Body: {response.json()}")

                assert response.status_code == 200
                result = response.json()
                assert result["questions_added"] == 3

                print(f"✓ CSV upload with mixed stem lengths: {result['questions_added']} questions added")
        finally:
            os.unlink(temp_file.name)

    def test_xml_with_mixed_stem_lengths(self) -> None:
        """
        Test XML upload with mixed stem lengths.
        """
        print("\n" + "=" * 60)
        print("TEST: XML Upload with Mixed Stem Lengths")
        print("=" * 60)

        long_stem = "Y" * 300  # > 255 bytes
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<questions>
    <question>
        <category>Math</category>
        <stem>Short question</stem>
        <qus_type>1</qus_type>
        <options>{{"A": "1", "B": "2"}}</options>
        <correct_ans_summary>A</correct_ans_summary>
        <full_answer>1</full_answer>
    </question>
    <question>
        <category>Science</category>
        <stem>{long_stem}</stem>
        <qus_type>1</qus_type>
        <options>{{"A": "A", "B": "B"}}</options>
        <correct_ans_summary>A</correct_ans_summary>
        <full_answer>A</full_answer>
        <explanation>Detailed explanation</explanation>
    </question>
</questions>
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False)
        temp_file.write(xml_content)
        temp_file.close()

        try:
            url = f"{UPLOAD_URL}/xml"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            with open(temp_file.name, 'rb') as f:
                files = {'file': ('test_mixed.xml', f, 'application/xml')}
                data = {'bank_id': self.question_bank_id}

                response = self.client.post(url, headers=headers, files=files, data=data)

                print(f"Response Status Code: {response.status_code}")
                print(f"Response Body: {response.json()}")

                assert response.status_code == 200
                result = response.json()
                assert result["questions_added"] == 2

                print(f"✓ XML upload with mixed stem lengths: {result['questions_added']} questions added")
        finally:
            os.unlink(temp_file.name)

    def cleanup(self):
        """Close the HTTP client."""
        self.client.close()

    def run_all_tests(self) -> None:
        """Run all tests in sequence."""
        print("\n" + "#" * 60)
        print("# Starting Stem Storage Logic Tests")
        print(f"# Base URL: {BASE_URL}")
        print(f"# Test Email: {self.test_email}")
        print(f"# STEM_MARKER: '{STEM_MARKER}'")
        print("#" * 60)

        try:
            # Setup
            self.register_and_login()
            self.test_create_question_bank()

            # Test boundary conditions
            self.test_stem_boundary_255_bytes()

            # Test Unicode handling
            self.test_stem_unicode_characters()
            self.test_stem_with_emoji()

            # Test file uploads
            self.test_csv_with_mixed_stem_lengths()
            self.test_xml_with_mixed_stem_lengths()

            print("\n" + "=" * 60)
            print("ALL STEM STORAGE TESTS PASSED ✓✓✓")
            print("=" * 60)

        except httpx.ConnectError:
            print("\n" + "!" * 60)
            print("ERROR: Could not connect to the API server.")
            print(f"Please make sure the server is running on {BASE_URL}")
            print("!" * 60)
            raise
        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {e}")
            raise
        finally:
            self.cleanup()


if __name__ == "__main__":
    tester = TestStemStorage()
    tester.run_all_tests()
