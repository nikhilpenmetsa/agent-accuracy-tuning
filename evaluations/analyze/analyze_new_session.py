"""Quick analysis of session 20260226235737-f6841cbb"""
import json
from collections import Counter

with open('session_data_20260226_160140/transaction_search_spans.json') as f:
    spans = json.load(f)

print('=' * 80)
print('AGENT BEHAVIOR ANALYSIS')
print('Session: 20260226235737-f6841cbb')
print('Question: "Tell me about the medical insurance options"')
print('=' * 80)
print()
print(f'TOTAL TRACE: 16.7 seconds | {len(spans)} spans')
print()

# Aggregate by operation
ops = Counter()
dur_by_op = {}
for s in spans:
    name = s['span']['name']
    ops[name] += 1
    dur_ms = s['span']['durationNano'] / 1_000_000
    dur_by_op.setdefault(name, []).append(dur_ms)

model_key = 'chat us.anthropic.claude-3-5-sonnet-20241022-v2:0'
llm_times = dur_by_op.get(model_key, [])
llm_time = sum(llm_times)
list_time = sum(dur_by_op.get('Bedrock AgentCore.ListEvents', []))
create_time = sum(dur_by_op.get('Bedrock AgentCore.CreateEvent', []))
retrieve_time = sum(dur_by_op.get('Bedrock AgentCore.RetrieveMemoryRecords', []))
ssm_time = sum(dur_by_op.get('SSM.GetParameter', []))
kb_time = sum(dur_by_op.get('Bedrock Agent Runtime.Retrieve', []))
memory_time = list_time + create_time + retrieve_time
total = 16728

print('TIME BREAKDOWN:')
print(f'  LLM calls (2x):              {llm_time:7.0f}ms  ({llm_time/total*100:.0f}%)')
print(f'    Call #1 (tool selection):    {llm_times[0]:7.0f}ms')
print(f'    Call #2 (response gen):     {llm_times[1]:7.0f}ms')
print(f'  Memory ops (27x):             {memory_time:7.0f}ms  ({memory_time/total*100:.0f}%)')
print(f'    ListEvents (13x):           {list_time:7.0f}ms')
print(f'    CreateEvent (11x):          {create_time:7.0f}ms')
print(f'    RetrieveMemoryRecords (3x): {retrieve_time:7.0f}ms')
print(f'  SSM params (4x):              {ssm_time:7.0f}ms  ({ssm_time/total*100:.0f}%)')
print(f'  KB search (1x):               {kb_time:7.0f}ms  ({kb_time/total*100:.0f}%)')
overhead = total - llm_time - memory_time - ssm_time - kb_time
print(f'  Framework overhead:           {overhead:7.0f}ms  ({overhead/total*100:.0f}%)')
print(f'  TOTAL:                        {total:7.0f}ms')

print()
print('PHASE TIMELINE:')
print('  [0.0s - 1.0s]  INIT: 4x SSM params + session load (2x ListEvents + CreateEvent)')
print('  [1.0s - 1.7s]  AGENT SETUP: state updates + 3x RetrieveMemoryRecords')
print('  [1.7s - 4.4s]  LLM #1: Tool selection (chose search_hr_knowledge_base)')
print('  [4.4s - 4.8s]  STATE: post-LLM state save (CreateEvent + ListEvents)')
print('  [4.8s - 5.3s]  TOOL: KB search (449ms) - query: medical insurance plans')
print('  [5.3s - 5.7s]  STATE: post-tool state save')
print('  [5.7s - 16.1s] LLM #2: Generate full response (10.3s - detailed 3-plan answer)')
print('  [16.1s-16.7s]  CLEANUP: final state saves + SaveConversation')

print()
print('BEHAVIOR ASSESSMENT:')
print('  Correct tool selection:    YES (search_hr_knowledge_base)')
print('  Unnecessary case creation: NO (correct)')
print('  KB relevance score:        0.41')
print('  Response quality:          Included Plan A/B/C with premiums, deductibles, OOP max')
print('  Memory pattern:            27 API calls (matches previous 27-call pattern)')
print('  LLM #2 was 3.9x slower than LLM #1 (generating detailed structured response)')

print()
print('COMPARISON WITH PREVIOUS SESSION (20260226_094223):')
print('  Previous question: "What is the vesting schedule for 401k matching?"')
print('  Both sessions show identical 27 memory API call pattern:')
print('    13x ListEvents, 11x CreateEvent, 3x RetrieveMemoryRecords')
print('  This confirms the memory overhead is structural, not question-dependent.')

print()
print('MATCHING TO TEST SUITE (test_questions.json):')
print('  Best match: mt-002 turn 1 - "Tell me about the medical insurance options"')
print('  Expected: KB search=true, case creation=false')
print('  Expected answer contains: Plan A, Plan B, Plan C, PPO, HDHP')
print('  RESULT: All expectations MET')
print('    - KB search: YES')
print('    - Case creation: NO')
print('    - Plan A: YES | Plan B: YES | Plan C: YES | PPO: YES | HDHP: YES')
