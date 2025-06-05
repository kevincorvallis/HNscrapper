// Firebase Authentication Client
// Handles all Firebase authentication on the frontend

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCfbBUpTH6XEgn2xdQNEuyfvjfW54_HCmM",
    authDomain: "hnsummary-8edb0.firebaseapp.com",
    projectId: "hnsummary-8edb0",
    storageBucket: "hnsummary-8edb0.firebasestorage.app",
    messagingSenderId: "572468292408",
    appId: "1:572468292408:web:be595dcfec6affeb79afcd",
    measurementId: "G-YG11QRPNHE"
};

// Initialize Firebase
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.0/firebase-app.js';
import { 
    getAuth, 
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    signInWithPopup,
    GoogleAuthProvider,
    signInWithPhoneNumber,
    RecaptchaVerifier,
    OAuthProvider,
    signOut,
    onAuthStateChanged 
} from 'https://www.gstatic.com/firebasejs/10.7.0/firebase-auth.js';
import { getAnalytics } from 'https://www.gstatic.com/firebasejs/10.7.0/firebase-analytics.js';

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const analytics = getAnalytics(app);

// Auth providers
const googleProvider = new GoogleAuthProvider();
const appleProvider = new OAuthProvider('apple.com');

// Configure Apple provider
appleProvider.addScope('email');
appleProvider.addScope('name');

// Configure Google provider
googleProvider.addScope('email');
googleProvider.addScope('profile');

class FirebaseAuthClient {
    constructor() {
        this.auth = auth;
        this.currentUser = null;
        this.accessToken = localStorage.getItem('accessToken');
        this.setupAuthStateListener();
    }

    setupAuthStateListener() {
        onAuthStateChanged(this.auth, async (user) => {
            if (user) {
                console.log('User signed in:', user);
                this.currentUser = user;
                
                // Get Firebase ID token and exchange for backend session token
                try {
                    const idToken = await user.getIdToken();
                    await this.exchangeFirebaseToken(idToken);
                } catch (error) {
                    console.error('Error getting ID token:', error);
                }
            } else {
                console.log('User signed out');
                this.currentUser = null;
                this.accessToken = null;
                localStorage.removeItem('accessToken');
                this.updateUI();
            }
        });
    }

    async exchangeFirebaseToken(firebaseToken) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    firebase_token: firebaseToken
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.accessToken = data.access_token;
                localStorage.setItem('accessToken', this.accessToken);
                console.log('Backend session created successfully');
                this.updateUI();
            } else {
                console.error('Failed to create backend session');
            }
        } catch (error) {
            console.error('Error exchanging Firebase token:', error);
        }
    }

    // Email/Password Authentication
    async signUpWithEmail(email, password) {
        try {
            const userCredential = await createUserWithEmailAndPassword(this.auth, email, password);
            return { success: true, user: userCredential.user };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async signInWithEmail(email, password) {
        try {
            const userCredential = await signInWithEmailAndPassword(this.auth, email, password);
            return { success: true, user: userCredential.user };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Google Authentication
    async signInWithGoogle() {
        try {
            const result = await signInWithPopup(this.auth, googleProvider);
            return { success: true, user: result.user };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Apple Authentication
    async signInWithApple() {
        try {
            const result = await signInWithPopup(this.auth, appleProvider);
            return { success: true, user: result.user };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Phone Authentication
    async setupPhoneAuth(phoneNumber, recaptchaContainerId) {
        try {
            if (!window.recaptchaVerifier) {
                window.recaptchaVerifier = new RecaptchaVerifier(this.auth, recaptchaContainerId, {
                    'size': 'normal',
                    'callback': (response) => {
                        console.log('reCAPTCHA solved');
                    }
                });
            }

            const confirmationResult = await signInWithPhoneNumber(this.auth, phoneNumber, window.recaptchaVerifier);
            return { success: true, confirmationResult };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async verifyPhoneCode(confirmationResult, code) {
        try {
            const result = await confirmationResult.confirm(code);
            return { success: true, user: result.user };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Sign Out
    async signOut() {
        try {
            // Sign out from Firebase
            await signOut(this.auth);
            
            // Call backend logout
            if (this.accessToken) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.accessToken}`
                    }
                });
            }
            
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get authenticated API headers
    getAuthHeaders() {
        return this.accessToken ? {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
        } : {
            'Content-Type': 'application/json'
        };
    }

    // Make authenticated API calls
    async authenticatedFetch(url, options = {}) {
        const headers = {
            ...this.getAuthHeaders(),
            ...options.headers
        };

        return fetch(url, {
            ...options,
            headers
        });
    }

    // UI Update Methods
    updateUI() {
        const isAuthenticated = this.currentUser && this.accessToken;
        
        // Update auth buttons
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        const userInfo = document.getElementById('userInfo');
        
        if (loginBtn) loginBtn.style.display = isAuthenticated ? 'none' : 'block';
        if (logoutBtn) logoutBtn.style.display = isAuthenticated ? 'block' : 'none';
        
        if (userInfo && isAuthenticated) {
            userInfo.innerHTML = `
                <div class="user-profile">
                    <img src="${this.currentUser.photoURL || '/static/default-avatar.png'}" 
                         alt="Profile" class="profile-pic">
                    <span class="user-name">${this.currentUser.displayName || this.currentUser.email}</span>
                </div>
            `;
        } else if (userInfo) {
            userInfo.innerHTML = '';
        }

        // Show/hide protected content
        const protectedElements = document.querySelectorAll('.protected-content');
        protectedElements.forEach(el => {
            el.style.display = isAuthenticated ? 'block' : 'none';
        });
    }

    // Get current user info
    getCurrentUser() {
        return this.currentUser;
    }

    isAuthenticated() {
        return this.currentUser && this.accessToken;
    }
}

// Initialize auth client
const authClient = new FirebaseAuthClient();

// Export for global use
window.authClient = authClient;

export default authClient;
