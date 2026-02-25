import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def handler(event, context):
    try:
        # Extract user info from Cognito authorizer
        claims = event['requestContext']['authorizer']['claims']
        user_id = claims.get('sub')  # Use UUID (sub claim)
        
        # Get session_id from path parameters
        session_id = event['pathParameters']['session_id']
        
        # Verify session belongs to user
        session_response = table.get_item(
            Key={
                'user_id': user_id,
                'session_id': session_id
            }
        )
        
        if 'Item' not in session_response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Session not found'})
            }
        
        # Get memory_id from SSM
        ssm = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        memory_id = ssm.get_parameter(Name='/hr-assistant/AGENTCORE_MEMORY_ID')['Parameter']['Value']
        
        print(f"Retrieving messages - memory_id: {memory_id}, actor_id: {user_id}, session_id: {session_id}")
        
        # Use bedrock-agentcore client (not bedrock-agent-runtime)
        bedrock_agentcore = boto3.client('bedrock-agentcore', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        
        # List events from AgentCore Memory
        response = bedrock_agentcore.list_events(
            memoryId=memory_id,
            actorId=user_id,
            sessionId=session_id,
            maxResults=20,  # Get last 20 events (~10 turns)
            includePayloads=True  # CRITICAL: Include message content!
        )
        
        print(f"ListEvents returned {len(response.get('events', []))} events")
        
        # Parse events into messages
        messages = []
        events = response.get('events', [])
        
        print(f"Parsing {len(events)} events...")
        
        # Events are returned newest first, reverse for chronological order
        for idx, event_item in enumerate(reversed(events)):
            try:
                # Check if event has payload (new format) or content (old format)
                payload_list = event_item.get('payload', [])
                
                if not payload_list:
                    # Try old format with content
                    content_str = event_item.get('content', '{}')
                    if len(content_str) > 2:
                        content_data = json.loads(content_str)
                        message_data = content_data.get('message', {})
                    else:
                        print(f"Event {idx}: No payload or content, skipping")
                        continue
                else:
                    # New format: payload is a list of payload items
                    print(f"Event {idx}: Has {len(payload_list)} payload items")
                    
                    for payload_item in payload_list:
                        # Check for conversational payload type (lowercase!)
                        if 'conversational' in payload_item:
                            conv = payload_item['conversational']
                            role = conv.get('role', '').lower()
                            content_obj = conv.get('content', '')
                            
                            # Content might be a dict with 'text' field or a string
                            if isinstance(content_obj, dict) and 'text' in content_obj:
                                content_str = content_obj['text']
                            elif isinstance(content_obj, str):
                                content_str = content_obj
                            else:
                                print(f"Event {idx}: Unknown content format: {type(content_obj)}")
                                continue
                            
                            # Parse the nested JSON to get the actual message
                            try:
                                message_data = json.loads(content_str)
                                actual_message = message_data.get('message', {})
                                content_array = actual_message.get('content', [])
                                
                                # Extract text parts only (skip toolUse/toolResult)
                                text_parts = []
                                for item in content_array:
                                    if 'text' in item:
                                        text_parts.append(item['text'])
                                
                                if text_parts:
                                    messages.append({
                                        'role': role,
                                        'content': '\n'.join(text_parts),
                                        'timestamp': str(event_item.get('eventTimestamp'))
                                    })
                                    print(f"Event {idx}: Added {role} message with {len(text_parts)} text parts")
                            except json.JSONDecodeError:
                                # If not JSON, use as-is
                                if content_str and role in ['user', 'assistant']:
                                    messages.append({
                                        'role': role,
                                        'content': content_str,
                                        'timestamp': str(event_item.get('eventTimestamp'))
                                    })
                                    print(f"Event {idx}: Added {role} message (plain text)")
                        elif 'blob' in payload_item:
                            print(f"Event {idx}: Skipping blob payload")
                    
                    continue  # Skip old format parsing if we found payload
                
                # Old format parsing (for backward compatibility)
                role = message_data.get('role', '').lower()
                content_array = message_data.get('content', [])
                text_parts = []
                
                for content_item in content_array:
                    if 'text' in content_item:
                        text_parts.append(content_item['text'])
                
                if text_parts and role in ['user', 'assistant']:
                    messages.append({
                        'role': role,
                        'content': '\n'.join(text_parts),
                        'timestamp': message_data.get('created_at')
                    })
                    print(f"Event {idx}: Added message (old format)")
            
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing event {idx}: {str(e)}")
                continue
        
        print(f"Final: {len(messages)} messages parsed")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'messages': messages,
                'count': len(messages)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Could not load conversation history',
                'details': str(e)
            })
        }
