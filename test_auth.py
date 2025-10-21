"""
Test script to verify authentication endpoints are working correctly.
Run this after starting the Django server.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_registration():
    """Test user registration endpoint"""
    print("\n=== Testing User Registration ===")
    
    url = f"{BASE_URL}/api/auth/register/"
    data = {
        "username": "testuser",
        "full_name": "Test User",
        "email": "testuser@example.com",
        "phone_number": "+1234567890",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!"
    }
    
    print(f"POST {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            return True
        else:
            print("❌ Registration failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_login(email="testuser@example.com", password="TestPassword123!"):
    """Test user login endpoint"""
    print("\n=== Testing User Login ===")
    
    url = f"{BASE_URL}/api/auth/login/"
    data = {
        "email": email,
        "password": password
    }
    
    print(f"POST {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            return response.json()
        else:
            print("❌ Login failed!")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    print("=" * 60)
    print("Authentication Endpoints Test")
    print("=" * 60)
    print("Make sure the Django server is running at", BASE_URL)
    print("=" * 60)
    
    # Test registration
    reg_success = test_registration()
    
    # Test login
    if reg_success:
        login_result = test_login()
        
        if login_result:
            print("\n" + "=" * 60)
            print("✅ All tests passed!")
            print("=" * 60)
            print("\nYou can use this access token for authenticated requests:")
            print(f"Authorization: Bearer {login_result.get('access')}")
            print("=" * 60)
        else:
            print("\n❌ Login test failed")
    else:
        print("\n⚠️ Skipping login test due to registration failure")
        print("Note: If user already exists, try with different credentials")


if __name__ == "__main__":
    main()
