#!/usr/bin/env python3
"""
Firebase Authentication Integration Test Script
This script tests the Firebase authentication integration with the FastAPI backend.
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_firebase_auth_integration():
    """Test Firebase authentication integration"""
    print("🔥 Testing Firebase Authentication Integration")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if server is running
    print("\n1. Testing server connectivity...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the FastAPI server is running on port 8000")
        return False
    
    # Test 2: Check authentication endpoints
    print("\n2. Testing authentication endpoints...")
    
    # Test login endpoint
    try:
        response = requests.post(f"{base_url}/api/auth/login", 
                                json={"idToken": "test-token"}, 
                                timeout=5)
        if response.status_code in [400, 401]:  # Expected for invalid token
            print("✅ Login endpoint is accessible")
        else:
            print(f"⚠️  Login endpoint returned unexpected status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Login endpoint error: {e}")
    
    # Test profile endpoint (should require authentication)
    try:
        response = requests.get(f"{base_url}/api/auth/profile", timeout=5)
        if response.status_code == 401:  # Expected for unauthenticated request
            print("✅ Profile endpoint requires authentication")
        else:
            print(f"⚠️  Profile endpoint returned unexpected status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Profile endpoint error: {e}")
    
    # Test 3: Check static file serving
    print("\n3. Testing static file serving...")
    
    static_files = [
        "/static/js/firebase-auth.js",
        "/static/js/firebase-config.js",
        "/static/css/auth.css",
        "/static/templates/auth-modal.html"
    ]
    
    for file_path in static_files:
        try:
            response = requests.get(f"{base_url}{file_path}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {file_path} - served successfully")
            else:
                print(f"❌ {file_path} - status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {file_path} - error: {e}")
    
    # Test 4: Check Firebase configuration
    print("\n4. Checking Firebase configuration...")
    
    # Check if Firebase service account file exists
    service_account_path = "firebase-service-account.json"
    if os.path.exists(service_account_path):
        print("✅ Firebase service account file found")
    else:
        print("❌ Firebase service account file missing")
        print("   Download it from Firebase Console > Project Settings > Service Accounts")
    
    # Check environment variables
    env_vars = [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_CLIENT_EMAIL",
        "JWT_SECRET_KEY"
    ]
    
    from dotenv import load_dotenv
    load_dotenv()
    
    for var in env_vars:
        if os.getenv(var):
            print(f"✅ {var} - configured")
        else:
            print(f"❌ {var} - missing")
    
    # Test 5: Test Firebase Auth module
    print("\n5. Testing Firebase Auth module...")
    
    try:
        from auth import FirebaseAuth
        auth_instance = FirebaseAuth()
        print("✅ Firebase Auth module imported successfully")
        
        # Test token verification with invalid token (should fail gracefully)
        try:
            result = auth_instance.verify_token("invalid-token")
            print("❌ Token verification should have failed")
        except Exception:
            print("✅ Token verification fails gracefully for invalid tokens")
            
    except ImportError as e:
        print(f"❌ Cannot import Firebase Auth module: {e}")
    except Exception as e:
        print(f"❌ Firebase Auth module error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("If you see mostly ✅ marks above, your Firebase authentication")
    print("integration is set up correctly!")
    print("\nTo complete the setup:")
    print("1. Configure your Firebase project")
    print("2. Download and place the service account JSON file")
    print("3. Update your .env file with Firebase credentials")
    print("4. Update static/js/firebase-config.js with your web app config")
    print("\nFor detailed instructions, see: firebase_config.md")
    
    return True

if __name__ == "__main__":
    test_firebase_auth_integration()
