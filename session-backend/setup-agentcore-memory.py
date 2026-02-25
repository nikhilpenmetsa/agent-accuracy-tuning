#!/usr/bin/env python3
"""
Setup script for creating AgentCore Memory resource with LTM strategies.
Run this once before deploying the session-backend stack.
"""

import os
import sys
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../config.env')
load_dotenv('.env')

def create_agentcore_memory():
    """Create AgentCore Memory resource with LTM strategies."""
    
    region = os.getenv('AWS_REGION', 'us-east-1')
    project_name = os.getenv('PROJECT_NAME', 'hr-assistant')
    # Create simple memory name from project name
    memory_name = f"{project_name.replace('-', '_')}_memory"
    
    print("=" * 60)
    print("AgentCore Memory Setup")
    print("=" * 60)
    print(f"Region: {region}")
    print(f"Memory Name: {memory_name}")
    print()
    
    try:
        # Import AgentCore Memory client
        try:
            from bedrock_agentcore.memory import MemoryClient
        except ImportError:
            print("Error: bedrock-agentcore package not installed")
            print("Install with: pip install bedrock-agentcore")
            sys.exit(1)
        
        # Create memory client
        client = MemoryClient(region_name=region)
        
        print("Creating AgentCore Memory resource with LTM strategies...")
        print("This may take a few minutes...")
        print()
        
        # Create memory with all three LTM strategies
        memory = client.create_memory_and_wait(
            name=memory_name,
            description=f"Memory for {project_name} with conversation history and user preferences",
            strategies=[
                {
                    "summaryMemoryStrategy": {
                        "name": "SessionSummarizer",
                        "namespaces": ["/summaries/{actorId}/{sessionId}"]
                    }
                },
                {
                    "userPreferenceMemoryStrategy": {
                        "name": "PreferenceLearner",
                        "namespaces": ["/preferences/{actorId}"]
                    }
                },
                {
                    "semanticMemoryStrategy": {
                        "name": "FactExtractor",
                        "namespaces": ["/facts/{actorId}"]
                    }
                }
            ]
        )
        
        memory_id = memory.get('id')
        
        print("✓ AgentCore Memory created successfully!")
        print()
        print("=" * 60)
        print("Memory Details")
        print("=" * 60)
        print(f"Memory ID: {memory_id}")
        print(f"Memory Name: {memory.get('name')}")
        print(f"Status: {memory.get('status')}")
        print()
        
        # Store in SSM Parameter Store
        print("Storing Memory ID in SSM Parameter Store...")
        ssm_client = boto3.client('ssm', region_name=region)
        parameter_name = f'/{project_name}/AGENTCORE_MEMORY_ID'
        
        try:
            ssm_client.put_parameter(
                Name=parameter_name,
                Value=memory_id,
                Type='String',
                Overwrite=True,
                Description=f'AgentCore Memory ID for {project_name}'
            )
            print(f"✓ Stored in SSM: {parameter_name}")
        except Exception as e:
            print(f"Warning: Could not store in SSM: {e}")
        
        print()
        print("=" * 60)
        print("Next Steps")
        print("=" * 60)
        print("1. Copy the Memory ID above")
        print("2. Update your .env file:")
        print(f"   AGENTCORE_MEMORY_ID={memory_id}")
        print()
        print("3. Deploy the session-backend stack:")
        print("   bash deploy.sh")
        print()
        print("4. Update agent-agentcore to use AgentCore Memory")
        print("=" * 60)
        
        return memory_id
        
    except Exception as e:
        print(f"Error creating AgentCore Memory: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_agentcore_memory()
