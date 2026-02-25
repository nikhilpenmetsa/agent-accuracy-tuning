#!/usr/bin/env python3
"""
Directly query AgentCore Memory to see what's stored
"""
import json
import boto3

# Configuration
MEMORY_ID = "hr_assistant_memory-QzY4Jx5O7Z"
ACTOR_ID = "245874d8-5051-706e-f8ed-cd94ee41440d"  # Jane's UUID
SESSION_ID = "20260224233605-35f38f82"  # Jane's session
REGION = "us-east-1"

print("=" * 70)
print("Direct Memory Query")
print("=" * 70)
print(f"Memory ID: {MEMORY_ID}")
print(f"Actor ID: {ACTOR_ID}")
print(f"Session ID: {SESSION_ID}")
print()

# Use bedrock-agentcore client
client = boto3.client('bedrock-agentcore', region_name=REGION)

print("Calling list_events with includePayloads=True...")
print()

try:
    response = client.list_events(
        memoryId=MEMORY_ID,
        actorId=ACTOR_ID,
        sessionId=SESSION_ID,
        maxResults=20,
        includePayloads=True
    )
    
    events = response.get('events', [])
    print(f"✓ Retrieved {len(events)} events")
    print()
    
    if len(events) == 0:
        print("⚠️  No events found for this session!")
        print()
        print("Possible reasons:")
        print("1. Messages not yet persisted to memory")
        print("2. Wrong actor_id or session_id")
        print("3. Agent not using AgentCore Memory session manager")
        print()
        
        # Try listing all sessions for this actor
        print("Checking what sessions exist for this actor...")
        sessions_response = client.list_sessions(
            memoryId=MEMORY_ID,
            actorId=ACTOR_ID,
            maxResults=10
        )
        sessions = sessions_response.get('sessions', [])
        print(f"Found {len(sessions)} sessions for actor {ACTOR_ID}:")
        for s in sessions:
            print(f"  - {s.get('sessionId')}")
    else:
        print("=" * 70)
        print("Event Details:")
        print("=" * 70)
        
        for idx, event in enumerate(events[:5]):  # Show first 5
            print(f"\nEvent {idx}:")
            print(f"  Event ID: {event.get('eventId')}")
            print(f"  Type: {event.get('eventType')}")
            print(f"  Timestamp: {event.get('eventTimestamp')}")
            
            # Check for payload field (new format)
            payload = event.get('payload', [])
            if payload:
                print(f"  Payload items: {len(payload)}")
                for p_idx, p_item in enumerate(payload):
                    print(f"    Payload {p_idx}: {list(p_item.keys())}")
                    if 'Conversational' in p_item:
                        conv = p_item['Conversational']
                        print(f"      Role: {conv.get('role')}")
                        print(f"      Content: {conv.get('content', '')[:100]}...")
            else:
                print(f"  Payload: EMPTY")
            
            # Check for content field (old format)
            content = event.get('content', '{}')
            if len(content) > 2:
                print(f"  Content length: {len(content)}")
                print(f"  Content preview: {content[:200]}...")
            else:
                print(f"  Content: {content} (EMPTY!)")
        
        if len(events) > 5:
            print(f"\n... and {len(events) - 5} more events")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
