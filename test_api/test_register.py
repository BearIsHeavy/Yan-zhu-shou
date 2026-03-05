"""
Test script for /register API endpoint
Usage: python test_register.py
"""
import httpx
import asyncio

BASE_URL = "http://localhost:8000"


async def test_register():
    """Test the /register endpoint"""
    async with httpx.AsyncClient() as client:
        # Test 1: Successful registration
        print("=" * 50)
        print("Test 1: Register new user")
        print("=" * 50)
        response = await client.post(
            f"{BASE_URL}/register",
            json={
                "email": f"test_{asyncio.get_event_loop().time()}@example.com",
                "username": f"testuser_{asyncio.get_event_loop().time()}",
                "password": "password123"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()

        # Test 2: Duplicate email
        print("=" * 50)
        print("Test 2: Duplicate email")
        print("=" * 50)
        response = await client.post(
            f"{BASE_URL}/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "password123"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()

        # Test 3: Duplicate username
        print("=" * 50)
        print("Test 3: Duplicate username")
        print("=" * 50)
        response = await client.post(
            f"{BASE_URL}/register",
            json={
                "email": "unique@example.com",
                "username": "user1",
                "password": "password123"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()

        # Test 4: Invalid email
        print("=" * 50)
        print("Test 4: Invalid email format")
        print("=" * 50)
        response = await client.post(
            f"{BASE_URL}/register",
            json={
                "email": "invalid-email",
                "username": "user2",
                "password": "password123"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()

        # Test 5: Short password
        print("=" * 50)
        print("Test 5: Password too short")
        print("=" * 50)
        response = await client.post(
            f"{BASE_URL}/register",
            json={
                "email": "user3@example.com",
                "username": "user3",
                "password": "12345"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()


if __name__ == "__main__":
    print("Starting /register API tests...\n")
    asyncio.run(test_register())
    print("Tests completed!")
