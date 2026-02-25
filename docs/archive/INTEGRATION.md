# Session Backend Integration Guide

Quick reference for integrating session-backend with agent and frontend.

## Agent Integration (agent-agentcore)

Add to `agent-agentcore/askhragent/src/main.py`:

```python
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

@app.entrypoint
async def invoke(payload, context):
    session_id = payload.get("session_id") or f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    user_id = extract_user_from_jwt(payload.get("auth_token"))
    memory_id = _get_ssm_parameter('/hr-assistant/AGENTCORE_MEMORY_ID')
    
    config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=session_id,
        actor_id=user_id,
        retrieval_config={
            "/preferences/{actorId}": RetrievalConfig(top_k=5, relevance_score=0.7),
            "/facts/{actorId}": RetrievalConfig(top_k=10, relevance_score=0.3),
            "/summaries/{actorId}/{sessionId}": RetrievalConfig(top_k=5, relevance_score=0.5)
        }
    )
    
    with AgentCoreMemorySessionManager(config, region_name="us-east-1") as session_manager:
        agent = Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=tools, session_manager=session_manager)
        stream = agent.stream_async(payload.get("prompt"))
        async for event in stream:
            if "data" in event and isinstance(event["data"], str):
                yield event["data"]
```

## Frontend Integration

### 1. Add Session API URL to `frontend/config.js`:
```javascript
const CONFIG = {
    // ... existing config ...
    SESSION_API_URL: 'https://wyut1ctgc1.execute-api.us-east-1.amazonaws.com/prod'
};
```

### 2. Create `frontend/sessions.js`:
```javascript
class SessionAPI {
    constructor(apiUrl, authToken) {
        this.apiUrl = apiUrl;
        this.authToken = authToken;
    }
    
    async createSession(title = "New conversation") {
        const response = await fetch(`${this.apiUrl}/sessions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_title: title })
        });
        return response.json();
    }
    
    async listSessions() {
        const response = await fetch(`${this.apiUrl}/sessions`, {
            headers: { 'Authorization': `Bearer ${this.authToken}` }
        });
        return response.json();
    }
    
    async deleteSession(sessionId) {
        const response = await fetch(`${this.apiUrl}/sessions/${sessionId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${this.authToken}` }
        });
        return response.json();
    }
}
```

### 3. Update `frontend/chat.js` to include session_id:
```javascript
async sendMessage(userMessage, sessionId) {
    const response = await fetch(CONFIG.AGENT_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${auth.idToken}`
        },
        body: JSON.stringify({
            prompt: userMessage,
            session_id: sessionId,  // Add this
            auth_token: `Bearer ${auth.idToken}`
        }),
        signal: this.abortController.signal
    });
    // ... rest of code
}
```

## Deployment Order

1. Deploy case-backend (for Cognito)
2. Run `bash session-backend/1-setup-memory.sh`
3. Deploy session-backend with `bash session-backend/2-deploy.sh`
4. Update agent-agentcore to use AgentCore Memory
5. Update frontend to use session API
