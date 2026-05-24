# Session Management for Browserless

## Overview

Browserless sessions have lifecycle constraints based on your plan. Understanding session management prevents leaks and maximizes efficiency.

---

## Connection Lifecycle

```
┌─────────────┐
│   Connect   │ → Creates browser session on Browserless servers
└─────────────┘
      ↓
┌─────────────┐
│   Work...   │ → Execute automation, navigate pages
└─────────────┘
      ↓
┌─────────────┐
│   Close     │ → Terminates session, releases resources
└─────────────┘
```

### Session Creation

```python
from playwright.async_api import async_playwright

async def create_session(token: str, region: str = "sfo"):
    """Create new Browserless session."""
    ws = f"wss://production-{region}.browserless.io/?token={token}"

    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp(ws)

    context = browser.contexts[0]  # Default context exists in CDP mode
    page = await context.new_page()

    return {
        'playwright': playwright,
        'browser': browser,
        'context': context,
        'page': page
    }
```

---

## Session Duration Limits by Plan

| Plan | Max Session Duration |
|------|---------------------|
| Free | 1 minute |
| Prototyping (15k-100k) | 15 minutes |
| Starter (180k) | 30 minutes |
| Scale (500k+) | 60 minutes |
| Enterprise | Custom |

⚠️ Sessions exceeding limit are forcefully terminated by Browserless.

---

## Concurrency Limits

| Plan | Monthly Concurrent | Yearly Concurrent |
|------|-------------------|-------------------|
| Free | 2 | 2 |
| Prototyping | 5 | 10 |
| Starter | 30 | 40 |
| Scale | 80 | 100 |
| Enterprise | Custom | Custom |

**Concurrent** = number of active sessions at the same time.

---

## Proper Cleanup Pattern

```python
async def run_with_cleanup():
    resources = None
    try:
        resources = await create_session(os.getenv('BROWSERLESS_TOKEN'))
        page = resources['page']

        # Your automation logic here
        await page.goto('https://example.com')
        # ...

    finally:
        if resources:
            # Close in reverse order
            await resources['page'].close()
            await resources['context'].close()
            await resources['browser'].close()
            await resources['playwright'].stop()
            print("✓ Session closed and resources released")

# Usage
await run_with_cleanup()
```

---

## Context Manager Pattern (Recommended)

```python
class BrowserlessSession:
    """Context manager for Browserless sessions."""

    def __init__(self, token: str, region: str = "sfo", timeout: int = 300000):
        self.token = token
        self.region = region
        self.timeout = timeout
        self.resources = None

    async def __aenter__(self):
        self.resources = await create_session(self.token, self.region)
        return self.resources['page']

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.resources:
            await self.resources['page'].close()
            await self.resources['context'].close()
            await self.resources['browser'].close()
            await self.resources['playwright'].stop()
        return False  # Don't suppress exceptions

# Usage (async with)
async with BrowserlessSession(token=os.getenv('BROWSERLESS_TOKEN')) as page:
    await page.goto('https://example.com')
    # Auto-closes on exit
```

---

## Tracking Active Sessions

```python
import requests

def list_active_sessions(token: str) -> list:
    """Check active sessions in your Browserless account."""
    # Browserless doesn't have direct "list sessions" API like Steel
    # Instead, check your dashboard: https://dashboard.browserless.io/sessions

    # For programmatic access, use BrowserQL or check usage metrics
    url = "https://production-sfo.browserless.io/usage?token=" + token
    resp = requests.get(url)

    if resp.status_code == 200:
        data = resp.json()
        return data.get('sessions', [])

    return []

# Check dashboard manually for active sessions
# https://dashboard.browserless.io/sessions
```

---

## Session Reconnect (Advanced)

⚠️ **Important**: Standard Sessions with `reconnect` work reliably only with Puppeteer, not Playwright. Playwright does not expose `browser.disconnect()`. Use manual state persistence instead.

### For Puppeteer Only (Reference)

```javascript
// Puppeteer - reconnect pattern
const { browser, page, cdp } = await connectToBrowserless();

// ... do work ...

// Prepare for reconnection
const { browserWSEndpoint } = await cdp.send('Browserless.reconnect', {
    timeout: 30000  // 30 seconds
});

await browser.disconnect();  // Keeps browser alive on server

// Later, in another process:
const reconnected = await puppeteer.connect({
    browserWSEndpoint: `${browserWSEndpoint}?token=${token}`
});
```

### For Playwright: Manual State Persistence

```python
async def save_session_state(page) -> dict:
    """Save cookies and localStorage for later reuse."""
    cookies = await page.context.cookies()
    local_storage = await page.evaluate('''() => {
        const data = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            data[key] = localStorage.getItem(key);
        }
        return data;
    }''')
    session_storage = await page.evaluate('''() => {
        const data = {};
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            data[key] = sessionStorage.getItem(key);
        }
        return data;
    }''')

    return {
        'url': page.url,
        'cookies': cookies,
        'localStorage': local_storage,
        'sessionStorage': session_storage
    }

async def restore_session_state(context, state: dict):
    """Restore saved session state to new context."""
    await context.add_cookies(state['cookies'])

    page = await context.new_page()
    await page.goto(state['url'])

    # Restore local storage
    await page.evaluate('''([ls, ss]) => {
        Object.entries(ls).forEach(([k, v]) => localStorage.setItem(k, v));
        Object.entries(ss).forEach(([k, v]) => sessionStorage.setItem(k, v));
    }''', [state['localStorage'], state['sessionStorage']])

    return page

# Usage
state = await save_session_state(page)
# ... later, new session ...
page = await restore_session_state(context, state)
```

---

## Connection URL Timeout Parameter

```python
# Session auto-terminates after 'timeout' milliseconds
# Limits vary by plan: Free=10000, Prototyping=30000, Scale=300000

ws = f"wss://production-sfo.browserless.io/?token={token}&timeout=300000"
```

**Example - Short timeout for quick tasks**:
```python
# 30 second timeout for scraping
ws = f"wss://production-sfo.browserless.io/?token={token}&timeout=30000"
```

**Example - Long timeout for complex workflows**:
```python
# 10 minute timeout (Scale plan)
ws = f"wss://production-sfo.browserless.io/?token={token}&timeout=600000"
```

---

## Session Pooling Pattern (Advanced)

```python
class SessionPool:
    """
    Pool of pre-warmed browser sessions.
    Reuse sessions to reduce connection overhead.
    """

    def __init__(self, size: int = 3, token: str = None, region: str = "sfo"):
        self.size = size
        self.token = token or os.getenv('BROWSERLESS_TOKEN')
        self.region = region
        self._pool = []
        self._in_use = []

    async def initialize(self):
        """Pre-create sessions."""
        for _ in range(self.size):
            session = await self._create_session()
            self._pool.append(session)

    async def acquire(self):
        """Get session from pool (or create new if pool empty)."""
        if self._pool:
            session = self._pool.pop()
            self._in_use.append(session)
            return session
        else:
            # Pool exhausted, create new session
            return await self._create_session()

    async def release(self, session: dict):
        """Return session to pool (reset state first)."""
        # Clear cookies to simulate fresh session
        await session['context'].clear_cookies()

        # Navigate to blank page
        await session['page'].goto('about:blank')

        self._in_use.remove(session)
        self._pool.append(session)

    async def _create_session(self):
        resources = await create_session(self.token, self.region)
        return resources

    async def close_all(self):
        """Close all sessions."""
        all_sessions = self._pool + self._in_use
        for session in all_sessions:
            try:
                await session['page'].close()
                await session['context'].close()
                await session['browser'].close()
                await session['playwright'].stop()
            except:
                pass
        self._pool.clear()
        self._in_use.clear()

# Usage
pool = SessionPool(size=3, token=os.getenv('BROWSERLESS_TOKEN'))
await pool.initialize()

try:
    session = await pool.acquire()
    page = session['page']
    await page.goto('https://example.com')
    # ... work ...
    await pool.release(session)  # Return to pool
finally:
    await pool.close_all()
```

---

## Session Health Monitoring

```python
async def check_session_health(page) -> dict:
    """Check if session is healthy and responsive."""
    try:
        start = time.time()
        await page.goto('about:blank', wait_until='load', timeout=10000)
        elapsed = time.time() - start

        return {
            'healthy': True,
            'response_time_ms': elapsed * 1000,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

# Periodic health check
async def monitor_sessions(pages: list, interval: int = 60):
    """Monitor multiple sessions."""
    while True:
        for i, page in enumerate(pages):
            health = await check_session_health(page)
            if not health['healthy']:
                print(f"[ALERT] Session {i} unhealthy: {health['error']}")
                # Recreate session
                # ...

        await asyncio.sleep(interval)
```

---

## Avoiding Session Leaks

### ✅ DO:
```python
async def safe_run():
    browser = None
    try:
        browser = await connect()
        # ... work
    finally:
        if browser:
            await browser.close()  # CRITICAL
```

### ❌ DON'T:
```python
async def leaky_run():
    browser = await connect()  # No try-finally → leaks if exception occurs
    await page.goto('https://example.com')
    # Missing browser.close()
```

### Example: Leak Detection

```python
class LeakDetector:
    """Track sessions to detect leaks."""

    def __init__(self):
        self.created = 0
        self.closed = 0

    def session_created(self):
        self.created += 1
        print(f"[POOL] Sessions created: {self.created}, closed: {self.closed}")

    def session_closed(self):
        self.closed += 1
        print(f"[POOL] Sessions created: {self.created}, closed: {self.closed}")

    def check_leaks(self):
        if self.created != self.closed:
            leaked = self.created - self.closed
            print(f"[WARNING] {leaked} session(s) may have leaked!")
            return leaked
        return 0

detector = LeakDetector()

async def tracked_connect():
    browser = await connect()
    detector.session_created()
    return browser

async def tracked_close(browser):
    await browser.close()
    detector.session_closed()
```

---

## Graceful Degradation

```python
async def resilient_operation(max_retries: int = 3):
    """Try operation multiple times, handle session expiration."""
    for attempt in range(max_retries):
        try:
            token = get_next_token()  # rotate tokens
            async with BrowserlessSession(token) as page:
                await page.goto('https://example.com')
                result = await page.text_content('main')
                return result
        except Exception as e:
            if "Timeout" in str(e) or "closed" in str(e).lower():
                print(f"[RETRY] Session issue, attempt {attempt + 1}")
                await asyncio.sleep(5 * (attempt + 1))
                continue
            else:
                raise  # Non-retryable error

    raise Exception(f"Failed after {max_retries} retries")
```

---

## Session Duration Optimization

```python
import time

async def optimized_single_task():
    """
    Do one task and close immediately.
    Best for high-volume scenarios.
    """
    token = os.getenv('BROWSERLESS_TOKEN')
    async with BrowserlessSession(token, timeout=60000) as page:
        start = time.time()
        await page.goto('https://example.com')
        data = await page.content()
        elapsed = time.time() - start
        print(f"Task completed in {elapsed:.2f}s")
        return data

async def optimized_multi_task_batch():
    """
    Batch multiple tasks in one session.
    Reduces connection overhead for related operations.
    """
    token = os.getenv('BROWSER_TOKEN')
    async with BrowserlessSession(token, timeout=300000) as page:
        tasks = ['site1.com', 'site2.com', 'site3.com']
        results = []

        for url in tasks:
            await page.goto(f'https://{url}', wait_until='domcontentloaded')
            content = await page.content()
            results.append(content)
            print(f"✓ Fetched {url}")

        return results
```

---

## Dashboard Monitoring

Always monitor your Browserless dashboard:

1. **Active Sessions**: https://dashboard.browserless.io/sessions
2. **Usage Metrics**: https://dashboard.browserless.io/usage
3. **Billing**: Check credits consumption

Look for:
- Hanging sessions (close manually if needed)
- Unusual spikes in usage
- Failed sessions count

---

## Session Cleanup Checklist

When script finishes, verify:

- [ ] `await page.close()` called
- [ ] `await context.close()` called
- [ ] `await browser.close()` called
- [ ] `await playwright.stop()` called
- [ ] All inside `finally` block
- [ ] No exceptions preventing cleanup

---

## See Also

- Error Handling: `error_handling.md`
- Stealth Mode: `stealth_anti_detection.md`
- Browserless Docs: https://docs.browserless.io/baas/session-management/reconnect
