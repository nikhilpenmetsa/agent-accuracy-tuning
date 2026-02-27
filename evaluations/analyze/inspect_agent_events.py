#!/usr/bin/env python3
"""
Inspect what's stored in agent CreateEvent calls
"""
import boto3
import json
import sys

# Configuration
memory_id = "hr_assistant_memory-QzY4Jx5O7Z"
actor_id = "04e814e8-b0b1-7066-6bbf-2342a39c8ece"  # From the debug logs
session_id = "debug-20260226121457-f2de1488"

bedrock_agentcore = boto3.client('bedrock-agentcore', region_name='us-east-1')

print(f"Querying AgentCore Memory:")
print(f"  Memory ID: {memory_id}")
print(f"  Actor ID: {actor_id}")
print(f"  Session ID: {session_id}")
print()

# List all events for this session
print("Fetching all events...")
response = bedrock_agentcore.list_events(
    memoryId=memory_id,
    actorId=actor_id,
    sessionId=session_id,
    maxResults=100,
    includePayloads=True
)

events = response.get('events', [])
print(f"Found {len(events)} events\n")

# Filter for agent events (they have metadata with STATE_TYPE=AGENT)
agent_events = []
session_events = []
message_events = []

for event in events:
    metadata = event.get('metadata', {})
    state_type = metadata.get('stateType', {}).get('stringValue')
    
    if state_type == 'AGENT':
        agent_events.append(event)
    elif state_type == 'SESSION':
        session_events.append(event)
    else:
        message_events.append(event)

print(f"Event breakdown:")
print(f"  Session events: {len(session_events)}")
print(f"  Agent events: {len(agent_events)}")
print(f"  Message events: {len(message_events)}")
print()

# Inspect agent events
if agent_events:
    print("="*80)
    print("AGENT EVENTS ANALYSIS")
    print("="*80)
    
    for i, event in enumerate(agent_events, 1):
        event_id = event.get('eventId')
        timestamp = event.get('eventTimestamp')
        
        print(f"\n[{i}] Agent Event: {event_id}")
        print(f"    Timestamp: {timestamp}")
        
        # Get the payload
        payload = event.get('payload', [])
        if payload:
            for p in payload:
                if 'blob' in p:
                    blob_data = json.loads(p['blob'])
                    
                    print(f"    Agent ID: {blob_data.get('agent_id')}")
                    print(f"    Created at: {blob_data.get('created_at')}")
                    print(f"    Updated at: {blob_data.get('updated_at')}")
                    
                    # Check if it has messages
                    messages = blob_data.get('messages', [])
                    print(f"    Messages: {len(messages)}")
                    
                    if messages:
                        print(f"    Message summary:")
                        for j, msg in enumerate(messages[:5], 1):
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', [])
                            content_types = [c.get('type', 'unknown') for c in content if isinstance(c, dict)]
                            print(f"      [{j}] {role}: {content_types}")
                        
                        if len(messages) > 5:
                            print(f"      ... and {len(messages) - 5} more messages")
                    
                    # Check state
                    state = blob_data.get('state')
                    if state:
                        print(f"    State: {type(state)} with {len(state) if isinstance(state, dict) else 'N/A'} keys")
                    
                    # Show size
                    blob_size = len(p['blob'])
                    print(f"    Blob size: {blob_size:,} bytes ({blob_size/1024:.1f} KB)")

# Show a sample message event for comparison
if message_events:
    print(f"\n{'='*80}")
    print("SAMPLE MESSAGE EVENT (for comparison)")
    print("="*80)
    
    event = message_events[0]
    print(f"\nEvent ID: {event.get('eventId')}")
    print(f"Timestamp: {event.get('eventTimestamp')}")
    
    payload = event.get('payload', [])
    if payload:
        for p in payload:
            if 'conversational' in p:
                conv = p['conversational']
                print(f"Type: Conversational message")
                print(f"Role: {conv.get('role')}")
                content = conv.get('content', {})
                if isinstance(content, dict):
                    print(f"Content type: {content.get('type', 'text')}")
