# Firebase Configuration and Authentication

## Setup Instructions

### 1. Firebase Console Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `hnsummary-8edb0`
3. Navigate to Authentication > Sign-in method
4. Enable the following providers:
   - Email/Password
   - Google
   - Phone
   - Apple (requires Apple Developer account)

### 2. Service Account Setup
1. Go to Project Settings > Service accounts
2. Generate new private key
3. Download the JSON file
4. Save it as `firebase-service-account.json` in the project root
5. Add the file path to your `.env` file

### 3. Environment Variables
Add these to your `.env` file:
```
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
FIREBASE_PROJECT_ID=hnsummary-8edb0

# JWT Secret for session management
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Firebase Web App Config
FIREBASE_API_KEY=AIzaSyCfbBUpTH6XEgn2xdQNEuyfvjfW54_HCmM
FIREBASE_AUTH_DOMAIN=hnsummary-8edb0.firebaseapp.com
FIREBASE_PROJECT_ID=hnsummary-8edb0
FIREBASE_STORAGE_BUCKET=hnsummary-8edb0.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=572468292408
FIREBASE_APP_ID=1:572468292408:web:be595dcfec6affeb79afcd
FIREBASE_MEASUREMENT_ID=G-YG11QRPNHE
```

### 4. Security Notes
- Never commit `firebase-service-account.json` to version control
- Use strong JWT secret keys in production
- Configure CORS properly for your domain
- Enable Firebase Security Rules for Firestore if using database features

### 5. Authentication Flow
1. User signs in via Firebase Auth (frontend)
2. Firebase returns ID token
3. Frontend sends ID token to FastAPI backend
4. Backend verifies token with Firebase Admin SDK
5. Backend creates session JWT for subsequent requests
6. Protected routes verify JWT token

## Supported Authentication Methods
- ✅ Email/Password
- ✅ Google Sign-In
- ✅ Phone Number (SMS)
- ✅ Apple Sign-In
- ✅ Anonymous Sign-In (optional)
