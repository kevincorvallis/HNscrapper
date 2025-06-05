#!/bin/bash

# Firebase Authentication Setup Script for HN Enhanced Scraper
# This script helps set up Firebase authentication integration

echo "🔥 Firebase Authentication Setup for HN Enhanced Scraper"
echo "========================================================="
echo ""

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file - Please edit it with your Firebase configuration"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p static/js
mkdir -p static/css
mkdir -p static/templates
mkdir -p logs
mkdir -p data

echo ""
echo "🔧 NEXT STEPS:"
echo "=============="
echo ""
echo "1. FIREBASE SETUP:"
echo "   • Go to https://console.firebase.google.com/"
echo "   • Open your 'hnsummary-8edb0' project"
echo "   • Enable Authentication with these providers:"
echo "     - Email/Password"
echo "     - Google"
echo "     - Apple (optional)"
echo "     - Phone (optional)"
echo ""
echo "2. SERVICE ACCOUNT:"
echo "   • Go to Project Settings > Service Accounts"
echo "   • Click 'Generate new private key'"
echo "   • Download the JSON file as 'firebase-service-account.json'"
echo "   • Place it in the project root directory"
echo ""
echo "3. WEB APP CONFIG:"
echo "   • Go to Project Settings > General"
echo "   • Scroll to 'Your apps' section"
echo "   • Copy the Firebase configuration object"
echo "   • Update static/js/firebase-config.js with your config"
echo ""
echo "4. ENVIRONMENT VARIABLES:"
echo "   • Edit .env file with your Firebase service account details"
echo "   • Generate a secure JWT_SECRET_KEY"
echo ""
echo "5. START THE APPLICATION:"
echo "   • Run: python fastapi_enhanced_app.py"
echo "   • Open: http://localhost:8000"
echo ""
echo "📖 For detailed instructions, see: firebase_config.md"
echo ""
echo "🚀 Ready to authenticate users with Firebase!"
