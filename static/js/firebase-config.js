// Firebase client configuration
// This file should be served as static content and contains only public Firebase config

const firebaseConfig = {
  apiKey: "your-firebase-api-key",
  authDomain: "hnsummary-8edb0.firebaseapp.com",
  projectId: "hnsummary-8edb0",
  storageBucket: "hnsummary-8edb0.appspot.com",
  messagingSenderId: "your-messaging-sender-id",
  appId: "your-app-id",
  measurementId: "your-measurement-id"
};

// Export for use in firebase-auth.js
window.firebaseConfig = firebaseConfig;
