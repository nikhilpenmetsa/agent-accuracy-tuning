#!/usr/bin/env python3
import boto3

logs = boto3.client('logs', region_name='us-east-1')

log_group = "/aws/bedrock-agentcore/runtimes/askhragent-0L4quKFDp0-DEFAULT"
log_stream = "2026/02/26/[runtime-logs]ffa7d471-4eb3-405f-b9a2-0bc332545d22"

print(f"Fetching logs from: {log_group}")
print(f"Stream: {log_stream}\n")

response = logs.get_log_events(
    logGroupName=log_group,
    logStreamName=log_stream,
    limit=100
)

events = response.get('events', [])
print(f"Found {len(events)} log events\n")
print("="*80)

for event in events:
    message = event['message']
    # Filter for our debug markers
    if any(marker in message for marker in ['===', 'INVOKE', 'MEMORY', 'SESSION', 'AGENT', 'CREATING', 'ENTERING']):
        print(message)
