// Authentication module using AWS Cognito
class Auth {
    constructor() {
        this.currentUser = null;
        this.idToken = null;
        this.accessToken = null;
    }

    async login(email, password) {
        try {
            // Check if Cognito is configured
            if (!CONFIG.COGNITO_CLIENT_ID || !CONFIG.COGNITO_USER_POOL_ID) {
                console.log('Cognito not configured, using mock auth for local development');
                return this.mockLogin(email, password);
            }

            // Use AWS Cognito Identity Provider API
            const authData = {
                AuthFlow: 'USER_PASSWORD_AUTH',
                ClientId: CONFIG.COGNITO_CLIENT_ID,
                AuthParameters: {
                    USERNAME: email,
                    PASSWORD: password
                }
            };

            const response = await fetch(
                `https://cognito-idp.${CONFIG.AWS_REGION}.amazonaws.com/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-amz-json-1.1',
                        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
                    },
                    body: JSON.stringify(authData)
                }
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Login failed');
            }

            const data = await response.json();
            
            this.idToken = data.AuthenticationResult.IdToken;
            this.accessToken = data.AuthenticationResult.AccessToken;
            
            // Decode ID token to get user info
            const payload = JSON.parse(atob(this.idToken.split('.')[1]));
            this.currentUser = {
                email: payload.email,
                sub: payload.sub
            };

            // Store in sessionStorage
            sessionStorage.setItem('idToken', this.idToken);
            sessionStorage.setItem('accessToken', this.accessToken);
            sessionStorage.setItem('userEmail', this.currentUser.email);

            return this.currentUser;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    mockLogin(email, password) {
        // Mock authentication for local development
        const validUser = CONFIG.MOCK_USERS.find(u => u.email === email && u.password === password);
        
        if (!validUser) {
            throw new Error('Invalid credentials');
        }

        // Create mock tokens
        this.idToken = 'mock-id-token';
        this.accessToken = 'mock-access-token';
        this.currentUser = {
            email: validUser.email,
            sub: 'mock-sub-' + Date.now()
        };

        // Store in sessionStorage
        sessionStorage.setItem('idToken', this.idToken);
        sessionStorage.setItem('accessToken', this.accessToken);
        sessionStorage.setItem('userEmail', this.currentUser.email);

        return this.currentUser;
    }

    logout() {
        this.currentUser = null;
        this.idToken = null;
        this.accessToken = null;
        sessionStorage.clear();
    }

    isAuthenticated() {
        return !!this.idToken;
    }

    getAuthHeader() {
        return this.idToken ? { 'Authorization': this.idToken } : {};
    }

    restoreSession() {
        const idToken = sessionStorage.getItem('idToken');
        const userEmail = sessionStorage.getItem('userEmail');
        
        if (idToken && userEmail) {
            this.idToken = idToken;
            this.accessToken = sessionStorage.getItem('accessToken');
            this.currentUser = { email: userEmail };
            return true;
        }
        return false;
    }
}

// Global auth instance
const auth = new Auth();
