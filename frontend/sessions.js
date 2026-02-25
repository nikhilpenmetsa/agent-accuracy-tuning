// Session management module for AgentCore Memory integration
class SessionManager {
    constructor() {
        this.currentSession = null;
        this.sessions = [];
    }

    /**
     * Create a new session
     * @param {string} title - Session title (optional, defaults to "New conversation")
     * @returns {Promise<Object>} Created session object
     */
    async createSession(title = "New conversation") {
        try {
            const response = await fetch(`${CONFIG.SESSION_API_URL}/sessions`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${auth.idToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_title: title })
            });

            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.statusText}`);
            }

            const data = await response.json();
            const session = data.session;
            
            // Add to local sessions list
            this.sessions.unshift(session);
            this.currentSession = session;
            
            return session;
        } catch (error) {
            console.error('Error creating session:', error);
            throw error;
        }
    }

    /**
     * List all sessions for the current user
     * @returns {Promise<Array>} Array of session objects
     */
    async listSessions() {
        try {
            const response = await fetch(`${CONFIG.SESSION_API_URL}/sessions`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${auth.idToken}`
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to list sessions: ${response.statusText}`);
            }

            const data = await response.json();
            this.sessions = data.sessions || [];
            
            return this.sessions;
        } catch (error) {
            console.error('Error listing sessions:', error);
            throw error;
        }
    }

    /**
     * Get a specific session by ID
     * @param {string} sessionId - Session ID
     * @returns {Promise<Object>} Session object
     */
    async getSession(sessionId) {
        try {
            const response = await fetch(`${CONFIG.SESSION_API_URL}/sessions/${sessionId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${auth.idToken}`
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to get session: ${response.statusText}`);
            }

            const data = await response.json();
            return data.session;
        } catch (error) {
            console.error('Error getting session:', error);
            throw error;
        }
    }

    /**
     * Update session title
     * @param {string} sessionId - Session ID
     * @param {string} newTitle - New session title
     * @returns {Promise<Object>} Updated session object
     */
    async updateSessionTitle(sessionId, newTitle) {
        try {
            const response = await fetch(`${CONFIG.SESSION_API_URL}/sessions/${sessionId}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${auth.idToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_title: newTitle })
            });

            if (!response.ok) {
                throw new Error(`Failed to update session: ${response.statusText}`);
            }

            const data = await response.json();
            const updatedSession = data.session;
            
            // Update in local sessions list
            const index = this.sessions.findIndex(s => s.session_id === sessionId);
            if (index !== -1) {
                this.sessions[index] = updatedSession;
            }
            
            if (this.currentSession && this.currentSession.session_id === sessionId) {
                this.currentSession = updatedSession;
            }
            
            return updatedSession;
        } catch (error) {
            console.error('Error updating session:', error);
            throw error;
        }
    }

    /**
     * Delete a session
     * @param {string} sessionId - Session ID
     * @returns {Promise<void>}
     */
    async deleteSession(sessionId) {
        try {
            const response = await fetch(`${CONFIG.SESSION_API_URL}/sessions/${sessionId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${auth.idToken}`
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to delete session: ${response.statusText}`);
            }

            // Remove from local sessions list
            this.sessions = this.sessions.filter(s => s.session_id !== sessionId);
            
            // If this was the current session, clear it
            if (this.currentSession && this.currentSession.session_id === sessionId) {
                this.currentSession = null;
            }
        } catch (error) {
            console.error('Error deleting session:', error);
            throw error;
        }
    }

    /**
     * Switch to a different session
     * @param {string} sessionId - Session ID to switch to
     * @returns {Promise<Object>} Session object
     */
    async switchSession(sessionId) {
        const session = this.sessions.find(s => s.session_id === sessionId);
        if (session) {
            this.currentSession = session;
            return session;
        }
        
        // If not in local list, fetch from API
        const fetchedSession = await this.getSession(sessionId);
        this.currentSession = fetchedSession;
        return fetchedSession;
    }

    /**
     * Get current session, creating one if needed
     * @returns {Promise<Object>} Current session object
     */
    async getCurrentSession() {
        if (this.currentSession) {
            return this.currentSession;
        }

        // Try to get the most recent session
        await this.listSessions();
        if (this.sessions.length > 0) {
            this.currentSession = this.sessions[0];
            return this.currentSession;
        }

        // No sessions exist, create a new one
        return await this.createSession();
    }

    /**
     * Generate a title from the first user message
     * @param {string} message - First user message
     * @returns {string} Generated title
     */
    generateTitle(message) {
        // Take first 50 characters and add ellipsis if needed
        const maxLength = 50;
        if (message.length <= maxLength) {
            return message;
        }
        return message.substring(0, maxLength).trim() + '...';
    }

    /**
     * Get messages for a specific session from AgentCore Memory
     * @param {string} sessionId - Session ID
     * @returns {Promise<Array>} Array of message objects
     */
    async getSessionMessages(sessionId) {
        try {
            const response = await fetch(`${CONFIG.SESSION_API_URL}/sessions/${sessionId}/messages`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${auth.idToken}`
                }
            });

            if (!response.ok) {
                if (response.status === 404) {
                    // Session has no messages yet
                    return [];
                }
                throw new Error(`Failed to get messages: ${response.statusText}`);
            }

            const data = await response.json();
            return data.messages || [];
        } catch (error) {
            console.error('Error getting session messages:', error);
            // Return empty array on error - don't block UI
            return [];
        }
    }

    /**
     * Clear current session (for logout)
     */
    clear() {
        this.currentSession = null;
        this.sessions = [];
    }
}

// Global session manager instance
const sessionManager = new SessionManager();
