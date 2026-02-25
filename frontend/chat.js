// Chat module with SSE streaming support
class Chat {
    constructor() {
        this.messages = [];
        this.isStreaming = false;
        this.currentStreamingMessage = null;
        this.abortController = null;
    }

    addMessage(role, content) {
        // Clear welcome message before adding first message
        if (this.messages.length === 0) {
            const messagesContainer = document.getElementById('messagesContainer');
            const welcomeMsg = messagesContainer.querySelector('.welcome-message');
            if (welcomeMsg) {
                welcomeMsg.remove();
            }
        }
        
        const message = {
            id: Date.now(),
            role, // 'user' or 'assistant'
            content,
            timestamp: new Date()
        };
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
        return message;
    }

    renderMessage(message) {
        const messagesContainer = document.getElementById('messagesContainer');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        messageDiv.dataset.messageId = message.id;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = message.role === 'user' ? '👤' : '🤖';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        // For user messages, use plain text
        // For assistant messages, render markdown
        if (message.role === 'user') {
            content.textContent = message.content;
        } else {
            content.innerHTML = this.renderMarkdown(message.content);
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        messagesContainer.appendChild(messageDiv);
    }

    updateStreamingMessage(content) {
        if (!this.currentStreamingMessage) return;
        
        const messageDiv = document.querySelector(
            `[data-message-id="${this.currentStreamingMessage.id}"]`
        );
        if (messageDiv) {
            const contentDiv = messageDiv.querySelector('.message-content');
            contentDiv.innerHTML = this.renderMarkdown(content);
            contentDiv.classList.add('streaming');
        }
        this.scrollToBottom();
    }

    finishStreaming() {
        if (!this.currentStreamingMessage) return;
        
        const messageDiv = document.querySelector(
            `[data-message-id="${this.currentStreamingMessage.id}"]`
        );
        if (messageDiv) {
            const contentDiv = messageDiv.querySelector('.message-content');
            contentDiv.classList.remove('streaming');
        }
        
        this.currentStreamingMessage = null;
        this.isStreaming = false;
    }

    renderMarkdown(text) {
        if (!text) return '';
        
        // Fix common spacing issues from LLM output
        // Add space after period if followed by capital letter
        text = text.replace(/\.([A-Z])/g, '. $1');
        // Add space after comma if followed by capital letter  
        text = text.replace(/,([A-Z])/g, ', $1');
        // Add space after colon if followed by capital letter or number
        text = text.replace(/:([A-Z0-9])/g, ': $1');
        
        // Escape HTML to prevent XSS
        let html = text.replace(/&/g, '&amp;')
                       .replace(/</g, '&lt;')
                       .replace(/>/g, '&gt;');
        
        // Code blocks first (before inline code): ```code```
        html = html.replace(/```([\s\S]+?)```/g, (match, code) => {
            return `<pre><code>${code.trim()}</code></pre>`;
        });
        
        // Inline code: `code`
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Bold: **text** or __text__
        html = html.replace(/\*\*([^\*]+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/__([^_]+?)__/g, '<strong>$1</strong>');
        
        // Italic: *text* or _text_ (but not in middle of words or numbers)
        html = html.replace(/(?<!\w)\*([^\*\n]+?)\*(?!\w)/g, '<em>$1</em>');
        html = html.replace(/(?<!\w)_([^_\n]+?)_(?!\w)/g, '<em>$1</em>');
        
        // Links: [text](url)
        html = html.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        
        // Process lists and paragraphs
        const lines = html.split('\n');
        const result = [];
        let inList = false;
        let listType = null;
        let currentParagraph = [];
        
        const flushParagraph = () => {
            if (currentParagraph.length > 0) {
                const text = currentParagraph.join('<br>').trim();
                if (text) {
                    result.push(`<p>${text}</p>`);
                }
                currentParagraph = [];
            }
        };
        
        const closeList = () => {
            if (inList) {
                result.push(`</${listType}>`);
                inList = false;
                listType = null;
            }
        };
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            // Empty line
            if (!line) {
                flushParagraph();
                closeList();
                continue;
            }
            
            // Check for list items
            const unorderedMatch = line.match(/^[\-\*\•]\s+(.+)$/);
            const orderedMatch = line.match(/^(\d+)\.\s+(.+)$/);
            
            if (unorderedMatch) {
                flushParagraph();
                if (!inList || listType !== 'ul') {
                    closeList();
                    result.push('<ul>');
                    inList = true;
                    listType = 'ul';
                }
                result.push(`<li>${unorderedMatch[1]}</li>`);
            } else if (orderedMatch) {
                flushParagraph();
                if (!inList || listType !== 'ol') {
                    closeList();
                    result.push('<ol>');
                    inList = true;
                    listType = 'ol';
                }
                result.push(`<li>${orderedMatch[2]}</li>`);
            } else if (line.startsWith('<pre>') || line.startsWith('</pre>')) {
                flushParagraph();
                closeList();
                result.push(line);
            } else {
                closeList();
                currentParagraph.push(line);
            }
        }
        
        flushParagraph();
        closeList();
        
        return result.join('');
    }

    async sendMessage(userMessage) {
        // Prevent duplicate calls
        if (this.isStreaming) {
            console.log('Already streaming, ignoring duplicate call');
            return;
        }
        
        // Add user message
        this.addMessage('user', userMessage);
        
        // Small delay to ensure unique timestamp for next message
        await new Promise(resolve => setTimeout(resolve, 1));
        
        // Start streaming response
        this.isStreaming = true;
        this.currentStreamingMessage = {
            id: Date.now(),
            role: 'assistant',
            content: '',
            timestamp: new Date()
        };
        this.messages.push(this.currentStreamingMessage);
        this.renderMessage(this.currentStreamingMessage);

        // Check if we have AgentCore endpoint configured
        if (CONFIG.AGENT_ENDPOINT) {
            await this.streamFromAgentCore(userMessage);
        } else {
            // Use mock streaming for now
            await this.mockStreamResponse(userMessage);
        }
        
        // After first message, update session title if it's still "New conversation"
        if (this.messages.filter(m => m.role === 'user').length === 1) {
            const session = await sessionManager.getCurrentSession();
            if (session && session.session_title === 'New conversation') {
                const newTitle = sessionManager.generateTitle(userMessage);
                await sessionManager.updateSessionTitle(session.session_id, newTitle);
                // Update UI
                if (window.updateSessionsList) {
                    window.updateSessionsList();
                }
            }
        }
    }

    async streamFromAgentCore(userMessage) {
        // Create abort controller for this request
        this.abortController = new AbortController();
        
        try {
            // Get current session
            const session = await sessionManager.getCurrentSession();
            
            // AgentCore deployed endpoint
            const response = await fetch(CONFIG.AGENT_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${auth.idToken}`
                },
                body: JSON.stringify({
                    prompt: userMessage,
                    session_id: session.session_id,  // Include session_id for memory
                    auth_token: `Bearer ${auth.idToken}`  // Also pass in payload for agent to use
                }),
                signal: this.abortController.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                
                // Keep the last incomplete line in the buffer
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            // Parse the JSON data after "data: "
                            const data = JSON.parse(line.slice(6));
                            if (typeof data === 'string') {
                                this.currentStreamingMessage.content += data;
                                this.updateStreamingMessage(this.currentStreamingMessage.content);
                            }
                        } catch (e) {
                            // If not JSON, treat as plain text
                            const text = line.slice(6);
                            this.currentStreamingMessage.content += text;
                            this.updateStreamingMessage(this.currentStreamingMessage.content);
                        }
                    }
                }
            }

            this.finishStreaming();
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Request aborted');
            } else {
                console.error('Streaming error:', error);
                this.currentStreamingMessage.content = 'Sorry, I encountered an error connecting to the agent. Please try again.';
                this.updateStreamingMessage(this.currentStreamingMessage.content);
            }
            this.finishStreaming();
        } finally {
            this.abortController = null;
        }
    }

    async mockStreamResponse(userMessage) {
        // Mock streaming response for testing
        const responses = [
            "Let me help you with that. ",
            "I'm checking our HR policies and knowledge base... ",
            "\n\nBased on the information I found:\n\n",
            "• ACME offers comprehensive benefits including health, dental, and vision insurance\n",
            "• You have 15 days of PTO per year, plus 10 company holidays\n",
            "• For time off requests, you can submit them through Workday\n",
            "\n\nWould you like me to create a case for you or provide more specific information?"
        ];

        for (const chunk of responses) {
            await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200));
            this.currentStreamingMessage.content += chunk;
            this.updateStreamingMessage(this.currentStreamingMessage.content);
        }

        this.finishStreaming();
    }

    scrollToBottom() {
        const container = document.getElementById('messagesContainer');
        container.scrollTop = container.scrollHeight;
    }

    clear() {
        this.messages = [];
        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <h3>Welcome to AskHR! 👋</h3>
                <p>I'm your HR assistant. I can help you with:</p>
                <ul>
                    <li>Company policies and benefits</li>
                    <li>Time off requests</li>
                    <li>Creating and tracking HR cases</li>
                    <li>General HR questions</li>
                </ul>
                <p>What can I help you with today?</p>
            </div>
        `;
    }

    async loadMessagesFromHistory(messages) {
        // Clear current messages
        this.messages = [];
        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.innerHTML = '';
        
        // Add each message from history
        for (const msg of messages) {
            const message = {
                id: Date.now() + Math.random(), // Unique ID
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date()
            };
            this.messages.push(message);
            this.renderMessage(message);
        }
        
        this.scrollToBottom();
    }

    showLoadingIndicator() {
        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.innerHTML = `
            <div class="loading-indicator">
                <div class="spinner"></div>
                <p>Loading conversation history...</p>
            </div>
        `;
    }

    showErrorMessage(message) {
        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.innerHTML = `
            <div class="error-message-box">
                <p>⚠️ ${message}</p>
                <p>Start a new conversation below.</p>
            </div>
        `;
    }
}

// Global chat instance
const chat = new Chat();
