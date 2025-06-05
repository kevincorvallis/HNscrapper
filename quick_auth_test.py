#!/usr/bin/env python3
"""
Quick Firebase Authentication Integration Test
"""

import sys
import os
import subprocess
import time
import requests
from pathlib import Path

def test_authentication_setup():
    """Test the Firebase authentication setup"""
    print("🔥 Firebase Authentication Integration Test")
    print("=" * 50)
    
    # Test 1: Check if required files exist
    print("\n1. Checking required files...")
    
    required_files = [
        "auth.py",
        "fastapi_enhanced_app.py",
        "static/js/firebase-auth.js",
        "static/js/firebase-config.js", 
        "static/css/auth.css",
        "static/templates/auth-modal.html",
        "templates/index.html"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
    
    # Test 2: Check dependencies
    print("\n2. Testing Python dependencies...")
    
    try:
        import fastapi
        print("✅ FastAPI available")
    except ImportError:
        print("❌ FastAPI not available")
    
    try:
        import firebase_admin
        print("✅ firebase_admin available")
    except ImportError:
        print("❌ firebase_admin not available - run: pip install firebase-admin")
    
    try:
        from jose import jwt
        print("✅ python-jose available")
    except ImportError:
        print("❌ python-jose not available - run: pip install python-jose[cryptography]")
    
    try:
        from passlib.context import CryptContext
        print("✅ passlib available")
    except ImportError:
        print("❌ passlib not available - run: pip install passlib[bcrypt]")
    
    # Test 3: Try to import auth module
    print("\n3. Testing auth module...")
    
    try:
        sys.path.insert(0, os.getcwd())
        import auth
        print("✅ Auth module imports successfully")
        
        # Test FirebaseAuth class
        try:
            auth_instance = auth.FirebaseAuth()
            print("✅ FirebaseAuth class instantiated")
        except Exception as e:
            print(f"⚠️  FirebaseAuth instantiation issue: {e}")
            print("   (This is expected without proper Firebase credentials)")
        
    except ImportError as e:
        print(f"❌ Auth module import failed: {e}")
    except Exception as e:
        print(f"❌ Auth module error: {e}")
    
    # Test 4: Check environment setup
    print("\n4. Checking environment setup...")
    
    if os.path.exists(".env"):
        print("✅ .env file exists")
    else:
        print("❌ .env file missing - copy from .env.example")
    
    if os.path.exists("firebase-service-account.json"):
        print("✅ Firebase service account file exists")
    else:
        print("❌ Firebase service account file missing")
        print("   Download from Firebase Console > Project Settings > Service Accounts")
    
    # Test 5: Try starting FastAPI app
    print("\n5. Testing FastAPI application...")
    
    try:
        # Import the app to see if it loads
        import fastapi_enhanced_app
        print("✅ FastAPI app module loads successfully")
    except Exception as e:
        print(f"❌ FastAPI app module error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Setup Status Summary:")
    print("If you see mostly ✅ marks above, your setup is ready!")
    print("\nNext steps:")
    print("1. Configure Firebase project settings")
    print("2. Download service account JSON file")
    print("3. Update .env with your credentials")
    print("4. Update static/js/firebase-config.js")
    print("5. Run: python fastapi_enhanced_app.py")
    print("\nFor detailed setup instructions, see: firebase_config.md")
    
if __name__ == "__main__":
    test_authentication_setup()
