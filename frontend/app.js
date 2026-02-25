// Main application logic
class App {
    constructor() {
        this.loginScreen = document.getElementById('loginScreen');
        this.chatScreen = document.getElementById('chatScreen');
        this.sidebarOpen = true;
        this.init();
    }

    init() {
        // Check for existing session
        if (auth.restoreSession()) {
            this.showChatScreen();
        }

        // Setup event listeners
        this.setupLoginListeners();
        this.setupChatListeners();
        this.setupSessionListeners();
    }

    setupLoginListeners() {
        // Quick login buttons
        const quickLoginButtons = document.querySelectorAll('.quick-login-btn');
        quickLoginButtons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const email = e.target.dataset.email;
                const password = e.target.dataset.password;
                await this.handleLogin(email, password);
            });
        });

        // Hide quick login section if disabled
        if (!CONFIG.ENABLE_QUICK_LOGIN) {
            document.getElementById('quickLoginSection').style.display = 'none';
        }

        // Manual login form
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            await this.handleLogin(email, password);
        });
    }

    setupChatListeners() {
        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Send message
        document.getElementById('sendBtn').addEventListener('click', () => {
            this.sendMessage();
        });

        // Enter to send (Shift+Enter for new line)
        document.getElementById('messageInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        document.getElementById('messageInput').addEventListener('input', (e) => {
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
        });
    }

    setupSessionListeners() {
        // New session button
        document.getElementById('newSessionBtn').addEventListener('click', async () => {
            await this.createNewSession();
        });

        // Toggle sidebar button
        document.getElementById('toggleSidebarBtn').addEventListener('click', () => {
            this.toggleSidebar();
        });
    }

    async handleLogin(email, password) {
        const errorDiv = document.getElementById('loginError');
        errorDiv.textContent = '';

        try {
            await auth.login(email, password);
            this.showChatScreen();
        } catch (error) {
            errorDiv.textContent = error.message || 'Login failed. Please check your credentials.';
        }
    }

    handleLogout() {
        auth.logout();
        chat.clear();
        sessionManager.clear();
        this.showLoginScreen();
    }

    showLoginScreen() {
        this.loginScreen.classList.add('active');
        this.chatScreen.classList.remove('active');
        document.getElementById('email').value = '';
        document.getElementById('password').value = '';
        document.getElementById('loginError').textContent = '';
    }

    async showChatScreen() {
        this.loginScreen.classList.remove('active');
        this.chatScreen.classList.add('active');
        
        // Update user status
        const userName = auth.currentUser.email.split('@')[0].replace('.', ' ');
        document.getElementById('userStatus').textContent = 
            `Connected as ${userName}`;
        
        // Load sessions
        await this.loadSessions();
        
        // Focus on input
        document.getElementById('messageInput').focus();
    }

    async loadSessions() {
        const sessionsList = document.getElementById('sessionsList');
        sessionsList.innerHTML = '<div class="sessions-loading">Loading conversations...</div>';

        try {
            const sessions = await sessionManager.listSessions();
            this.renderSessions(sessions);
        } catch (error) {
            console.error('Error loading sessions:', error);
            sessionsList.innerHTML = '<div class="sessions-error">Failed to load conversations</div>';
        }
    }

    renderSessions(sessions) {
        const sessionsList = document.getElementById('sessionsList');
        
        if (sessions.length === 0) {
            sessionsList.innerHTML = '<div class="sessions-empty">No conversations yet</div>';
            return;
        }

        sessionsList.innerHTML = '';
        sessions.forEach(session => {
            const sessionItem = document.createElement('div');
            sessionItem.className = 'session-item';
            if (sessionManager.currentSession && sessionManager.currentSession.session_id === session.session_id) {
                sessionItem.classList.add('active');
            }

            const sessionTitle = document.createElement('div');
            sessionTitle.className = 'session-title';
            sessionTitle.textContent = session.session_title;
            sessionTitle.title = session.session_title;

            const sessionDate = document.createElement('div');
            sessionDate.className = 'session-date';
            sessionDate.textContent = this.formatDate(session.updated_at);

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'session-delete-btn';
            deleteBtn.innerHTML = '×';
            deleteBtn.title = 'Delete conversation';
            deleteBtn.onclick = async (e) => {
                e.stopPropagation();
                await this.deleteSession(session.session_id);
            };

            sessionItem.appendChild(sessionTitle);
            sessionItem.appendChild(sessionDate);
            sessionItem.appendChild(deleteBtn);

            sessionItem.onclick = () => this.switchToSession(session.session_id);

            sessionsList.appendChild(sessionItem);
        });
    }

    async createNewSession() {
        try {
            await sessionManager.createSession();
            chat.clear();
            await this.loadSessions();
        } catch (error) {
            console.error('Error creating session:', error);
            alert('Failed to create new conversation');
        }
    }

    async switchToSession(sessionId) {
        try {
            await sessionManager.switchSession(sessionId);
            
            // Show loading indicator
            chat.showLoadingIndicator();
            
            // Update UI to show active session
            this.renderSessions(sessionManager.sessions);
            
            // Load message history from AgentCore Memory
            try {
                const messages = await sessionManager.getSessionMessages(sessionId);
                
                if (messages.length > 0) {
                    await chat.loadMessagesFromHistory(messages);
                } else {
                    // No messages yet, show welcome
                    chat.clear();
                }
            } catch (error) {
                console.error('Error loading message history:', error);
                chat.showErrorMessage('Could not load conversation history');
            }
        } catch (error) {
            console.error('Error switching session:', error);
            alert('Failed to switch conversation');
        }
    }

    async deleteSession(sessionId) {
        if (!confirm('Delete this conversation?')) {
            return;
        }

        try {
            await sessionManager.deleteSession(sessionId);
            
            // If we deleted the current session, create a new one
            if (!sessionManager.currentSession) {
                await sessionManager.createSession();
                chat.clear();
            }
            
            await this.loadSessions();
        } catch (error) {
            console.error('Error deleting session:', error);
            alert('Failed to delete conversation');
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sessionsSidebar');
        this.sidebarOpen = !this.sidebarOpen;
        
        if (this.sidebarOpen) {
            sidebar.classList.remove('collapsed');
        } else {
            sidebar.classList.add('collapsed');
        }
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message || chat.isStreaming) return;

        // Clear input
        input.value = '';
        input.style.height = 'auto';

        // Disable send button during streaming
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = true;

        try {
            await chat.sendMessage(message);
        } finally {
            sendBtn.disabled = false;
            input.focus();
        }
    }
}

// Make updateSessionsList available globally for chat.js
window.updateSessionsList = async function() {
    if (window.appInstance) {
        await window.appInstance.loadSessions();
    }
};

// Initialize app when DOM is ready AND config is loaded
document.addEventListener('DOMContentLoaded', async () => {
    // Wait for config to load
    await window.configReady;
    window.appInstance = new App();
});
