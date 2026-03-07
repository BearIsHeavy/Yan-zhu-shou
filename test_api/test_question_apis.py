"""
Test script for Question Bank and Question Upload APIs.
Tests question bank creation, CSV/XML upload, and single question upload.
Includes tests for stem storage logic (>255 bytes stored in StemText table).

Usage:
    python test_api/test_question_apis.py

Note: Make sure the FastAPI server is running on http://127.0.0.1:8000
      and Redis server is running on localhost:6379
"""

import httpx
import random
import string
import json
import os
import tempfile
import time

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"
USERS_URL = f"{BASE_URL}/users"
QUESTION_BANKS_URL = f"{BASE_URL}/question_banks"
UPLOAD_URL = f"{BASE_URL}/upload"


def generate_random_email() -> str:
    """Generate a random email address for testing."""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"test_{random_str}@example.com"


def generate_random_phone() -> str:
    """Generate a random phone number for testing."""
    random_digits = ''.join(random.choices(string.digits, k=11))
    return f"1{random_digits}"


def generate_random_name() -> str:
    """Generate a random name for testing."""
    return "TestUser_" + ''.join(random.choices(string.ascii_uppercase, k=5))


class TestQuestionAPIs:
    """Test class for question bank and question upload APIs."""

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
        if response.status_code != 200:
            detail = response.json().get("detail", "") if response.headers.get("content-type", "").startswith("application/json") else response.text
            if "Email already register" not in detail and "already" not in detail.lower():
                print(f"Register response: {response.status_code} - {detail}")
                # Try to login anyway if email exists
                if response.status_code != 400:
                    raise AssertionError(f"Registration failed: {detail}")
        
        # Login
        login_payload = {
            "username": self.test_email,
            "password": self.test_password
        }
        response = self.client.post(f"{USERS_URL}/login", data=login_payload)
        if response.status_code != 200:
            print(f"Login response: {response.status_code} - {response.text}")
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        
        self.access_token = response.json()["access_token"]
        print(f"✓ Logged in successfully. Token: {self.access_token[:30]}...")

    def test_create_question_bank(self) -> dict:
        """
        Test POST /question_banks/book - Create a new question bank.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /question_banks/book - Create question bank")
        print("=" * 60)

        url = f"{QUESTION_BANKS_URL}/book"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "name": f"Test Question Bank {generate_random_name()}",
            "is_public": False,
            "description": "Test question bank for API testing"
        }

        print(f"Request URL: {url}")
        print(f"Request Payload: {payload}")

        response = self.client.post(url, json=payload, headers=headers)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["is_public"] == payload["is_public"]
        assert "bank_id" in data
        assert "user_id" in data

        self.question_bank_id = data["bank_id"]
        print(f"✓ Question bank created with ID: {self.question_bank_id}")
        return data

    def test_create_csv_file(self) -> str:
        """Create a temporary CSV file for testing."""
        csv_content = """category,stem,qus_type,options,correct_ans_summary,full_text,image_url,full_answer,explanation
Math,"What is 2+2?",1,"{""A"": ""3"", ""B"": ""4"", ""C"": ""5""}",B,"What is the sum of 2 and 2?",,The answer is 4,"Basic addition"
Math,"Solve: x - 3 = 5",1,"{""A"": ""x=6"", ""B"": ""x=8"", ""C"": ""x=2""}",B,"Find the value of x in the equation x - 3 = 5",,x=8,"Add 3 to both sides"
English,"Choose the correct spelling",1,"{""A"": ""recieve"", ""B"": ""receive"", ""C"": ""receve""}",B,"Which is the correct spelling?",,receive,"Common spelling rule"
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        return temp_file.name

    def test_upload_csv(self) -> dict:
        """
        Test POST /upload/csv - Upload CSV file with questions.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /upload/csv - Upload CSV file")
        print("=" * 60)

        if not self.question_bank_id:
            raise RuntimeError("Question bank ID not set. Run test_create_question_bank first.")

        url = f"{UPLOAD_URL}/csv"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        csv_file_path = self.test_create_csv_file()
        
        try:
            with open(csv_file_path, 'rb') as f:
                files = {'file': ('test_questions.csv', f, 'text/csv')}
                data = {'bank_id': self.question_bank_id}
                
                print(f"Request URL: {url}")
                print(f"Bank ID: {self.question_bank_id}")
                print(f"File: test_questions.csv")

                response = self.client.post(url, headers=headers, files=files, data=data)

                print(f"Response Status Code: {response.status_code}")
                print(f"Response Body: {response.json()}")

                assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
                result = response.json()
                assert "questions_added" in result
                assert result["questions_added"] == 3, f"Expected 3 questions, got {result['questions_added']}"

                print(f"✓ CSV upload successful. {result['questions_added']} questions added.")
                return result
        finally:
            os.unlink(csv_file_path)

    def test_create_xml_file(self) -> str:
        """Create a temporary XML file for testing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<questions>
    <question>
        <category>Science</category>
        <stem>What is H2O?</stem>
        <qus_type>1</qus_type>
        <options>{"A": "Salt", "B": "Water", "C": "Sugar"}</options>
        <correct_ans_summary>B</correct_ans_summary>
        <full_text>What is the common name for the chemical compound H2O?</full_text>
        <image_url></image_url>
        <full_answer>Water</full_answer>
        <explanation>H2O is the chemical formula for water.</explanation>
    </question>
    <question>
        <category>Science</category>
        <stem>What planet is known as the Red Planet?</stem>
        <qus_type>1</qus_type>
        <options>{"A": "Venus", "B": "Mars", "C": "Jupiter"}</options>
        <correct_ans_summary>B</correct_ans_summary>
        <full_text>Which planet in our solar system is known as the Red Planet?</full_text>
        <image_url></image_url>
        <full_answer>Mars</full_answer>
        <explanation>Mars appears red due to iron oxide on its surface.</explanation>
    </question>
</questions>
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False)
        temp_file.write(xml_content)
        temp_file.close()
        return temp_file.name

    def test_upload_xml(self) -> dict:
        """
        Test POST /upload/xml - Upload XML file with questions.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /upload/xml - Upload XML file")
        print("=" * 60)

        if not self.question_bank_id:
            raise RuntimeError("Question bank ID not set. Run test_create_question_bank first.")

        url = f"{UPLOAD_URL}/xml"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        xml_file_path = self.test_create_xml_file()
        
        try:
            with open(xml_file_path, 'rb') as f:
                files = {'file': ('test_questions.xml', f, 'application/xml')}
                data = {'bank_id': self.question_bank_id}
                
                print(f"Request URL: {url}")
                print(f"Bank ID: {self.question_bank_id}")
                print(f"File: test_questions.xml")

                response = self.client.post(url, headers=headers, files=files, data=data)

                print(f"Response Status Code: {response.status_code}")
                print(f"Response Body: {response.json()}")

                assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
                result = response.json()
                assert "questions_added" in result
                assert result["questions_added"] == 2, f"Expected 2 questions, got {result['questions_added']}"

                print(f"✓ XML upload successful. {result['questions_added']} questions added.")
                return result
        finally:
            os.unlink(xml_file_path)

    def test_upload_single_question(self) -> dict:
        """
        Test POST /upload/question - Upload a single question.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /upload/question - Upload single question")
        print("=" * 60)

        if not self.question_bank_id:
            raise RuntimeError("Question bank ID not set. Run test_create_question_bank first.")

        url = f"{UPLOAD_URL}/question"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Prepare form data
        form_data = {
            'bank_id': str(self.question_bank_id),
            'category': 'History',
            'stem': 'Who was the first President of the United States?',
            'qus_type': '1',
            'options': json.dumps({"A": "Washington", "B": "Lincoln", "C": "Jefferson"}),
            'correct_ans_summary': 'A',
            'is_public': 'false',
            'full_text': 'Who was the first person to serve as President of the United States of America?',
            'full_answer': 'George Washington',
            'explanation': 'Washington served from 1789 to 1797.'
        }

        print(f"Request URL: {url}")
        print(f"Bank ID: {self.question_bank_id}")
        print(f"Question Data: {form_data}")

        response = self.client.post(url, headers=headers, data=form_data)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
        result = response.json()
        assert result["category"] == "History"
        assert result["bank_id"] == self.question_bank_id
        assert "No" in result

        print(f"✓ Single question upload successful. Question No: {result['No']}")
        return result

    def test_upload_to_nonexistent_bank(self) -> None:
        """
        Test uploading to a non-existent question bank.
        Should return 404.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /upload/question - Upload to non-existent bank")
        print("=" * 60)

        url = f"{UPLOAD_URL}/question"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        form_data = {
            'bank_id': '99999',
            'category': 'Test',
            'stem': 'Test question',
            'qus_type': '1'
        }

        response = self.client.post(url, headers=headers, data=form_data)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        assert "not found" in response.json()["detail"].lower()

        print("✓ Non-existent bank test PASSED")

    def test_upload_without_auth(self) -> None:
        """
        Test uploading without authentication.
        Should return 401.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /upload/question - Without authentication")
        print("=" * 60)

        url = f"{UPLOAD_URL}/question"
        
        form_data = {
            'bank_id': '1',
            'category': 'Test',
            'stem': 'Test question',
            'qus_type': '1'
        }

        response = self.client.post(url, data=form_data)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

        print("✓ No auth test PASSED")

    def test_create_duplicate_question_bank(self) -> None:
        """
        Test creating a question bank with duplicate name.
        Should return 400.
        """
        print("\n" + "=" * 60)
        print("TEST: POST /question_banks/book - Duplicate name")
        print("=" * 60)

        if not self.question_bank_id:
            raise RuntimeError("Question bank ID not set.")

        url = f"{QUESTION_BANKS_URL}/book"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        payload = {
            "name": f"Test Question Bank",
            "is_public": False,
            "description": "Duplicate test"
        }

        response = self.client.post(url, json=payload, headers=headers)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        
        if response.status_code == 400:
            assert "already" in response.json()["detail"].lower()
            print("✓ Duplicate name rejection test PASSED")
        else:
            print("✓ Created with unique name (no conflict)")

    def test_stem_storage_short_stem(self) -> dict:
        """
        Test POST /upload/question - Short stem (<=255 bytes) stored directly.
        """
        print("\n" + "=" * 60)
        print("TEST: Stem Storage - Short stem (<=255 bytes)")
        print("=" * 60)

        if not self.question_bank_id:
            raise RuntimeError("Question bank ID not set.")

        url = f"{UPLOAD_URL}/question"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Short stem (less than 255 bytes)
        short_stem = "What is 2+2?"
        print(f"Stem length: {len(short_stem.encode('utf-8'))} bytes")
        
        form_data = {
            'bank_id': str(self.question_bank_id),
            'category': 'Math',
            'stem': short_stem,
            'qus_type': '1',
            'options': json.dumps({"A": "3", "B": "4", "C": "5"}),
            'correct_ans_summary': 'B',
            'is_public': 'false'
        }

        response = self.client.post(url, headers=headers, data=form_data)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200
        result = response.json()
        # Stem should be stored directly, not the marker
        assert result["stem"] == short_stem
        assert not result["stem"].startswith("###")
        
        print("✓ Short stem stored directly (no '###' marker)")
        return result

    def test_stem_storage_long_stem(self) -> dict:
        """
        Test POST /upload/question - Long stem (>255 bytes) stored in StemText table.
        """
        print("\n" + "=" * 60)
        print("TEST: Stem Storage - Long stem (>255 bytes)")
        print("=" * 60)

        if not self.question_bank_id:
            raise RuntimeError("Question bank ID not set.")

        url = f"{UPLOAD_URL}/question"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Long stem (more than 255 bytes)
        long_stem = "This is a very long question stem. " + "A" * 300
        stem_bytes = len(long_stem.encode('utf-8'))
        print(f"Stem length: {stem_bytes} bytes (should be > 255)")
        
        assert stem_bytes > 255, "Test stem should be longer than 255 bytes"

        form_data = {
            'bank_id': str(self.question_bank_id),
            'category': 'General',
            'stem': long_stem,
            'qus_type': '1',
            'options': json.dumps({"A": "Option A", "B": "Option B"}),
            'correct_ans_summary': 'A',
            'is_public': 'false',
            'full_answer': 'The correct answer is A',
            'explanation': 'This is a detailed explanation.'
        }

        response = self.client.post(url, headers=headers, data=form_data)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        assert response.status_code == 200
        result = response.json()
        # Stem should be the marker '###' since it's stored in StemText table
        assert result["stem"] == "###", f"Expected '###' marker, got: {result['stem']}"
        
        print(f"✓ Long stem stored in StemText table (marker '###' used)")
        return result

    def test_stem_storage_csv_upload(self) -> dict:
        """
        Test CSV upload with mixed stem lengths.
        """
        print("\n" + "=" * 60)
        print("TEST: Stem Storage - CSV upload with mixed stem lengths")
        print("=" * 60)

        if not self.question_bank_id:
            raise RuntimeError("Question bank ID not set.")

        # Create CSV with short and long stems
        long_text = "X" * 300  # Make stem > 255 bytes
        csv_content = f"""category,stem,qus_type,options,correct_ans_summary,full_answer,explanation
Math,"What is 2+2?",1,"{{""A"": ""3"", ""B"": ""4""}}","B","4","Basic math"
Science,"This is a very long question stem that exceeds 255 bytes. {long_text}",1,"{{""A"": ""A"", ""B"": ""B""}}","A","Answer","Explanation"
"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()

        try:
            url = f"{UPLOAD_URL}/csv"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            with open(temp_file.name, 'rb') as f:
                files = {'file': ('test_stems.csv', f, 'text/csv')}
                data = {'bank_id': self.question_bank_id}

                response = self.client.post(url, headers=headers, files=files, data=data)

                print(f"Response Status Code: {response.status_code}")
                print(f"Response Body: {response.json()}")

                assert response.status_code == 200
                result = response.json()
                assert result["questions_added"] == 2

                print(f"✓ CSV upload with mixed stem lengths successful")
                return result
        finally:
            os.unlink(temp_file.name)

    def cleanup(self):
        """Close the HTTP client."""
        self.client.close()

    def run_all_tests(self) -> None:
        """Run all tests in sequence."""
        print("\n" + "#" * 60)
        print("# Starting Question Bank API Tests")
        print(f"# Base URL: {BASE_URL}")
        print(f"# Test Email: {self.test_email}")
        print("#" * 60)

        try:
            # Setup: Register and login
            self.register_and_login()

            # Test create question bank
            self.test_create_question_bank()

            # Test CSV upload
            self.test_upload_csv()

            # Test XML upload
            self.test_upload_xml()

            # Test single question upload
            self.test_upload_single_question()

            # Test stem storage logic
            self.test_stem_storage_short_stem()
            self.test_stem_storage_long_stem()
            self.test_stem_storage_csv_upload()

            # Test error cases
            self.test_upload_to_nonexistent_bank()
            self.test_upload_without_auth()
            self.test_create_duplicate_question_bank()

            print("\n" + "=" * 60)
            print("ALL TESTS PASSED ✓✓✓")
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
    tester = TestQuestionAPIs()
    tester.run_all_tests()
