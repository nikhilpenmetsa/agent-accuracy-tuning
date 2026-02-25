#!/usr/bin/env python3
"""
Test script to see what AgentCore Memory returns
"""
import json
from bedrock_agentcore.memory import MemoryClient

# Configuration
MEMORY_ID = "hr_assistant_memory-QzY4Jx5O7Z"
ACTOR_ID = "4438f4c8-00a1-70ad-2378-d635d3ec1404"  # UUID from JWT sub claim
SESSION_ID = "test-20260224130627-67bf11fe"  # From our recent test
REGION = "us-east-1"

print("=" * 60)
print("AgentCore Memory Format Test")
print("=" * 60)
print(f"Memory ID: {MEMORY_ID}")
print(f"Actor ID: {ACTOR_ID}")
print(f"Session ID: {SESSION_ID}")
print()

# Initialize memory client
client = MemoryClient(region_name=REGION)

print("Retrieving last 10 conversation turns...")
print()

try:
    # Get last k turns
    turns = client.get_last_k_turns(
        memory_id=MEMORY_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        k=10
    )
    
    print(f"Retrieved {len(turns)} turns")
    print()
    print("=" * 60)
    print("RAW FORMAT:")
    print("=" * 60)
    print(json.dumps(turns, indent=2, default=str))
    print()
    
    if turns:
        print("=" * 60)
        print("STRUCTURE ANALYSIS:")
        print("=" * 60)
        print(f"Type: {type(turns)}")
        print(f"Number of turns: {len(turns)}")
        if len(turns) > 0:
            print(f"First turn type: {type(turns[0])}")
            print(f"First turn structure:")
            print(json.dumps(turns[0], indent=2, default=str))
            
            # Check if it has messages
            if isinstance(turns[0], list):
                print(f"\nFirst turn has {len(turns[0])} messages")
                if len(turns[0]) > 0:
                    print(f"First message structure:")
                    print(json.dumps(turns[0][0], indent=2, default=str))
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Test complete!")
print("=" * 60)
