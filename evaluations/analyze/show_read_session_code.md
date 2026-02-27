# read_session() Code Analysis

From the AgentCoreMemorySessionManager source code I fetched from GitHub:

```python
def read_session(self, session_id: str, **kwargs: Any) -> Optional[Session]:
    """Read session data.

    AgentCore Memory does not have a `get_session` method.
    Which is fine as AgentCore Memory is a managed service we therefore do not need to read/update
    the session data. We just return the session object.
    """
    if session_id != self.config.session_id:
        return None

    # 1. Try new approach (metadata filter)
    event_metadata = [
        EventMetadataFilter.build_expression(
            left_operand=LeftExpression.build(STATE_TYPE_KEY),
            operator=OperatorType.EQUALS_TO,
            right_operand=RightExpression.build(StateType.SESSION.value),
        )
    ]

    events = self.memory_client.list_events(          # ← ListEvents CALL #1
        memory_id=self.config.memory_id,
        actor_id=self.config.actor_id,
        session_id=session_id,
        event_metadata=event_metadata,
        max_results=1,
    )
    if events:
        session_data = json.loads(events[0].get("payload", {})[0].get("blob"))
        return Session.from_dict(session_data)

    # 2. Fallback: check for legacy event and migrate
    legacy_actor_id = f"{LEGACY_SESSION_PREFIX}{session_id}"
    events = self.memory_client.list_events(          # ← ListEvents CALL #2
        memory_id=self.config.memory_id,
        actor_id=legacy_actor_id,
        session_id=session_id,
        max_results=1,
    )
    if events:
        old_event = events[0]
        session_data = json.loads(old_event.get("payload", {})[0].get("blob"))
        session = Session.from_dict(session_data)
        # Migrate: create new event with metadata, delete old
        self.create_session(session)
        self.memory_client.gmdp_client.delete_event(...)
        logger.info("Migrated legacy session event for session: %s", session_id)
        return session

    return None
```

## Why 2 ListEvents?

1. **First ListEvents**: Check for session using new format (with metadata filter `STATE_TYPE=SESSION`)
2. **Second ListEvents**: Fallback check for legacy format (using `legacy_actor_id = "session_{session_id}"`)

This is for **backward compatibility** - older versions stored session data differently.

## Confirmed by Debug Logs

From the logs we just saw:
```
[48] 12:15:01.885 - INFO:bedrock_agentcore.memory.client:Retrieved total of 0 events
[49] 12:15:01.932 - INFO:bedrock_agentcore.memory.client:Retrieved total of 0 events
[50] 12:15:02.093 - INFO:...Created session: debug-20260226121457-f2de1488...
```

- **01.885** - First ListEvents (0 events found - new format doesn't exist)
- **01.932** - Second ListEvents (0 events found - legacy format doesn't exist)
- **02.093** - CreateEvent (create new session since neither format exists)

Both returned 0 events because this was a new session.

## Same Pattern for read_agent()

The `read_agent()` function has identical structure:
1. ListEvents with metadata filter (STATE_TYPE=AGENT, AGENT_ID=default)
2. ListEvents with legacy actor_id format

**Source:** Direct from the session_manager.py code I fetched from https://raw.githubusercontent.com/aws/bedrock-agentcore-sdk-python/main/src/bedrock_agentcore/memory/integrations/strands/session_manager.py

**Confidence: 100%** - This is directly from the source code.