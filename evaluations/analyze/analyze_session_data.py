#!/usr/bin/env python3
"""
Analyze Extracted Session Data

This script provides interactive analysis of extracted session data:
- View conversation flow
- Analyze tool calls and their results
- Examine agent reasoning
- View timing and performance metrics
- Search for specific patterns

Usage:
    python analyze_session_data.py evaluations/session_data_20260225_184500
"""

import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict


class SessionAnalyzer:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.data = {}
        self.load_data()
    
    def load_data(self):
        """Load all JSON files from the data directory"""
        print(f"Loading data from {self.data_dir}...")
        
        json_files = ['session_metadata.json', 'session_messages.json', 
                      'cloudwatch_traces.json', 'cloudwatch_logs.json', 'otel_spans.json',
                      'model_invocation_logs.json']
        
        for filename in json_files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    key = filename.replace('.json', '')
                    self.data[key] = json.load(f)
                    print(f"  ✓ Loaded {filename}")
            else:
                print(f"  ✗ {filename} not found")
        
        print()
    
    def show_summary(self):
        """Display a summary of the session"""
        print("=" * 80)
        print("SESSION SUMMARY")
        print("=" * 80)
        
        # Session metadata
        if 'session_metadata' in self.data and self.data['session_metadata']:
            meta = self.data['session_metadata']
            print(f"\nSession ID: {meta.get('session_id')}")
            print(f"User ID: {meta.get('user_id')}")
            print(f"Title: {meta.get('title', 'Untitled')}")
            print(f"Created: {meta.get('created_at')}")
            print(f"Updated: {meta.get('updated_at')}")
            print(f"Message Count: {meta.get('message_count', 0)}")
        
        # Message statistics
        if 'session_messages' in self.data:
            messages = self.data['session_messages']
            user_msgs = [m for m in messages if m['role'] == 'user']
            assistant_msgs = [m for m in messages if m['role'] == 'assistant']
            
            print(f"\nMessages:")
            print(f"  Total: {len(messages)}")
            print(f"  User: {len(user_msgs)}")
            print(f"  Assistant: {len(assistant_msgs)}")
            
            # Count tool uses
            tool_uses = []
            for msg in assistant_msgs:
                for content in msg.get('content', []):
                    if content.get('type') == 'toolUse':
                        tool_uses.append(content['toolUse'])
            
            if tool_uses:
                print(f"  Tool Calls: {len(tool_uses)}")
                
                # Count by tool name
                tool_counts = defaultdict(int)
                for tool in tool_uses:
                    tool_counts[tool.get('name', 'unknown')] += 1
                
                print(f"\n  Tool Usage:")
                for tool_name, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"    {tool_name}: {count}")
        
        # OTEL span statistics
        if 'otel_spans' in self.data and self.data['otel_spans']:
            spans = self.data['otel_spans']
            print(f"\nOTEL Spans:")
            print(f"  Total: {len(spans)}")
            
            # Extract trace IDs
            trace_ids = set()
            for span in spans:
                span_data = span.get('span_data', {})
                if 'traceId' in span_data:
                    trace_ids.add(span_data['traceId'])
            
            if trace_ids:
                print(f"  Trace IDs: {', '.join(list(trace_ids)[:3])}")
            
            # Count memory operations from span bodies
            memory_ops = defaultdict(int)
            for span in spans:
                span_data = span.get('span_data', {})
                body = span_data.get('body', '')
                if 'Created session' in body or 'Created agent' in body:
                    memory_ops['CreateEvent'] += 1
                elif 'Retrieved' in body and 'memories' in body:
                    memory_ops['RetrieveMemoryRecords'] += 1
                elif 'Conversation saved' in body:
                    memory_ops['SaveConversation'] += 1
            
            if memory_ops:
                print(f"\n  Memory Operations (from logs):")
                for op, count in memory_ops.items():
                    print(f"    {op}: {count}")
        
        # Trace statistics
        if 'cloudwatch_traces' in self.data and self.data['cloudwatch_traces']:
            trace = self.data['cloudwatch_traces']
            print(f"\nTrace:")
            print(f"  Trace ID: {trace.get('trace_id')}")
            print(f"  Duration: {trace.get('duration')} seconds")
            print(f"  Segments: {len(trace.get('segments', []))}")
        
        # Log statistics
        if 'cloudwatch_logs' in self.data:
            logs = self.data['cloudwatch_logs']
            print(f"\nLogs:")
            print(f"  Entries: {len(logs)}")
        
        # Model invocation log statistics
        if 'model_invocation_logs' in self.data and self.data['model_invocation_logs']:
            invocations = self.data['model_invocation_logs']
            print(f"\nModel Invocations:")
            print(f"  Total LLM calls: {len(invocations)}")
            total_in = sum(i.get('input', {}).get('inputTokenCount', 0) for i in invocations)
            total_out = sum(i.get('output', {}).get('outputTokenCount', 0) for i in invocations)
            total_latency = sum(i.get('output', {}).get('latencyMs', 0) for i in invocations)
            print(f"  Total tokens: {total_in} input, {total_out} output ({total_in + total_out} total)")
            print(f"  Total LLM latency: {total_latency}ms")
            for idx, inv in enumerate(invocations):
                inp = inv.get('input', {})
                out = inv.get('output', {})
                in_tok = inp.get('inputTokenCount', 0)
                out_tok = out.get('outputTokenCount', 0)
                latency = out.get('latencyMs', 0)
                stop = out.get('stopReason', '?')
                has_ctx = inp.get('hasUserContext', False)
                tools = [t['name'] for t in out.get('toolUses', [])]
                print(f"  [{idx+1}] {in_tok}→{out_tok} tokens | {latency}ms | stop={stop} | memory_ctx={has_ctx} | tools={tools}")
        
        print("\n" + "=" * 80)
    
    def show_conversation(self, include_tools: bool = False):
        """Display the conversation flow"""
        print("\n" + "=" * 80)
        print("CONVERSATION FLOW")
        print("=" * 80 + "\n")
        
        if 'session_messages' not in self.data:
            print("No messages found")
            return
        
        messages = self.data['session_messages']
        
        for idx, msg in enumerate(messages, 1):
            role = msg['role'].upper()
            timestamp = msg.get('timestamp', 'N/A')
            
            print(f"[{idx}] {role} ({timestamp})")
            print("-" * 80)
            
            for content in msg.get('content', []):
                content_type = content.get('type')
                
                if content_type == 'text':
                    text = content.get('text', '')
                    # Truncate long text
                    if len(text) > 500 and not include_tools:
                        text = text[:500] + "... (truncated)"
                    print(text)
                
                elif content_type == 'toolUse' and include_tools:
                    tool = content.get('toolUse', {})
                    print(f"\n🔧 TOOL USE: {tool.get('name')}")
                    print(f"   Tool Use ID: {tool.get('toolUseId')}")
                    print(f"   Input: {json.dumps(tool.get('input', {}), indent=2)}")
                
                elif content_type == 'toolResult' and include_tools:
                    result = content.get('toolResult', {})
                    print(f"\n📊 TOOL RESULT: {result.get('toolUseId')}")
                    status = result.get('status', 'unknown')
                    print(f"   Status: {status}")
                    
                    # Show content
                    for result_content in result.get('content', []):
                        if 'text' in result_content:
                            result_text = result_content['text']
                            if len(result_text) > 300:
                                result_text = result_text[:300] + "... (truncated)"
                            print(f"   Result: {result_text}")
            
            print("\n")
    
    def show_tool_analysis(self):
        """Analyze tool usage patterns"""
        print("\n" + "=" * 80)
        print("TOOL USAGE ANALYSIS")
        print("=" * 80 + "\n")
        
        if 'session_messages' not in self.data:
            print("No messages found")
            return
        
        messages = self.data['session_messages']
        
        # Extract all tool uses and results
        tool_calls = []
        
        for msg_idx, msg in enumerate(messages):
            if msg['role'] != 'assistant':
                continue
            
            for content in msg.get('content', []):
                if content.get('type') == 'toolUse':
                    tool = content['toolUse']
                    tool_calls.append({
                        'message_idx': msg_idx,
                        'name': tool.get('name'),
                        'tool_use_id': tool.get('toolUseId'),
                        'input': tool.get('input', {}),
                        'result': None,
                        'status': None
                    })
        
        # Match results to tool uses
        for msg_idx, msg in enumerate(messages):
            if msg['role'] != 'user':
                continue
            
            for content in msg.get('content', []):
                if content.get('type') == 'toolResult':
                    result = content['toolResult']
                    tool_use_id = result.get('toolUseId')
                    
                    # Find matching tool call
                    for tool_call in tool_calls:
                        if tool_call['tool_use_id'] == tool_use_id:
                            tool_call['result'] = result.get('content', [])
                            tool_call['status'] = result.get('status')
                            break
        
        # Display analysis
        print(f"Total Tool Calls: {len(tool_calls)}\n")
        
        for idx, call in enumerate(tool_calls, 1):
            print(f"[{idx}] {call['name']}")
            print(f"    Tool Use ID: {call['tool_use_id']}")
            print(f"    Input: {json.dumps(call['input'], indent=6)}")
            print(f"    Status: {call['status'] or 'No result'}")
            
            if call['result']:
                for result_content in call['result']:
                    if 'text' in result_content:
                        result_text = result_content['text']
                        if len(result_text) > 200:
                            result_text = result_text[:200] + "... (truncated)"
                        print(f"    Result: {result_text}")
            
            print()
    
    def show_trace_details(self):
        """Display trace segment details"""
        print("\n" + "=" * 80)
        print("TRACE DETAILS")
        print("=" * 80 + "\n")
        
        if 'cloudwatch_traces' not in self.data or not self.data['cloudwatch_traces']:
            print("No trace data found")
            return
        
        trace = self.data['cloudwatch_traces']
        segments = trace.get('segments', [])
        
        print(f"Trace ID: {trace.get('trace_id')}")
        print(f"Total Duration: {trace.get('duration')} seconds")
        print(f"Segments: {len(segments)}\n")
        
        for idx, segment in enumerate(segments, 1):
            print(f"[{idx}] {segment.get('name', 'Unknown')}")
            print(f"    ID: {segment.get('id')}")
            print(f"    Start: {segment.get('start_time')}")
            print(f"    End: {segment.get('end_time')}")
            
            if 'subsegments' in segment:
                print(f"    Subsegments: {len(segment['subsegments'])}")
                for subseg in segment['subsegments'][:5]:  # Show first 5
                    print(f"      - {subseg.get('name')}")
            
            if 'annotations' in segment:
                print(f"    Annotations: {json.dumps(segment['annotations'], indent=6)}")
            
            print()
    
    def show_invocations(self):
        """Display detailed model invocation log analysis"""
        print("\n" + "=" * 80)
        print("MODEL INVOCATION LOGS")
        print("=" * 80 + "\n")
        
        if 'model_invocation_logs' not in self.data or not self.data['model_invocation_logs']:
            print("No model invocation logs found.")
            print("Ensure 'bedrock-access-log' log group exists and model invocation logging is enabled.")
            return
        
        invocations = self.data['model_invocation_logs']
        
        for idx, inv in enumerate(invocations):
            inp = inv.get('input', {})
            out = inv.get('output', {})
            
            print(f"--- LLM Call #{idx + 1} ---")
            print(f"  Timestamp:    {inv.get('timestamp')}")
            print(f"  Request ID:   {inv.get('requestId')}")
            print(f"  Model:        {inv.get('modelId')}")
            print(f"  Region:       {inv.get('inferenceRegion')}")
            print(f"  Operation:    {inv.get('operation')}")
            print(f"  Temperature:  {inp.get('temperature')}")
            
            print(f"\n  INPUT ({inp.get('inputTokenCount')} tokens):")
            print(f"    System prompt: {inp.get('systemPromptLength')} chars")
            print(f"    Messages:      {inp.get('messageCount')}")
            print(f"    Tools:         {inp.get('toolCount')} ({', '.join(inp.get('toolNames', []))})")
            print(f"    Cache read:    {inp.get('cacheReadInputTokenCount', 0)} tokens")
            print(f"    Cache write:   {inp.get('cacheWriteInputTokenCount', 0)} tokens")
            
            # Memory context
            if inp.get('hasUserContext'):
                ctx = inp.get('userContext', '')
                print(f"\n  MEMORY CONTEXT (injected as <user_context>):")
                # Show the context, truncated if long
                if len(ctx) > 500:
                    print(f"    {ctx[:500]}...")
                    print(f"    ... ({len(ctx)} chars total)")
                else:
                    print(f"    {ctx}")
            else:
                print(f"\n  MEMORY CONTEXT: None (no user_context block)")
            
            # User message
            if inp.get('userMessage'):
                print(f"\n  USER MESSAGE:")
                msg = inp['userMessage']
                if len(msg) > 300:
                    print(f"    {msg[:300]}...")
                else:
                    print(f"    {msg}")
            
            print(f"\n  OUTPUT ({out.get('outputTokenCount')} tokens):")
            print(f"    Stop reason: {out.get('stopReason')}")
            print(f"    Latency:     {out.get('latencyMs')}ms")
            
            # Tool uses
            if out.get('toolUses'):
                print(f"    Tool calls:")
                for tool in out['toolUses']:
                    print(f"      - {tool['name']}({json.dumps(tool.get('input', {}))})")
            
            # Assistant text
            if out.get('assistantText'):
                text = out['assistantText']
                print(f"    Assistant text:")
                if len(text) > 500:
                    print(f"      {text[:500]}...")
                    print(f"      ... ({len(text)} chars total)")
                else:
                    print(f"      {text}")
            
            print()
        
        # Summary
        total_in = sum(i.get('input', {}).get('inputTokenCount', 0) for i in invocations)
        total_out = sum(i.get('output', {}).get('outputTokenCount', 0) for i in invocations)
        total_latency = sum(i.get('output', {}).get('latencyMs', 0) for i in invocations)
        print(f"TOTALS: {len(invocations)} calls | {total_in}+{total_out}={total_in+total_out} tokens | {total_latency}ms LLM time")

    def search_logs(self, pattern: str):
        """Search logs for a specific pattern"""
        print(f"\n" + "=" * 80)
        print(f"LOG SEARCH: '{pattern}'")
        print("=" * 80 + "\n")
        
        if 'cloudwatch_logs' not in self.data:
            print("No log data found")
            return
        
        logs = self.data['cloudwatch_logs']
        matches = []
        
        for log in logs:
            message = log.get('@message', '')
            if pattern.lower() in message.lower():
                matches.append(log)
        
        print(f"Found {len(matches)} matching log entries\n")
        
        for idx, log in enumerate(matches, 1):
            timestamp = log.get('@timestamp', 'N/A')
            message = log.get('@message', '')
            
            print(f"[{idx}] {timestamp}")
            print(f"    {message[:500]}")
            if len(message) > 500:
                print("    ... (truncated)")
            print()
    
    def interactive_menu(self):
        """Interactive menu for analysis"""
        while True:
            print("\n" + "=" * 80)
            print("SESSION DATA ANALYZER")
            print("=" * 80)
            print("\n1. Show Summary")
            print("2. Show Conversation (text only)")
            print("3. Show Conversation (with tools)")
            print("4. Show Tool Analysis")
            print("5. Show Trace Details")
            print("6. Search Logs")
            print("7. Export Report")
            print("0. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                self.show_summary()
            elif choice == '2':
                self.show_conversation(include_tools=False)
            elif choice == '3':
                self.show_conversation(include_tools=True)
            elif choice == '4':
                self.show_tool_analysis()
            elif choice == '5':
                self.show_trace_details()
            elif choice == '6':
                pattern = input("Enter search pattern: ").strip()
                self.search_logs(pattern)
            elif choice == '7':
                self.export_report()
            elif choice == '0':
                print("\nGoodbye!")
                break
            else:
                print("\nInvalid option")
            
            input("\nPress Enter to continue...")
    
    def export_report(self):
        """Export a comprehensive analysis report"""
        output_file = os.path.join(self.data_dir, "analysis_report.txt")
        
        print(f"\nExporting report to {output_file}...")
        
        # Redirect print to file
        import sys
        original_stdout = sys.stdout
        
        with open(output_file, 'w', encoding='utf-8') as f:
            sys.stdout = f
            
            print("SESSION DATA ANALYSIS REPORT")
            print("=" * 80)
            print(f"Generated: {datetime.now().isoformat()}")
            print("=" * 80)
            
            self.show_summary()
            self.show_conversation(include_tools=True)
            self.show_tool_analysis()
            self.show_trace_details()
        
        sys.stdout = original_stdout
        
        print(f"✓ Report saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Analyze extracted session data')
    parser.add_argument('data_dir', help='Directory containing extracted session data')
    parser.add_argument('--summary', action='store_true', help='Show summary only')
    parser.add_argument('--conversation', action='store_true', help='Show conversation only')
    parser.add_argument('--tools', action='store_true', help='Show tool analysis only')
    parser.add_argument('--trace', action='store_true', help='Show trace details only')
    parser.add_argument('--search', help='Search logs for pattern')
    parser.add_argument('--invocations', action='store_true', help='Show model invocation log details')
    parser.add_argument('--export', action='store_true', help='Export full report')
    
    args = parser.parse_args()
    
    analyzer = SessionAnalyzer(args.data_dir)
    
    # If specific options provided, run those
    if args.summary:
        analyzer.show_summary()
    elif args.conversation:
        analyzer.show_conversation(include_tools=True)
    elif args.tools:
        analyzer.show_tool_analysis()
    elif args.trace:
        analyzer.show_trace_details()
    elif args.search:
        analyzer.search_logs(args.search)
    elif args.invocations:
        analyzer.show_invocations()
    elif args.export:
        analyzer.export_report()
    else:
        # Otherwise, run interactive menu
        analyzer.interactive_menu()


if __name__ == '__main__':
    main()
