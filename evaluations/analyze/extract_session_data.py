#!/usr/bin/env python3
"""
Extract Session Data for Analysis

This script extracts:
1. Session metadata from DynamoDB
2. Session messages from AgentCore Memory
3. CloudWatch traces (OTEL data) for the agent execution
4. CloudWatch logs for the agent

Usage:
    python extract_session_data.py --ui-session 20260225184304-c338801e \
                                    --user-id d4e83478-60e1-7084-76a6-884f78d662a6 \
                                    --trace-id 699f47041e534f81661794b32b7df31d \
                                    --otel-session f26e44bf-a514-4218-8509-50712b7e7a23
"""

import argparse
import boto3
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class SessionDataExtractor:
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock_agentcore = boto3.client('bedrock-agentcore', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.xray = boto3.client('xray', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment and SSM"""
        # Get project name from config.env
        project_name = os.getenv('PROJECT_NAME', 'hr-assistant')
        
        # DynamoDB table name
        self.table_name = f"{project_name}-session-backend-stack-sessions"
        self.table = self.dynamodb.Table(self.table_name)
        
        # Get AgentCore Memory ID from SSM
        try:
            response = self.ssm.get_parameter(Name='/hr-assistant/AGENTCORE_MEMORY_ID')
            self.memory_id = response['Parameter']['Value']
        except Exception as e:
            print(f"Warning: Could not get memory_id from SSM: {e}")
            self.memory_id = None
        
        # CloudWatch log group for agent (will be determined dynamically)
        self.agent_log_group = None
        self._find_agent_log_group()
        
        print(f"Configuration loaded:")
        print(f"  Region: {self.region}")
        print(f"  DynamoDB Table: {self.table_name}")
        print(f"  Memory ID: {self.memory_id}")
        print(f"  Log Group: {self.agent_log_group}")
    
    def _find_agent_log_group(self):
        """Find the agent's log group dynamically"""
        try:
            # Try to find log group based on agent ID from SSM or env
            agent_id = os.getenv('AGENT_ID', 'askhragent-0L4quKFDp0')
            
            # Try the DEFAULT endpoint pattern
            log_group_name = f"/aws/bedrock-agentcore/runtimes/{agent_id}-DEFAULT"
            
            # Check if it exists
            response = self.logs.describe_log_groups(
                logGroupNamePrefix=log_group_name,
                limit=1
            )
            
            if response.get('logGroups'):
                self.agent_log_group = log_group_name
                return
            
            # Fallback: search for any log group with the agent ID
            response = self.logs.describe_log_groups(
                logGroupNamePrefix=f"/aws/bedrock-agentcore/runtimes/{agent_id}"
            )
            
            if response.get('logGroups'):
                self.agent_log_group = response['logGroups'][0]['logGroupName']
                return
            
            print(f"Warning: Could not find log group for agent {agent_id}")
            self.agent_log_group = None
            
        except Exception as e:
            print(f"Warning: Error finding log group: {e}")
            self.agent_log_group = None
    
    def extract_session_metadata(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Extract session metadata from DynamoDB"""
        print(f"\n=== Extracting Session Metadata ===")
        print(f"User ID: {user_id}")
        print(f"Session ID: {session_id}")
        
        try:
            response = self.table.get_item(
                Key={
                    'user_id': user_id,
                    'session_id': session_id
                }
            )
            
            if 'Item' in response:
                session = response['Item']
                print(f"✓ Found session: {session.get('title', 'Untitled')}")
                print(f"  Created: {session.get('created_at')}")
                print(f"  Updated: {session.get('updated_at')}")
                print(f"  Message Count: {session.get('message_count', 0)}")
                return session
            else:
                print("✗ Session not found in DynamoDB")
                return None
        except Exception as e:
            print(f"✗ Error extracting session metadata: {e}")
            return None
    
    def extract_session_messages(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """Extract session messages from AgentCore Memory"""
        print(f"\n=== Extracting Session Messages ===")
        
        if not self.memory_id:
            print("✗ Memory ID not available")
            return []
        
        try:
            response = self.bedrock_agentcore.list_events(
                memoryId=self.memory_id,
                actorId=user_id,
                sessionId=session_id,
                maxResults=100,  # Get more events for analysis
                includePayloads=True
            )
            
            events = response.get('events', [])
            print(f"✓ Retrieved {len(events)} events from AgentCore Memory")
            
            # Parse events into messages
            messages = []
            for idx, event_item in enumerate(reversed(events)):
                try:
                    payload_list = event_item.get('payload', [])
                    
                    if not payload_list:
                        continue
                    
                    for payload_item in payload_list:
                        if 'conversational' in payload_item:
                            conv = payload_item['conversational']
                            role = conv.get('role', '').lower()
                            content_obj = conv.get('content', '')
                            
                            # Extract content
                            if isinstance(content_obj, dict) and 'text' in content_obj:
                                content_str = content_obj['text']
                            elif isinstance(content_obj, str):
                                content_str = content_obj
                            else:
                                continue
                            
                            # Parse nested JSON
                            try:
                                message_data = json.loads(content_str)
                                actual_message = message_data.get('message', {})
                                content_array = actual_message.get('content', [])
                                
                                # Extract all content (text, toolUse, toolResult)
                                parsed_content = []
                                for item in content_array:
                                    if 'text' in item:
                                        parsed_content.append({
                                            'type': 'text',
                                            'text': item['text']
                                        })
                                    elif 'toolUse' in item:
                                        parsed_content.append({
                                            'type': 'toolUse',
                                            'toolUse': item['toolUse']
                                        })
                                    elif 'toolResult' in item:
                                        parsed_content.append({
                                            'type': 'toolResult',
                                            'toolResult': item['toolResult']
                                        })
                                
                                if parsed_content:
                                    messages.append({
                                        'role': role,
                                        'content': parsed_content,
                                        'timestamp': str(event_item.get('eventTimestamp')),
                                        'event_id': event_item.get('eventId')
                                    })
                            except json.JSONDecodeError:
                                # Plain text message
                                if content_str and role in ['user', 'assistant']:
                                    messages.append({
                                        'role': role,
                                        'content': [{'type': 'text', 'text': content_str}],
                                        'timestamp': str(event_item.get('eventTimestamp')),
                                        'event_id': event_item.get('eventId')
                                    })
                except Exception as e:
                    print(f"  Warning: Error parsing event {idx}: {e}")
                    continue
            
            print(f"✓ Parsed {len(messages)} messages")
            return messages
        except Exception as e:
            print(f"✗ Error extracting messages: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_cloudwatch_traces(self, trace_id: str, start_time: datetime = None, end_time: datetime = None) -> Dict[str, Any]:
        """Extract X-Ray traces from CloudWatch"""
        print(f"\n=== Extracting CloudWatch Traces ===")
        print(f"Trace ID: {trace_id}")
        
        # Default time range: last 24 hours
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        print(f"Time range: {start_time} to {end_time}")
        
        try:
            # Get trace by ID
            response = self.xray.batch_get_traces(
                TraceIds=[trace_id]
            )
            
            traces = response.get('Traces', [])
            if traces:
                trace = traces[0]
                print(f"✓ Found trace with {len(trace.get('Segments', []))} segments")
                
                # Parse segments
                parsed_segments = []
                for segment_doc in trace.get('Segments', []):
                    try:
                        segment = json.loads(segment_doc['Document'])
                        parsed_segments.append(segment)
                    except json.JSONDecodeError as e:
                        print(f"  Warning: Could not parse segment: {e}")
                
                return {
                    'trace_id': trace_id,
                    'duration': trace.get('Duration'),
                    'segments': parsed_segments
                }
            else:
                print("✗ Trace not found")
                return None
        except Exception as e:
            print(f"✗ Error extracting traces: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_cloudwatch_logs(self, session_id: str, start_time: datetime = None, end_time: datetime = None) -> List[Dict[str, Any]]:
        """Extract CloudWatch logs for the agent session"""
        print(f"\n=== Extracting CloudWatch Logs ===")
        
        if not self.agent_log_group:
            print("✗ Agent log group not found")
            return []
        
        print(f"Log Group: {self.agent_log_group}")
        print(f"Session ID: {session_id}")
        
        # Default time range: last 24 hours
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        print(f"Time range: {start_time} to {end_time}")
        
        try:
            # Query logs filtered by session ID
            query = f'fields @timestamp, @message | filter @message like /{session_id}/ | sort @timestamp asc'
            
            # Start query
            response = self.logs.start_query(
                logGroupName=self.agent_log_group,
                startTime=start_ms,
                endTime=end_ms,
                queryString=query
            )
            
            query_id = response['queryId']
            print(f"Started query: {query_id}")
            
            # Wait for query to complete
            import time
            max_wait = 30  # seconds
            waited = 0
            while waited < max_wait:
                result = self.logs.get_query_results(queryId=query_id)
                status = result['status']
                
                if status == 'Complete':
                    logs = result.get('results', [])
                    print(f"✓ Found {len(logs)} log entries")
                    
                    # Parse log entries
                    parsed_logs = []
                    for log_entry in logs:
                        log_dict = {}
                        for field in log_entry:
                            log_dict[field['field']] = field['value']
                        parsed_logs.append(log_dict)
                    
                    return parsed_logs
                elif status == 'Failed':
                    print(f"✗ Query failed")
                    return []
                
                time.sleep(1)
                waited += 1
            
            print(f"✗ Query timed out after {max_wait} seconds")
            return []
        except Exception as e:
            print(f"✗ Error extracting logs: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_transaction_search_spans(self, trace_id: str, start_time: datetime = None, end_time: datetime = None) -> List[Dict[str, Any]]:
        """Extract actual OTEL spans from CloudWatch Transaction Search"""
        print(f"\n=== Extracting Transaction Search Spans ===")
        
        spans_log_group = 'aws/spans'
        
        print(f"Log Group: {spans_log_group}")
        print(f"Trace ID: {trace_id}")
        
        # Default time range: last 24 hours
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        print(f"Time range: {start_time} to {end_time}")
        
        try:
            # Query for spans with this trace ID
            query = f'fields @timestamp, @message | filter traceId = "{trace_id}" | sort @timestamp asc | limit 100'
            
            # Start query
            response = self.logs.start_query(
                logGroupName=spans_log_group,
                startTime=start_ms,
                endTime=end_ms,
                queryString=query
            )
            
            query_id = response['queryId']
            print(f"Started query: {query_id}")
            
            # Wait for query to complete
            import time
            max_wait = 30
            waited = 0
            while waited < max_wait:
                result = self.logs.get_query_results(queryId=query_id)
                status = result['status']
                
                if status == 'Complete':
                    logs = result.get('results', [])
                    print(f"✓ Found {len(logs)} spans")
                    
                    # Parse span data
                    spans = []
                    for log_entry in logs:
                        log_dict = {}
                        for field in log_entry:
                            log_dict[field['field']] = field['value']
                        
                        # Parse JSON from message
                        message = log_dict.get('@message', '')
                        try:
                            if message.strip().startswith('{'):
                                span_data = json.loads(message)
                                spans.append({
                                    'timestamp': log_dict.get('@timestamp'),
                                    'span': span_data
                                })
                        except json.JSONDecodeError:
                            pass
                    
                    print(f"✓ Parsed {len(spans)} spans")
                    return spans
                elif status == 'Failed':
                    print(f"✗ Query failed")
                    return []
                
                time.sleep(1)
                waited += 1
            
            print(f"✗ Query timed out after {max_wait} seconds")
            return []
        except Exception as e:
            print(f"✗ Error extracting spans: {e}")
            return []
    
    def extract_otel_spans(self, ui_session_id: str, start_time: datetime = None, end_time: datetime = None) -> List[Dict[str, Any]]:
        """Extract OTEL spans from CloudWatch logs using UI session ID"""
        print(f"\n=== Extracting OTEL Spans ===")
        
        if not self.agent_log_group:
            print("✗ Agent log group not found")
            return []
        
        print(f"Log Group: {self.agent_log_group}")
        print(f"UI Session ID: {ui_session_id}")
        
        # Default time range: last 24 hours
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        print(f"Time range: {start_time} to {end_time}")
        
        try:
            # Query for OTEL span data using UI session ID (not OTEL session ID)
            query = f'''fields @timestamp, @message
                | filter @message like /{ui_session_id}/
                | sort @timestamp asc
                | limit 1000'''
            
            # Start query
            response = self.logs.start_query(
                logGroupName=self.agent_log_group,
                startTime=start_ms,
                endTime=end_ms,
                queryString=query
            )
            
            query_id = response['queryId']
            print(f"Started query: {query_id}")
            
            # Wait for query to complete
            import time
            max_wait = 30
            waited = 0
            while waited < max_wait:
                result = self.logs.get_query_results(queryId=query_id)
                status = result['status']
                
                if status == 'Complete':
                    logs = result.get('results', [])
                    print(f"✓ Found {len(logs)} OTEL log entries")
                    
                    # Parse log entries and extract span data
                    spans = []
                    for log_entry in logs:
                        log_dict = {}
                        for field in log_entry:
                            log_dict[field['field']] = field['value']
                        
                        # Try to parse JSON from message
                        message = log_dict.get('@message', '')
                        try:
                            if message.strip().startswith('{'):
                                span_data = json.loads(message)
                                
                                # Check if it's OTEL data (has traceId or spanId)
                                if 'traceId' in span_data or 'spanId' in span_data or 'otelTraceID' in span_data.get('attributes', {}):
                                    spans.append({
                                        'timestamp': log_dict.get('@timestamp'),
                                        'span_data': span_data
                                    })
                        except json.JSONDecodeError:
                            pass
                    
                    print(f"✓ Parsed {len(spans)} OTEL spans")
                    return spans
                elif status == 'Failed':
                    print(f"✗ Query failed")
                    return []
                
                time.sleep(1)
                waited += 1
            
            print(f"✗ Query timed out after {max_wait} seconds")
            return []
        except Exception as e:
            print(f"✗ Error extracting OTEL spans: {e}")
            import traceback
            traceback.print_exc()
            return []

    def extract_model_invocation_logs(self, start_time: datetime = None, end_time: datetime = None,
                                       identity_filter: str = 'BedrockAgentCore') -> List[Dict[str, Any]]:
        """Extract Bedrock model invocation logs from bedrock-access-log.
        
        These logs contain the full request/response payloads sent to/from the LLM,
        including the exact prompt composition (system prompt, user context from memory,
        user message, tool definitions) and the model's response.
        
        The logs are in the 'bedrock-access-log' log group in the same region as the agent.
        Invocations from AgentCore have an identity ARN containing 'BedrockAgentCore'.
        
        Args:
            start_time: Start of time window to search
            end_time: End of time window to search  
            identity_filter: Filter identity ARN (default: 'BedrockAgentCore' to match agent invocations)
            
        Returns:
            List of parsed invocation log entries with input/output details
        """
        print(f"\n=== Extracting Model Invocation Logs ===")
        
        log_group = 'bedrock-access-log'
        
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        print(f"Log Group: {log_group}")
        print(f"Identity filter: {identity_filter}")
        print(f"Time range: {start_time} to {end_time}")
        
        try:
            # Query invocation logs filtered by identity (AgentCore runtime)
            query = (
                f"fields @timestamp, @message"
                f" | filter identity.arn like /{identity_filter}/"
                f" | sort @timestamp asc"
            )
            
            response = self.logs.start_query(
                logGroupName=log_group,
                startTime=start_ms,
                endTime=end_ms,
                queryString=query
            )
            
            query_id = response['queryId']
            print(f"Started query: {query_id}")
            
            # Wait for query to complete
            import time
            max_wait = 30
            waited = 0
            while waited < max_wait:
                result = self.logs.get_query_results(queryId=query_id)
                status = result['status']
                
                if status == 'Complete':
                    raw_results = result.get('results', [])
                    print(f"✓ Found {len(raw_results)} invocation log entries")
                    
                    # Parse each invocation log
                    parsed = []
                    for entry in raw_results:
                        entry_dict = {}
                        for field in entry:
                            entry_dict[field['field']] = field['value']
                        
                        # Parse the JSON message
                        try:
                            log_data = json.loads(entry_dict.get('@message', '{}'))
                        except json.JSONDecodeError:
                            continue
                        
                        inp = log_data.get('input', {})
                        out = log_data.get('output', {})
                        inp_body = inp.get('inputBodyJson', {})
                        out_body = out.get('outputBodyJson', {})
                        
                        # Extract user_context from messages if present
                        user_context = None
                        user_message = None
                        messages = inp_body.get('messages', [])
                        for msg in messages:
                            if msg.get('role') == 'user':
                                for content_block in msg.get('content', []):
                                    text = content_block.get('text', '')
                                    if '<user_context>' in text:
                                        user_context = text
                                    elif text and not text.startswith('<'):
                                        user_message = text
                            # Also capture tool results in user messages
                        
                        # Extract tool use from output
                        tool_uses = []
                        out_message = out_body.get('output', {}).get('message', {})
                        for content_block in out_message.get('content', []):
                            if 'toolUse' in content_block:
                                tool_use = content_block['toolUse']
                                tool_uses.append({
                                    'name': tool_use.get('name'),
                                    'input': tool_use.get('input'),
                                    'toolUseId': tool_use.get('toolUseId')
                                })
                        
                        # Extract assistant text from output
                        assistant_text = None
                        for content_block in out_message.get('content', []):
                            if 'text' in content_block:
                                assistant_text = content_block['text']
                        
                        # Count tools in toolConfig
                        tool_count = len(inp_body.get('toolConfig', {}).get('tools', []))
                        tool_names = [
                            t.get('toolSpec', {}).get('name')
                            for t in inp_body.get('toolConfig', {}).get('tools', [])
                        ]
                        
                        parsed_entry = {
                            'timestamp': log_data.get('timestamp'),
                            'requestId': log_data.get('requestId'),
                            'modelId': log_data.get('modelId'),
                            'operation': log_data.get('operation'),
                            'inferenceRegion': log_data.get('inferenceRegion'),
                            'identity': log_data.get('identity', {}).get('arn'),
                            'input': {
                                'inputTokenCount': inp.get('inputTokenCount'),
                                'cacheReadInputTokenCount': inp.get('cacheReadInputTokenCount', 0),
                                'cacheWriteInputTokenCount': inp.get('cacheWriteInputTokenCount', 0),
                                'messageCount': len(messages),
                                'systemPromptLength': len(inp_body.get('system', [{}])[0].get('text', '')) if inp_body.get('system') else 0,
                                'toolCount': tool_count,
                                'toolNames': tool_names,
                                'temperature': inp_body.get('inferenceConfig', {}).get('temperature'),
                                'hasUserContext': user_context is not None,
                                'userContext': user_context,
                                'userMessage': user_message,
                            },
                            'output': {
                                'outputTokenCount': out.get('outputTokenCount'),
                                'stopReason': out_body.get('stopReason'),
                                'latencyMs': out_body.get('metrics', {}).get('latencyMs'),
                                'toolUses': tool_uses,
                                'assistantText': assistant_text,
                            },
                            # Keep full raw data for deep analysis
                            'raw': log_data
                        }
                        
                        parsed.append(parsed_entry)
                    
                    # Print summary
                    for i, p in enumerate(parsed):
                        stop = p['output']['stopReason']
                        in_tok = p['input']['inputTokenCount']
                        out_tok = p['output']['outputTokenCount']
                        latency = p['output']['latencyMs']
                        has_ctx = p['input']['hasUserContext']
                        tools = [t['name'] for t in p['output']['toolUses']]
                        print(f"  [{i+1}] {p['timestamp']} | {in_tok}→{out_tok} tokens | {latency}ms | stop={stop} | memory_ctx={has_ctx} | tools={tools}")
                    
                    return parsed
                    
                elif status == 'Failed':
                    print(f"✗ Query failed")
                    return []
                
                time.sleep(1)
                waited += 1
            
            print(f"✗ Query timed out after {max_wait} seconds")
            return []
            
        except Exception as e:
            print(f"✗ Error extracting model invocation logs: {e}")
            import traceback
            traceback.print_exc()
            return []

    def save_results(self, output_dir: str, data: Dict[str, Any]):
        """Save extracted data to JSON files"""
        print(f"\n=== Saving Results ===")
        print(f"Output directory: {output_dir}")
        
        # Ensure we use absolute path or relative to script location
        if not os.path.isabs(output_dir):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(script_dir, output_dir)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save each component
        for key, value in data.items():
            if value is not None:
                filename = os.path.join(output_dir, f"{key}.json")
                with open(filename, 'w') as f:
                    json.dump(value, f, indent=2, cls=DecimalEncoder)
                print(f"✓ Saved {filename}")
        
        # Save summary
        summary_file = os.path.join(output_dir, "summary.txt")
        with open(summary_file, 'w') as f:
            f.write("Session Data Extraction Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Extraction Time: {datetime.utcnow().isoformat()}\n\n")
            
            for key, value in data.items():
                if value is not None:
                    if isinstance(value, list):
                        f.write(f"{key}: {len(value)} items\n")
                    elif isinstance(value, dict):
                        f.write(f"{key}: {len(value)} keys\n")
                    else:
                        f.write(f"{key}: present\n")
                else:
                    f.write(f"{key}: not found\n")
        
        print(f"✓ Saved {summary_file}")
        print(f"\n✓ All data saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Extract session data for analysis')
    parser.add_argument('--ui-session', required=True, help='UI session ID (e.g., 20260225184304-c338801e)')
    parser.add_argument('--user-id', required=True, help='User ID (UUID)')
    parser.add_argument('--trace-id', help='CloudWatch X-Ray trace ID')
    parser.add_argument('--otel-session', help='OTEL session ID')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--output-dir', help='Output directory (default: evaluations/session_data_<timestamp>)')
    parser.add_argument('--hours', type=int, default=24, help='Hours to look back for logs/traces (default: 24)')
    
    args = parser.parse_args()
    
    # Create output directory
    if not args.output_dir:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output_dir = f"session_data_{timestamp}"
    
    # Initialize extractor
    extractor = SessionDataExtractor(region=args.region)
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=args.hours)
    
    # Extract all data
    data = {
        'session_metadata': extractor.extract_session_metadata(args.user_id, args.ui_session),
        'session_messages': extractor.extract_session_messages(args.user_id, args.ui_session),
    }
    
    # Extract traces if trace ID provided
    if args.trace_id:
        data['cloudwatch_traces'] = extractor.extract_cloudwatch_traces(args.trace_id, start_time, end_time)
    
    # Extract logs (using OTEL session if provided, otherwise UI session)
    log_session_id = args.otel_session if args.otel_session else args.ui_session
    data['cloudwatch_logs'] = extractor.extract_cloudwatch_logs(log_session_id, start_time, end_time)
    
    # Extract OTEL spans from CloudWatch logs (using UI session ID)
    data['otel_spans'] = extractor.extract_otel_spans(args.ui_session, start_time, end_time)
    
    # Extract actual spans from Transaction Search if trace ID provided
    if args.trace_id:
        data['transaction_search_spans'] = extractor.extract_transaction_search_spans(args.trace_id, start_time, end_time)
    
    # Extract model invocation logs (full LLM request/response payloads)
    # Use session metadata timestamps for a tight time window to avoid pulling
    # invocation logs from other sessions (invocation logs have no session ID field)
    session_meta = data.get('session_metadata')
    if session_meta and session_meta.get('created_at'):
        from dateutil import parser as dateparser
        try:
            session_created = dateparser.parse(session_meta['created_at'])
            session_updated = dateparser.parse(session_meta.get('updated_at', session_meta['created_at']))
            # Ensure UTC — session timestamps are stored as UTC
            if session_created.tzinfo is None:
                from datetime import timezone as tz
                session_created = session_created.replace(tzinfo=tz.utc)
                session_updated = session_updated.replace(tzinfo=tz.utc)
            # Add buffer: 1 minute before creation, 2 minutes after last update
            invocation_start = session_created - timedelta(minutes=1)
            invocation_end = session_updated + timedelta(minutes=2)
            print(f"\nUsing session timestamps for invocation log window: {invocation_start} to {invocation_end}")
        except Exception as e:
            print(f"\nCould not parse session timestamps ({e}), using full time range")
            invocation_start = start_time
            invocation_end = end_time
    else:
        invocation_start = start_time
        invocation_end = end_time
    
    data['model_invocation_logs'] = extractor.extract_model_invocation_logs(invocation_start, invocation_end)
    
    # Save results
    extractor.save_results(args.output_dir, data)
    
    print("\n" + "=" * 50)
    print("Extraction complete!")
    print(f"Data saved to: {args.output_dir}")
    print("=" * 50)


if __name__ == '__main__':
    main()
