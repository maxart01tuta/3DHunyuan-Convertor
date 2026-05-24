# Error Handling & Retry Patterns for Browserless

## Common Errors

### HTTP Status Codes

| Code | Meaning | Cause | Solution |
|------|---------|-------|----------|
| 400 | Bad Request | Invalid JSON, negative timeout, conflicting params | Validate payload, check timeout values |
| 401 | Unauthorized | Invalid/missing token, or endpoint not in your plan | Verify token, check plan features |
| 403 | Forbidden | Wrong regional endpoint or IP restrictions | Use correct region for your account |
| 404 | Not Found | Invalid endpoint URL | Check URL spelling |
| 408 | Request Timeout | Timeout too low or selector never appears | Increase timeout, verify selectors |
| 429 | Too Many Requests | Exceeded concurrency limit (unclosed sessions) | Close browsers in finally |
| 500+ | Server Error | Browserless internal error | Retry with backoff |

---

## Retry Pattern with Exponential Backoff

```python
import asyncio
import random
from typing import Callable, Any

async def retry_with_backoff(
    operation: Callable,
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0
) -> Any:
    """
    Retry async operation with exponential backoff.

    Args:
        operation: Async function to retry
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for each retry (default 2)

    Returns:
        Result of successful operation

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                delay = min(base_delay * (backoff_factor ** (attempt - 1)), max_delay)
                print(f"[RETRY] Attempt {attempt}/{max_retries}, waiting {delay:.1f}s...")
                await asyncio.sleep(delay)

            result = await operation()
            if attempt > 0:
                print(f"[SUCCESS] Operation succeeded after {attempt} retries")
            return result

        except Exception as e:
            last_exception = e
            print(f"[ERROR] Attempt {attempt + 1} failed: {e}")

            # Don't sleep on last attempt
            if attempt == max_retries:
                break

    raise last_exception

# Usage
async def connect_to_browserless():
    token = os.getenv('BROWSERLESS_TOKEN')
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(
            f"wss://production-sfo.browserless.io/?token={token}"
        )
        return browser

try:
    browser = await retry_with_backoff(
        connect_to_browserless,
        max_retries=3,
        base_delay=5
    )
except Exception as e:
    print(f"Failed to connect after retries: {e}")
```

---

## Token Rotation with Fallback

```python
class BrowserlessConnector:
    def __init__(self, tokens: list, region: str = "sfo"):
        self.tokens = tokens
        self.region = region

    async def connect(self, timeout: int = 300000):
        """Connect using random token with retry fallback."""
        max_attempts = len(self.tokens) * 3

        for attempt in range(max_attempts):
            token = random.choice(self.tokens)
            try:
                ws = f"wss://production-{self.region}.browserless.io/?token={token}&timeout={timeout}"

                async with async_playwright() as p:
                    browser = await p.chromium.connect_over_cdp(ws)
                    context = browser.contexts[0]
                    page = await context.new_page()

                    return {
                        'browser': browser,
                        'context': context,
                        'page': page,
                        'token': token
                    }

            except Exception as e:
                print(f"[WARN] Token {token[:10]}... failed: {e}")
                await asyncio.sleep(5)

        raise Exception(f"All {len(self.tokens)} tokens exhausted after {max_attempts} attempts")

# Usage
connector = BrowserlessConnector([
    "token1",
    "token2",
    "token3"
])
result = await connector.connect()
```

---

## Try-Catch Block Templates

### Template 1: Simple Try-Except-Finally

```python
async def run_automation():
    browser = None
    try:
        # Connect to Browserless
        browser = await connect_to_browserless()
        page = browser.contexts[0].new_page()

        # Your automation
        await page.goto('https://example.com')
        # ...

    except PlaywrightError as e:
        print(f"[CRITICAL] Playwright error: {e}")
        raise
    except requests.RequestException as e:
        print(f"[NETWORK] HTTP request failed: {e}")
        raise
    except asyncio.TimeoutError as e:
        print(f"[TIMEOUT] Operation timed out: {e}")
        raise
    except Exception as e:
        print(f"[UNKNOWN] Unexpected error: {type(e).__name__}: {e}")
        raise
    finally:
        if browser:
            await browser.close()
            print("[INFO] Browser closed")
```

### Template 2: Granular Exception Handling

```python
import playwright
from playwright.async_api import Error as PlaywrightError
import requests

async def robust_operation(page):
    try:
        # Navigation
        await page.goto('https://example.com', timeout=30000)

    except PlaywrightError as e:
        # Playwright-specific errors
        if "Timeout" in str(e):
            print("[ERROR] Navigation timeout - page took too long")
            # Take screenshot for debugging
            await page.screenshot(path='error_timeout.png')
        elif "selector" in str(e).lower():
            print("[ERROR] Selector not found")
        else:
            print(f"[ERROR] Playwright error: {e}")
        raise

    except requests.RequestException as e:
        # Network errors for REST API calls
        status = e.response.status_code if e.response else None
        print(f"[NETWORK] HTTP {status}: {e}")
        if status == 429:
            print("[RATE LIMIT] Too many requests - implement backoff")
        raise

    except ValueError as e:
        print(f"[DATA] Invalid data format: {e}")
        raise

    else:
        print("[SUCCESS] Operation completed")
        return True
```

---

## Specific Exceptions Reference

### Playwright Exceptions

```python
from playwright.async_api import Error, TimeoutError

try:
    await page.click('#nonexistent', timeout=5000)
except TimeoutError:
    print("Action timed out (selector not found or not actionable)")
except Error as e:
    print(f"Playwright error: {e}")
```

Common Playwright errors:
- `TimeoutError` - Operation exceeded timeout
- `Error` with message containing "selector" - Element not found
- `Error` with "locator" - Locator resolution failed
- `Error` with "navigation" - Page failed to navigate

### HTTP Errors from REST API

```python
import requests
from requests.exceptions import RequestException

try:
    response = requests.post(
        'https://production-sfo.browserless.io/screenshot?token=TOKEN',
        json={'url': 'https://example.com'},
        timeout=60
    )
    response.raise_for_status()  # Raises HTTPError for 4xx/5xx
except RequestException as e:
    if e.response is not None:
        status = e.response.status_code
        print(f"HTTP {status}: {e}")
        if status == 401:
            print("→ Check API token")
        elif status == 429:
            print("→ Rate limited, reduce concurrency")
        elif status == 403:
            print("→ Check region/plan")
    else:
        print(f"Network error: {e}")
```

---

## Circuit Breaker Pattern

```python
class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    Opens circuit after consecutive failures, rejects calls for cooldown period.
    """
    def __init__(self, failure_threshold: int = 5, cooldown: float = 60.0):
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, operation: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.cooldown:
                self.state = "HALF_OPEN"
                print("[CIRCUIT] Half-open, allowing test request")
            else:
                raise Exception("Circuit is OPEN - operation rejected")

        try:
            result = await operation(*args, **kwargs)
            if self.state != "CLOSED":
                self.state = "CLOSED"
                self.failures = 0
                print("[CIRCUIT] Closed, operations restored")
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()

            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                print(f"[CIRCUIT] OPEN - {self.failures} failures, cooldown {self.cooldown}s")

            raise

# Usage
breaker = CircuitBreaker(failure_threshold=3, cooldown=30)

async def safe_connect():
    return await breaker.call(connect_to_browserless)
```

---

## Monitoring & Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('browserless.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def monitored_operation(page):
    start = time.time()
    try:
        logger.info("Starting page.goto()")
        await page.goto('https://example.com', wait_until='networkidle')
        elapsed = time.time() - start
        logger.info(f"Navigation completed in {elapsed:.2f}s")
        return True
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"Operation failed after {elapsed:.2f}s: {e}")
        # Screenshot for debugging
        await page.screenshot(path=f'error_{int(time.time())}.png')
        raise
```

---

## Common Error Scenarios & Solutions

### Scenario 1: Connection Refused

```python
# Error: playwright._impl._api_types.Error: Target closed
# Browserless session closed unexpectedly

async def handle_connection_closed():
    try:
        browser = await connect_to_browserless()
    except Error as e:
        if "Target closed" in str(e) or "Connection closed" in str(e):
            print("Browserless disconnected - retrying...")
            await asyncio.sleep(5)
            return await connect_to_browserless()  # retry
        raise
```

### Scenario 2: Timeout on Slow Networks

```python
# Increase timeout globally
import os
os.environ['PLAYWRIGHT_BROWSER_TIMEOUT'] = '600000'  # 10 minutes

# Or per-operation
await page.goto('https://slow-site.com', timeout=300000, wait_until='networkidle')
```

### Scenario 3: Selector Not Found

```python
async def safe_click(page, selector: str, description: str = "element"):
    """Click with better error messages."""
    try:
        element = await page.wait_for_selector(selector, timeout=10000)
        await element.click()
    except TimeoutError:
        # Provide diagnostic info
        html = await page.content()
        print(f"[DEBUG] Looking for: {selector}")
        print(f"[DEBUG] Page title: {await page.title()}")
        print(f"[DEBUG] URL: {page.url}")

        # Check if selector exists but not visible
        elements = await page.query_selector_all(selector)
        print(f"[DEBUG] Found {len(elements)} elements matching selector")
        if elements:
            for i, el in enumerate(elements):
                visible = await el.is_visible()
                print(f"  Element {i}: visible={visible}")

        raise TimeoutError(f"Could not find {description} with selector '{selector}'")
```

### Scenario 4: Memory Leaks / Too Many Sessions

```python
# Problem: Scripts crash without closing browsers, accumulate in dashboard

class SessionManager:
    """Automatic session cleanup."""
    def __init__(self):
        self.sessions = []

    async def create_session(self, token: str):
        browser = await connect_to_browserless(token)
        self.sessions.append(browser)
        return browser

    async def cleanup_all(self):
        """Close all sessions."""
        for browser in self.sessions:
            try:
                await browser.close()
            except:
                pass
        self.sessions.clear()

# Usage
manager = SessionManager()
try:
    browser = await manager.create_session(token)
    # ... do work
finally:
    await manager.cleanup_all()
```

---

## Retry with Multiple Tokens (Full Implementation)

```python
from typing import Optional
import asyncio
import random

class ResilientBrowserless:
    """Browserless connector with comprehensive retry logic."""

    def __init__(
        self,
        tokens: list[str],
        region: str = "sfo",
        max_token_retries: int = 3,
        connection_timeout: int = 300000
    ):
        self.tokens = tokens
        self.region = region
        self.max_token_retries = max_token_retries
        self.connection_timeout = connection_timeout

    async def connect(self) -> Optional[dict]:
        """Connect with full retry across all tokens."""
        attempts = 0
        max_attempts = len(self.tokens) * self.max_token_retries

        while attempts < max_attempts:
            token = random.choice(self.tokens)
            attempt_num = attempts + 1

            try:
                print(f"[INFO] Attempt {attempt_num}/{max_attempts} with token {token[:10]}...")

                ws = f"wss://production-{self.region}.browserless.io/?token={token}&timeout={self.connection_timeout}"

                async with async_playwright() as p:
                    browser = await p.chromium.connect_over_cdp(ws)
                    context = browser.contexts[0]
                    page = await context.new_page()

                    print(f"[SUCCESS] Connected with token {token[:10]}...")
                    return {
                        'browser': browser,
                        'context': context,
                        'page': page,
                        'token': token,
                        'attempts': attempt_num
                    }

            except Exception as e:
                attempts += 1
                print(f"[ERROR] Token {token[:10]}... failed: {e}")

                if attempts >= max_attempts:
                    print(f"[FATAL] All {len(self.tokens)} tokens exhausted after {max_attempts} attempts")
                    break

                delay = min(5 * (attempts // len(self.tokens) + 1), 30)
                print(f"[RETRY] Waiting {delay}s before next attempt...")
                await asyncio.sleep(delay)

        return None

# Usage
connector = ResilientBrowserless(
    tokens=["token1", "token2", "token3"],
    region="sfo",
    max_token_retries=3
)

result = await connector.connect()
if result:
    try:
        page = result['page']
        await page.goto('https://example.com')
        # ... work
    finally:
        await result['browser'].close()
else:
    print("Failed to connect")
```

---

## Logging Errors to File

```python
import json
from datetime import datetime

class ErrorLogger:
    def __init__(self, log_file: str = 'browserless_errors.log'):
        self.log_file = log_file

    def log_error(self, error: Exception, context: dict = None):
        """Log error with context for later analysis."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

        print(f"[LOG] Error logged to {self.log_file}")

# Usage
logger = ErrorLogger()

try:
    await page.goto('https://example.com')
except Exception as e:
    logger.log_error(e, {
        'url': page.url,
        'selector': '#example',
        'attempt': 2
    })
```

---

## Quick Reference: Common Error Messages

| Error Message | Likely Cause | Fix |
|---------------|--------------|-----|
| "Target closed" | Browser disconnected | Reconnect, check timeout |
| "Timeout" | Operation too slow | Increase timeout, optimize selectors |
| "selector not found" | Wrong selector or element not loaded | Wait for selector, check page state |
| "401 Unauthorized" | Invalid token | Verify token, don't hardcode |
| "429 Too Many Requests" | Too many concurrent sessions | Close browsers, reduce concurrency |
| "Network error" | Internet disconnected | Check connectivity, retry |
| "Node is not currently in a state that can be performing this action" | Page context lost | Refresh page, recreate context |

---

## Best Practices Summary

1. **Always use try-finally** to close browsers
2. **Implement retry logic** with exponential backoff
3. **Use token rotation** for redundancy
4. **Log errors with context** for debugging
5. **Take screenshots on errors** for visual debugging
6. **Don't swallow exceptions** - log and re-raise
7. **Set reasonable timeouts** (300000ms minimum for Browserless)
8. **Monitor concurrency** - close sessions promptly
9. **Check response status codes** when using REST API
10. **Validate inputs** before expensive operations

---

## See Also

- Session Management: `session_management.md`
- Troubleshooting: `troubleshooting.md`
- Best Practices: Reference in `MEMORY.md`
