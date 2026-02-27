# AgentCore Memory Behavior Analysis

## Summary of Findings

Based on trace analysis of session `20260226172511-6a2ef950` with 41 spans.

### Memory API Calls Per Single Question

For a single user question with 1 tool call:
- **13 ListEvents** calls
- **11 CreateEvent** calls  
- **3 RetrieveMemoryRecords** calls

Total: **27 memory API calls** for one question/answer cycle.

## Pre-Invoke Memory Operations (6 calls)

**Before `invoke_agent Strands Agents` span starts:**

### 1-2. ListEvents × 2 (Session Check)
- **When**: Session manager initialization (`with AgentCoreMemorySessionManager(...)`)
- **Why**: `read_session()` checks if session exists
  - First call: Check with metadata filter (STATE_TYPE=SESSION)
  - Second call: Fallback check for legacy session format
- **Code**: `session_manager.py` → `read_session()`

### 3. CreateEvent (Session Creation)
- **When**: After session check
- **Why**: `create_session()` saves session metadata to memory
- **Duration**: 0.281s (longest pre-invoke operation)
- **Code**: `session_manager.py` → `create_session()`

### 4-5. ListEvents × 2 (Agent Check)
- **When**: Agent object creation (`Agent(...)`)
- **Why**: `read_agent()` checks if agent "default" exists in session
  - First call: Check with metadata filter (STATE_TYPE=AGENT, AGENT_ID=default)
  - Second call: Fallback check for legacy agent format
- **Code**: `session_manager.py` → `read_agent()`

### 6. CreateEvent (Agent Creation)
- **When**: After agent check
- **Why**: `create_agent()` saves agent metadata to memory
- **Duration**: 0.148s
- **Code**: `session_manager.py` → `create_agent()` called from `initialize()`

**All 6 operations share the same parent span** - they're part of initialization before the agent starts processing.

## During Agent Processing

### CreateEvent Calls (5 more)
Each message/turn triggers `create_message()` → CreateEvent:
- User message
- Assistant thinking/tool decision
- Tool use
- Tool result  
- Assistant final response

With `batch_size=1`, each is sent immediately (no batching).

### ListEvents Calls (7 more)
- Called by `list_messages()` to retrieve conversation history
- May be called multiple times during agent event loop
- Used to maintain conversation context

### RetrieveMemoryRecords (3 calls)
One call per namespace in `retrieval_config`:
- `/preferences/{actorId}` - User preferences
- `/facts/{actorId}` - User facts
- `/summaries/{actorId}/{sessionId}` - Session summaries

These are semantic searches for LTM context injection.

## Why So Many Calls?

### Design Decisions
1. **Immutable Memory**: AgentCore Memory is append-only, so updates require new CreateEvent
2. **No Caching**: Session/agent existence checked on every invocation
3. **Batch Size = 1**: Every message sent immediately (no buffering)
4. **Legacy Compatibility**: Double ListEvents for new + legacy format checks

### Potential Optimizations
- Increase `batch_size` to reduce CreateEvent calls
- Cache session/agent existence checks
- Remove legacy format fallback checks if not needed

## Debug Logging Added

Updated `main.py` with detailed logging to show:
- When session manager context is entered (triggers read_session + create_session)
- When agent object is created (triggers read_agent + create_agent)
- When agent processing starts
- When memory is flushed on exit

Deploy and test to see these logs correlated with CloudWatch spans.

## Next Steps

1. Wait for new deployment logs to appear (~10 min)
2. Extract session: `debug-20260226121457-f2de1488`
3. Correlate debug logs with Transaction Search spans
4. Confirm the 6 pre-invoke operations match our analysis
