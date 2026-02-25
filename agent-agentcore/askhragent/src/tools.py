"""
Tools for the AskHR agent to interact with Workday API and Knowledge Base.
"""
import json
import boto3
import requests
import logging
from typing import Dict
from strands import tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global configuration - set by initialize_tools()
_API_URL = None
_AUTH_TOKEN = None
_KB_ID = None
_REGION = None
_SESSION_ID = None  # Add session_id to global config


def _get_ssm_parameter(parameter_name: str) -> str:
    """
    Retrieve a parameter from SSM Parameter Store.
    
    Args:
        parameter_name: Full parameter name (e.g., '/hr-assistant/KB_ID')
    
    Returns:
        Parameter value
    """
    try:
        ssm_client = boto3.client('ssm', region_name='us-east-1')
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Failed to retrieve SSM parameter {parameter_name}: {str(e)}")
        raise


def initialize_tools(auth_token: str = None, session_id: str = None):
    """
    Initialize tool configuration from SSM Parameter Store.
    Must be called before using tools.
    
    Args:
        auth_token: Optional Cognito ID token for API authentication
        session_id: Optional session ID for tracking conversation context
    
    Reads from SSM Parameter Store:
        - /hr-assistant/CASE_API_URL: Case Backend API Gateway URL
        - /hr-assistant/KB_ID: Bedrock Knowledge Base ID
    """
    import os
    global _API_URL, _AUTH_TOKEN, _KB_ID, _REGION, _SESSION_ID
    
    # Try SSM first, fall back to environment variables for local development
    try:
        _API_URL = _get_ssm_parameter('/hr-assistant/CASE_API_URL')
        _KB_ID = _get_ssm_parameter('/hr-assistant/KB_ID')
        logger.info("Configuration loaded from SSM Parameter Store")
    except Exception as e:
        logger.warning(f"Failed to load from SSM, falling back to environment variables: {str(e)}")
        _API_URL = os.getenv('CASE_API_URL')
        _KB_ID = os.getenv('KB_ID')
    
    # Region from environment or default
    _REGION = os.getenv('AWS_REGION', 'us-east-1')
    _AUTH_TOKEN = auth_token or os.getenv('AUTH_TOKEN')
    _SESSION_ID = session_id  # Store session_id for use in tools
    
    # Validate required configuration
    if not _API_URL:
        raise ValueError("CASE_API_URL is required")
    if not _KB_ID:
        raise ValueError("KB_ID is required")
    
    _API_URL = _API_URL.rstrip('/')
    
    logger.info(f"Tools initialized - API: {_API_URL}, KB: {_KB_ID}, Auth: {'Yes' if _AUTH_TOKEN else 'No'}, Session: {_SESSION_ID or 'None'}")


def _get_api_headers() -> Dict[str, str]:
    """Get headers for API requests."""
    headers = {'Content-Type': 'application/json'}
    if _AUTH_TOKEN:
        headers['Authorization'] = _AUTH_TOKEN
    return headers


@tool
def search_hr_knowledge_base(query: str) -> str:
    """
    Search the HR Knowledge Base for company policies, benefits, procedures, and guidelines.
    Use this tool to answer questions about HR policies, benefits, time off, compensation, 
    workplace guidelines, and other HR-related topics.
    
    Args:
        query: The question or topic to search for in the knowledge base
    
    Returns:
        Relevant information from the HR knowledge base
    """
    try:
        logger.info(f"Searching KB for: {query}")
        client = boto3.client('bedrock-agent-runtime', region_name=_REGION)
        
        response = client.retrieve(
            knowledgeBaseId=_KB_ID,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        results = []
        for item in response.get('retrievalResults', []):
            content = item.get('content', {}).get('text', '')
            score = item.get('score', 0)
            results.append(f"[Relevance: {score:.2f}]\n{content}")
        
        if not results:
            logger.warning("No results found in KB")
            return "No relevant information found in the knowledge base."
        
        logger.info(f"Found {len(results)} results from KB")
        return "\n\n---\n\n".join(results)
    
    except Exception as e:
        error_msg = f"Error searching knowledge base: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"I encountered an error searching the knowledge base: {str(e)}"


@tool
def get_available_case_types() -> str:
    """
    Get the list of available case types that can be created in Workday.
    Use this to show users what types of cases they can create.
    
    Returns:
        JSON string with available case types and their descriptions
    """
    try:
        logger.info(f"Fetching case types from: {_API_URL}/case-types")
        response = requests.get(
            f'{_API_URL}/case-types',
            headers=_get_api_headers(),
            timeout=10
        )
        
        logger.info(f"Case types API response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Case types API error: {response.status_code} - {response.text}")
            return f"Error fetching case types: API returned status {response.status_code}"
        
        response.raise_for_status()
        case_types = response.json()['case_types']
        logger.info(f"Retrieved {len(case_types)} case types")
        return json.dumps(case_types, indent=2)
    
    except requests.exceptions.Timeout:
        error_msg = "Request to case types API timed out"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Could not connect to case API at {_API_URL}"
        logger.error(f"{error_msg}: {str(e)}")
        return f"Error: {error_msg}. Please check if the API is running."
    except Exception as e:
        error_msg = f"Error fetching case types: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@tool
def create_workday_case(case_type: str, description: str) -> str:
    """
    Create a new case in Workday for the user.
    Use this when a user wants to submit an HR request, report an issue, or create a case.
    
    Args:
        case_type: The type of case (e.g., 'pto', 'benefits', 'compensation', 'general')
        description: Detailed description of the case or request
    
    Returns:
        Confirmation message with case details
    """
    try:
        payload = {'case_type': case_type, 'description': description}
        
        # Add session_id if available
        if _SESSION_ID:
            payload['session_id'] = _SESSION_ID
            logger.info(f"Creating case with session_id: {_SESSION_ID}")
        
        logger.info(f"Creating case: {case_type} - {description[:50]}...")
        logger.debug(f"API URL: {_API_URL}/cases")
        logger.debug(f"Payload: {json.dumps(payload)}")
        
        response = requests.post(
            f'{_API_URL}/cases',
            headers=_get_api_headers(),
            json=payload,
            timeout=10
        )
        
        logger.info(f"Create case API response status: {response.status_code}")
        
        if response.status_code not in [200, 201]:
            logger.error(f"Create case API error: {response.status_code} - {response.text}")
            return f"Error creating case: API returned status {response.status_code}. Response: {response.text}"
        
        result = response.json()
        logger.info(f"Case created successfully: {result.get('case', {}).get('case_id', 'unknown')}")
        return json.dumps(result, indent=2)
    
    except requests.exceptions.Timeout:
        error_msg = "Request to create case timed out"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Could not connect to case API at {_API_URL}"
        logger.error(f"{error_msg}: {str(e)}")
        return f"Error: {error_msg}. Please check if the API is running."
    except Exception as e:
        error_msg = f"Error creating case: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@tool
def list_my_cases() -> str:
    """
    List all cases created by the current user in Workday.
    Use this when a user wants to see their existing cases or check case status.
    
    Returns:
        JSON string with list of user's cases
    """
    try:
        logger.info(f"Fetching user cases from: {_API_URL}/cases")
        response = requests.get(
            f'{_API_URL}/cases',
            headers=_get_api_headers(),
            timeout=10
        )
        
        logger.info(f"List cases API response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"List cases API error: {response.status_code} - {response.text}")
            return f"Error fetching cases: API returned status {response.status_code}"
        
        response.raise_for_status()
        cases = response.json()['cases']
        
        if not cases:
            logger.info("User has no cases")
            return "You have no cases in the system."
        
        logger.info(f"Retrieved {len(cases)} cases for user")
        return json.dumps(cases, indent=2)
    
    except requests.exceptions.Timeout:
        error_msg = "Request to list cases timed out"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Could not connect to case API at {_API_URL}"
        logger.error(f"{error_msg}: {str(e)}")
        return f"Error: {error_msg}. Please check if the API is running."
    except Exception as e:
        error_msg = f"Error listing cases: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg
