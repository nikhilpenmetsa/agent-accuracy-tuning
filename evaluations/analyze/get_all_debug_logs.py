#!/usr/bin/env python3
import boto3

logs = boto3.client('logs', region_name='us-east-1')

log_group = "/aws/bedrock-agentcore/runtimes/askhragent-0L4quKFDp0-DEFAULT"
log_stream = "2026/02/26/[runtime-logs]ffa7d471-4eb3-405f-b9a2-0bc332545d22"

print(f"Fetching ALL logs from: {log_stream}\n")

response = logs.get_log_events(
    logGroupName=log_group,
    logStreamName=log_stream,
    limit=200
)

events = response.get('events', [])
print(f"Total events: {len(events)}\n")
print("="*80)
print("COMPLETE LOG TIMELINE")
print("="*80)

for i, event in enumerate(events, 1):
    message = event['message']
    timestamp = event['timestamp']
    
    # Parse timestamp
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp / 1000)
    time_str = dt.strftime('%H:%M:%S.%f')[:-3]
    
    print(f"[{i}] {time_str} - {message}")
