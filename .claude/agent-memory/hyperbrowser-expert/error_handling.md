# Error Handling

## Retry Pattern for Session Creation

```python
import asyncio
from hyperbrowser import AsyncHyperbrowser
from hyperbrowser.models import CreateSessionParams, ScreenConfig

async def create_session_with_retry(client, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"[INFO] Attempt {attempt + 1}: creating session")
            session = await client.sessions.create(params=params)
            print(f"[SUCCESS] Session created: {session.id}")
            return session
        except Exception as e:
            print(f"[ERROR] Failed: {e}")
            if attempt < max_retries - 1:
                delay = 5 * (attempt + 1)  # Increasing delay
                await asyncio.sleep(delay)
    raise Exception("All session creation attempts failed")

# Usage
client = AsyncHyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))
session = await create_session_with_retry(
    client,
    CreateSessionParams(use_stealth=True, timeout_minutes=30)
)
```

## Session Timeout Error Handling

```python
try:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(session.ws_endpoint)
        context = browser.contexts[0]
        page = context.pages[0]
        await page.goto(url, timeout=60000)
        # ... automation logic
except Exception as e:
    print(f"Session error: {e}")
    # Session may have auto-closed, create new one
finally:
    await client.sessions.stop(session.id)
```

## Retry with Multiple Sessions

```python
async def process_with_fallback():
    session = None
    try:
        session = await client.sessions.create(
            params=CreateSessionParams(timeout_minutes=30)
        )
        # ... process
    except Exception as e:
        print(f"Primary session failed: {e}")
        if session:
            await client.sessions.stop(session.id)
        session = await client.sessions.create(
            params=CreateSessionParams(
                timeout_minutes=30,
                use_stealth=True  # Try with stealth
            )
        )
        # ... retry
    finally:
        if session:
            await client.sessions.stop(session.id)
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Session timed out` | `timeout_minutes` expired | Increase timeout or optimize script |
| `Connection refused` | Session already closed/timeout | Create new session, check timeout |
| `Invalid API key` | Wrong/missing API key | Verify `HYPERBROWSER_API_KEY` |
| `Session not found` | Session ID invalid or closed | Check session lifecycle |
| `Rate limited` | Too many concurrent sessions | Wait and retry, check plan limits |

## 3DHunyuan Project Notes

- **Current Browserless**: Uses `close_browserless_session()` in finally block — mirror this with `client.sessions.stop()`
- **Timeouts**: Project uses `MAX_TIME=180` (max element wait), `WAIT_TIME=3` (inter-action pause)
- **Photo upload**: If file upload fails, check that the file exists and path is absolute
- **Session per row**: Each Excel row creates a new browser session — important to clean up after each row

## Best Practices

- Always use `try/finally` for session cleanup
- Implement retry with exponential backoff
- Set appropriate `timeout_minutes` at creation
- Monitor session duration vs. timeout
- Log session IDs for debugging
- Handle WebSocket disconnections gracefully
