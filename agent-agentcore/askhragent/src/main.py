"""
AskHR Agent - HR Assistant with Knowledge Base and Workday Integration
AgentCore-compatible version with Memory integration
"""
import os
import uuid
import json
import base64
import boto3
from datetime import datetime
from dotenv import load_dotenv
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from starlette.middleware.cors import CORSMiddleware
from strands import Agent
from strands.models.bedrock import BedrockModel
from tools import (
    initialize_tools,
    search_hr_knowledge_base,
    get_available_case_types,
    create_workday_case,
    list_my_cases
)

# Load environment variables (for local development)
load_dotenv()

app = BedrockAgentCoreApp()
log = app.logger

# Add CORS middleware - allow both local and CloudFront origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "https://*.cloudfront.net",  # Will be updated with specific CloudFront domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_ssm_parameter(parameter_name: str) -> str:
    """Retrieve a parameter from SSM Parameter Store."""
    try:
        ssm_client = boto3.client('ssm', region_name='us-east-1')
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        log.error(f"Failed to retrieve SSM parameter {parameter_name}: {str(e)}")
        # Fall back to environment variable
        return os.getenv(parameter_name.split('/')[-1])


def _extract_user_from_jwt(token: str) -> str:
    """
    Extract user_id (sub claim) from JWT token.
    
    Args:
        token: JWT token (with or without 'Bearer ' prefix)
    
    Returns:
        User ID from token's sub claim, or 'default-user' if extraction fails
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token and token.startswith('Bearer '):
            token = token[7:]
        
        # JWT tokens have 3 parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            log.warning("Invalid JWT token format")
            return 'default-user'
        
        # Decode the payload (second part)
        # Add padding if needed for base64 decoding
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded)
        
        # Extract sub claim (user ID)
        user_id = claims.get('sub') or claims.get('cognito:username') or 'default-user'
        log.info(f"Extracted user_id from JWT: {user_id}")
        return user_id
    
    except Exception as e:
        log.warning(f"Failed to extract user from JWT: {str(e)}")
        return 'default-user'

# System prompt for the HR assistant
SYSTEM_PROMPT = """You are AskHR, a helpful and knowledgeable HR assistant for employees at the company.

Your role is to:
1. Answer questions about HR policies, benefits, compensation, time off, and workplace guidelines
2. Help employees create and manage Workday cases for HR requests
3. Provide accurate information based on the company's HR knowledge base
4. Guide employees through HR processes in a friendly and professional manner

Guidelines:
- Always search the knowledge base first when answering policy or benefit questions
- Be concise but thorough in your responses
- If you're unsure about something, say so and offer to create a case for HR review
- When creating cases, ensure you capture all necessary details from the employee
- Maintain a professional yet approachable tone
- Protect employee privacy and handle sensitive information appropriately
- If a question is outside HR scope, politely redirect to the appropriate resource

Available tools:
- search_hr_knowledge_base: Search company HR policies and documentation
- get_available_case_types: Show what types of cases can be created
- create_workday_case: Create a new HR case in Workday
- list_my_cases: View the employee's existing cases

Remember: You're here to make HR processes easier and more accessible for employees."""


@app.entrypoint
async def invoke(payload, context):
    """AgentCore entrypoint for handling requests with Memory integration."""
    
    # Extract or generate session_id
    session_id = payload.get("session_id")
    if not session_id:
        session_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        log.info(f"Generated new session_id: {session_id}")
    else:
        log.info(f"Using provided session_id: {session_id}")
    
    # Extract JWT token from multiple possible sources
    auth_token = None
    
    # Try to get the token from the app's current request
    try:
        from starlette.requests import Request
        if hasattr(app, '_request') and app._request:
            request = app._request
            auth_header = request.headers.get('Authorization') or request.headers.get('authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]  # Remove 'Bearer ' prefix
                log.info("Extracted JWT token from Authorization header")
    except Exception as e:
        log.debug(f"Could not extract token from app request: {e}")
    
    # Try from context
    if not auth_token and hasattr(context, 'authorization'):
        auth_token = context.authorization
        if auth_token and auth_token.startswith('Bearer '):
            auth_token = auth_token[7:]
    
    # Try from payload
    if not auth_token:
        auth_token = payload.get("auth_token") or payload.get("authorization")
        if auth_token and auth_token.startswith('Bearer '):
            auth_token = auth_token[7:]
    
    # Extract user_id from JWT token or use provided user_id
    user_id = payload.get("user_id")
    if auth_token and not user_id:
        user_id = _extract_user_from_jwt(auth_token)
    elif not user_id:
        user_id = 'default-user'
    
    log.info(f"Request - user: {user_id}, session: {session_id}, has_token: {bool(auth_token)}")
    
    # Initialize tools with auth token and session_id
    if auth_token:
        # Ensure token has Bearer prefix for API calls
        if not auth_token.startswith('Bearer '):
            auth_token = f'Bearer {auth_token}'
        initialize_tools(auth_token, session_id)
    else:
        log.warning("No auth token provided, Case API calls may fail")
        initialize_tools(session_id=session_id)
    
    # Get configuration from SSM or environment
    try:
        model_id = _get_ssm_parameter('/hr-assistant/MODEL_ID')
    except Exception:
        model_id = os.getenv('MODEL_ID', 'us.anthropic.claude-3-5-sonnet-20241022-v2:0')
    
    try:
        memory_id = _get_ssm_parameter('/hr-assistant/AGENTCORE_MEMORY_ID')
    except Exception:
        memory_id = os.getenv('AGENTCORE_MEMORY_ID', 'hr_assistant_memory-QzY4Jx5O7Z')
    
    log.info(f"Using model: {model_id}, memory: {memory_id}")
    
    # Define tools list
    tools = [
        search_hr_knowledge_base,
        get_available_case_types,
        create_workday_case,
        list_my_cases
    ]
    
    # Initialize Bedrock model
    model = BedrockModel(
        model_id=model_id,
        temperature=0.3
    )
    
    # Configure AgentCore Memory
    memory_config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=session_id,
        actor_id=user_id,
        batch_size=1,  # Flush immediately (no batching)
        retrieval_config={
            # Retrieve user preferences (e.g., communication style, notification preferences)
            f"/preferences/{user_id}": RetrievalConfig(top_k=5, relevance_score=0.7),
            # Retrieve facts about the user (e.g., department, role, past requests)
            f"/facts/{user_id}": RetrievalConfig(top_k=10, relevance_score=0.3),
            # Retrieve conversation summaries for this session
            f"/summaries/{user_id}/{session_id}": RetrievalConfig(top_k=5, relevance_score=0.5)
        }
    )
    
    # Use context manager to ensure messages are flushed to memory
    with AgentCoreMemorySessionManager(memory_config, region_name="us-east-1") as session_manager:
        # Create agent with memory session manager
        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
            session_manager=session_manager
        )
        
        # Stream response
        stream = agent.stream_async(payload.get("prompt"))
        
        async for event in stream:
            # Handle text parts of the response
            if "data" in event and isinstance(event["data"], str):
                yield event["data"]
    
    # Memory is automatically flushed when exiting the context manager
    log.info(f"Conversation saved to memory - session: {session_id}, user: {user_id}")


if __name__ == "__main__":
    app.run()
