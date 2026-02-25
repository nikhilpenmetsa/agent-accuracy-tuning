# Frontend Integration with AgentCore Memory & Session Backend

This document describes the frontend integration completed to support conversation persistence with AgentCore Memory and session management.

## Changes Made

### 1. Configuration (`config.json`)
Added Session API URL:
```json
{
  "SESSION_API_URL": "https://wyut1ctgc1.execute-api.us-east-1.amazonaws.com/prod"
}
```

### 2. New Module: `sessions.js`
Created a complete session management module with:

**SessionManager Class Methods:**
- `createSession(title)` - Create new conversation
- `listSessions()` - Get all user sessions
- `getSession(sessionId)` - Get specific session
- `updateSessionTitle(sessionId, newTitle)` - Update session title
- `deleteSession(sessionId)` - Delete a session
- `switchSession(sessionId)` - Switch to different conversation
- `getCurrentSession()` - Get or create current session
- `generateTitle(message)` - Auto-generate title from first message

### 3. Updated: `chat.js`
**Enhanced `sendMessage()` method:**
- Gets current session before sending message
- Includes `session_id` in agent payload
- Auto-updates session title after first message

**Enhanced `streamFromAgentCore()` method:**
- Retrieves current session via `sessionManager.getCurrentSession()`
- Passes `session_id` to agent for memory persistence
- Agent now maintains conversation history per session

### 4. Updated: `index.html`
**New UI Components:**
- Sessions sidebar with conversation list
- "New conversation" button
- Toggle sidebar button (mobile-friendly)
- Session items with title, date, and delete button
- Active session highlighting

**Layout Structure:**
```
chat-layout
├── sessions-sidebar
│   ├── sidebar-header (title + new button)
│   └── sessions-list (conversation items)
└── chat-container
    ├── chat-header (with toggle button)
    ├── messages-container
    └── input-container
```

### 5. Updated: `app.js`
**New Methods:**
- `setupSessionListeners()` - Event handlers for session UI
- `loadSessions()` - Load and display user sessions
- `renderSessions(sessions)` - Render session list
- `createNewSession()` - Create new conversation
- `switchToSession(sessionId)` - Switch between conversations
- `deleteSession(sessionId)` - Delete conversation with confirmation
- `toggleSidebar()` - Show/hide sessions sidebar
- `formatDate(dateString)` - Format relative timestamps

**Enhanced Methods:**
- `showChatScreen()` - Now loads sessions on login
- `handleLogout()` - Clears session manager state

### 6. Updated: `styles.css`
**New Styles:**
- `.chat-layout` - Flex layout for sidebar + chat
- `.sessions-sidebar` - Sidebar container with collapse animation
- `.session-item` - Individual conversation item
- `.session-delete-btn` - Delete button (shows on hover)
- Mobile responsive styles for sidebar

## How It Works

### Session Flow

1. **Login**
   - User authenticates with Cognito
   - App loads existing sessions from session-backend
   - Most recent session becomes active (or creates new one)

2. **Sending Messages**
   - User types message
   - `chat.sendMessage()` gets current session
   - Message sent to agent with `session_id`
   - Agent uses session_id for AgentCore Memory
   - After first message, session title auto-updates

3. **Session Management**
   - Click "New conversation" → Creates new session, clears chat
   - Click session item → Switches to that session, clears chat
   - Click delete (×) → Deletes session with confirmation
   - Toggle button → Show/hide sidebar (mobile-friendly)

### Memory Persistence

**Agent Side (already implemented):**
- Receives `session_id` in payload
- Extracts `user_id` from JWT token
- Configures AgentCore Memory with both IDs
- Retrieves from memory namespaces:
  - `/preferences/{user_id}` - User preferences
  - `/facts/{user_id}` - User facts
  - `/summaries/{user_id}/{session_id}` - Conversation summaries

**Frontend Side (now implemented):**
- Maintains current session state
- Passes `session_id` to agent
- Manages session list UI
- Auto-generates titles from first message

## Testing

### Manual Testing Steps

1. **Login** as any test user (john.doe@acme.com, jane.smith@acme.com, bob.johnson@acme.com)

2. **First Conversation**
   - Ask: "What is the PTO policy?"
   - Observe: Session title updates to "What is the PTO policy?"
   - Ask follow-up: "How many days do I get?"
   - Agent should remember context from previous message

3. **New Conversation**
   - Click "New conversation" button
   - Ask: "What are the benefits?"
   - Observe: New session created with new title

4. **Switch Sessions**
   - Click on first session in sidebar
   - Chat clears (UI limitation - no history loading yet)
   - Ask new question - uses original session_id

5. **Delete Session**
   - Hover over session item
   - Click × button
   - Confirm deletion
   - Session removed from list

## Known Limitations

1. **No Message History Loading**
   - When switching sessions, chat UI clears
   - Messages are persisted in AgentCore Memory
   - Agent can access history, but UI doesn't display it
   - Future enhancement: Load message history from memory

2. **Session Title Updates**
   - Only updates after first message
   - Manual title editing not implemented
   - Future enhancement: Click to edit title

3. **No Search/Filter**
   - Sessions list shows all conversations
   - No search or filter functionality
   - Future enhancement: Search sessions by title

## API Integration

### Session Backend API
- **Base URL**: `https://wyut1ctgc1.execute-api.us-east-1.amazonaws.com/prod`
- **Authentication**: Bearer token (Cognito ID token)

**Endpoints Used:**
- `POST /sessions` - Create session
- `GET /sessions` - List sessions
- `GET /sessions/{id}` - Get session
- `PUT /sessions/{id}` - Update session
- `DELETE /sessions/{id}` - Delete session

### Agent Endpoint
- **URL**: AgentCore Runtime endpoint
- **Authentication**: Bearer token (Cognito ID token)

**Payload Format:**
```json
{
  "prompt": "User message",
  "session_id": "20260224-abc123",
  "auth_token": "Bearer eyJ..."
}
```

## Files Modified

1. `frontend/config.json` - Added SESSION_API_URL
2. `frontend/sessions.js` - NEW - Session management module
3. `frontend/chat.js` - Added session_id to agent requests
4. `frontend/index.html` - Added session sidebar UI
5. `frontend/app.js` - Added session management logic
6. `frontend/styles.css` - Added session UI styles

## Next Steps

### Immediate
- Test with real users
- Monitor session creation/deletion
- Verify memory persistence across sessions

### Future Enhancements
1. **Message History Loading**
   - Fetch conversation history from AgentCore Memory
   - Display previous messages when switching sessions
   - Implement pagination for long conversations

2. **Session Management**
   - Edit session titles inline
   - Search/filter sessions
   - Archive old sessions
   - Export conversation history

3. **UI Improvements**
   - Session folders/categories
   - Favorite/pin sessions
   - Session sharing (if needed)
   - Keyboard shortcuts

4. **Performance**
   - Lazy load sessions
   - Cache session list
   - Optimize re-renders

## Deployment

The frontend is ready to deploy. No additional backend changes needed.

**Deployment Steps:**
1. Upload updated files to S3 bucket
2. Invalidate CloudFront cache
3. Test with real users

**Files to Deploy:**
- config.json
- sessions.js (new)
- chat.js
- index.html
- app.js
- styles.css

## Support

For issues or questions:
- Check browser console for errors
- Verify SESSION_API_URL is correct
- Ensure Cognito authentication is working
- Check CloudWatch logs for agent errors
