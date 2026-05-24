# Troubleshooting Guide for Browserless

## Connection Issues

### "Target closed" or "Connection refused"

**Symptoms**:
```python
playwright._impl._api_types.Error: Target closed
# or
playwright._impl._api_types.Error: Connection closed
```

**Causes**:
- Session timed out (exceeded plan's max duration)
- Network disconnect
- Browserless server restart
- Invalid/expired token

**Solutions**:
```python
# 1. Check token validity
import os
token = os.getenv('BROWSERLESS_TOKEN')
assert token and len(token) > 20, "Invalid token"

# 2. Increase timeout in URL
ws = f"wss://production-sfo.browserless.io/?token={token}&timeout=600000"

# 3. Implement retry logic
async def connect_with_retry(token, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await create_browserless_browser(token)
        except Error as e:
            if "Target closed" in str(e) or "closed" in str(e).lower():
                print(f"Retry {attempt + 1}/{max_retries}")
                await asyncio.sleep(5 * (attempt + 1))
                continue
            raise
    raise Exception("All retries failed")

# 4. Check your plan's session duration limit
# Free=1min, Prototyping=15min, Scale=60min
```

### "401 Unauthorized"

**Causes**:
- Token missing from URL
- Token invalid/expired
- Using wrong region for your account

**Solutions**:
```python
# 1. Verify token exists
if not token or token == "YOUR_TOKEN":
    print("ERROR: Set BROWSERLESS_TOKEN environment variable")
    exit(1)

# 2. Check Dashboard for token
# Visit: https://dashboard.browserless.io/account/api-keys

# 3. Use correct regional endpoint
# Your plan may be limited to specific region
# Free plans typically use production-sfo only
```

---

## File Upload Issues

### "Local file path not accessible"

**Symptoms**:
- File input remains empty
- Upload fails silently

**Cause**: Using local path directly:
```python
await input.set_input_files('/path/to/file.jpg')  # WRONG for Browserless!
```

**Solution**: Use base64 + DataTransfer (see `base64_handling.md`)

**Example**:
```python
import base64

async def upload_correct(page, file_path):
    with open(file_path, 'rb') as f:
        base64_data = base64.b64encode(f.read()).decode('utf-8')

    await page.evaluate(
        '''({file, name, type}) => {
            function toUint8Array(b64) {
                const binary = atob(b64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                return bytes;
            }
            const input = document.querySelector('input[type="file"]');
            const fileObj = new File([toUint8Array(file)], name, { type });
            const dt = new DataTransfer();
            dt.items.add(fileObj);
            input.files = dt.files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }''',
        {'file': base64_data, 'name': Path(file_path).name, 'type': 'image/jpeg'}
    )
```

---

## Proxy Issues

### "Proxy not working, real IP exposed"

**Check**:
```python
# Verify proxy is in connection URL
ws = f"wss://...?token={token}&proxy=residential&proxyCountry=us"

# Check WebRTC leaks (bypasses proxy)
# Add --disable-webrtc flag or use stealth mode
ws += "&--disable-webrtc"
```

**Test**:
```python
async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp(ws)
    page = browser.contexts[0].new_page()
    await page.goto('https://ip-api.com/json/')
    ip = await page.text_content('body')
    print(f"IP: {ip}")  # Should show proxy IP, not your real IP
    await browser.close()
```

---

## Stealth Mode Issues

### "Still blocked despite using stealth"

**Common reasons**:

1. **Missing proxy**: Some sites require IP from specific country
   ```python
   # Add proxy
   ws = f"wss://.../stealth?token={token}&proxy=residential&proxyCountry=us"
   ```

2. **Insufficient wait time**: CAPTCHA/interstitial needs time to solve
   ```python
   await page.goto(url, wait_until='networkidle', timeout=120000)
   await page.wait_for_load_state('networkidle')
   ```

3. **Wrong stealth endpoint**: Use `/stealth` not `/chromium` only
   ```python
   # Good
   ws = "wss://.../stealth?token=..."
   # Bad (no stealth)
   ws = "wss://.../chromium?token=..."
   ```

4. **Complex fingerprinting**: Site uses advanced device fingerprinting
   - Consider BrowserQL with `unblock` strategy: `"aggressive"`
   - Add manual delays: `await page.wait_for_timeout(5000)`

---

## Performance Issues

### "Browserless is slow"

**Diagnosis**:
```python
import time

async def benchmark():
    token = os.getenv('BROWSERLESS_TOKEN')

    # Test regional endpoint
    regions = ['sfo', 'lon', 'ams']
    for region in regions:
        ws = f"wss://production-{region}.browserless.io/?token={token}"
        start = time.time()
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(ws)
            page = browser.contexts[0].new_page()
            await page.goto('https://example.com')
            elapsed = time.time() - start
            print(f"{region}: {elapsed:.2f}s")
            await browser.close()

benchmark()
```

**Solutions**:
1. Use nearest regional endpoint to your target site
2. Reduce number of `await` calls (bundle in `page.evaluate()`)
3. Reuse sessions when possible (but respect duration limits)
4. Use connection pooling

---

## Memory/Resource Leaks

### "Sessions accumulating in dashboard"

**Cause**: Forgetting `browser.close()` in exception cases

**Fix - Always use try-finally**:
```python
async def safe_automation():
    browser = None
    try:
        browser = await create_browserless_browser(token)
        # ... work ...
    finally:
        if browser:
            await browser.close()  # CRITICAL
```

**Detect leaks**:
```python
class LeakDetector:
    created = 0
    closed = 0

    @classmethod
    def created_session(cls):
        cls.created += 1
        print(f"Sessions: {cls.created} created, {cls.closed} closed")

    @classmethod
    def closed_session(cls):
        cls.closed += 1
        print(f"Sessions: {cls.created} created, {cls.closed} closed")

# Wrap create/close
async def tracked_create():
    browser = await create_browserless_browser(token)
    LeakDetector.created_session()
    return browser

async def tracked_close(browser):
    await browser.close()
    LeakDetector.closed_session()
```

---

## Selector Issues

### "Selector not found" despite element existing

**Check**:
```python
# 1. Wait for page to load properly
await page.goto(url, wait_until='networkidle')

# 2. Use appropriate wait
await page.wait_for_selector('.my-element', timeout=30000)

# 3. Debug: dump page content
html = await page.content()
print(f"HTML length: {len(html)}")
with open('debug.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 4. Check frame context
frames = page.frames
for frame in frames:
    try:
        element = frame.query_selector('.my-element')
        if element:
            print(f"Found in frame: {frame.url}")
    except:
        pass
```

---

## Timeout Issues

### "Navigation timeout" or "Operation timed out"

**Cause**: Timeout too short for network latency

**Fix**:
```python
# Increase timeout globally
os.environ['PLAYWRIGHT_BROWSER_TIMEOUT'] = '300000'  # 5 min

# Or per operation
await page.goto(url, timeout=120000)  # 2 minutes

# Add wait condition
await page.goto(url, wait_until='networkidle', timeout=60000)

# Avoid networkidle on busy pages
await page.goto(url, wait_until='domcontentloaded', timeout=30000)
```

---

## Rate Limiting (429)

**Symptoms**:
```python
requests.exceptions.HTTPError: 429 Client Error: Too Many Requests
```

**Causes**:
- Exceeded plan's concurrency limit
- Making too many requests in short time

**Solution**:
```python
# 1. Check concurrency limits in dashboard
# Reduce parallel sessions

# 2. Implement rate limiting
import asyncio

class RateLimiter:
    def __init__(self, rate: float):
        self.rate = rate  # requests per second
        self.last = time.time()

    async def acquire(self):
        elapsed = time.time() - self.last
        wait_time = max(0, 1/self.rate - elapsed)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self.last = time.time()

limiter = RateLimiter(rate=0.5)  # Max 0.5 req/sec

async def make_request():
    await limiter.acquire()
    # ... make API call ...
```

**3. Close sessions promptly** - lingering sessions count toward concurrency

---

## Debug Checklist

When something doesn't work, check:

- [ ] Token valid? (`echo $BROWSERLESS_TOKEN`)
- [ ] Correct regional endpoint? (`sfo`, `lon`, `ams`)
- [ ] Using `connect_over_cdp()` not `connect()` (for CDP mode)?
- [ ] Browser closed in `finally` block?
- [ ] Timeout high enough? (min 30000ms)
- [ ] Selector correct? Inspect in DevTools
- [ ] File upload using base64, not local path?
- [ ] Proxy parameters URL-encoded?
- [ ] Plan supports required features? (stealth, city-level proxy)
- [ ] Check dashboard for errors: https://dashboard.browserless.io
- [ ] Verified with minimal reproducible example?

---

## Getting Help

1. **Browserless Docs**: https://docs.browserless.io/
2. **Dashboard**: https://dashboard.browserless.io (check session logs)
3. **GitHub Issues**: https://github.com/browserless/browserless/issues
4. **Community Discord**: https://discord.browserless.io/
5. **Support Email**: support@browserless.io (for paid plans)

When requesting help, include:
- Browserless account email/ID
- Plan tier
- Token prefix (first 10 chars)
- Error message + stack trace
- Minimal code snippet that reproduces
- Browserless response headers (x-response-code, x-response-status)
- Your regional endpoint

---

## Quick Diagnostic Script

```python
#!/usr/bin/env python3
"""Diagnose common Browserless issues."""
import os, requests, asyncio
from playwright.async_api import async_playwright

async def diagnose():
    token = os.getenv('BROWSERLESS_TOKEN')
    if not token:
        print("❌ BROWSERLESS_TOKEN not set")
        return

    print(f"✓ Token: {token[:10]}...")

    # 1. Check token validity
    resp = requests.get(f"https://dashboard.browserless.io/api/v1/me?token={token}")
    if resp.status_code == 200:
        print(f"✓ Token valid, plan: {resp.json().get('plan', 'unknown')}")
    else:
        print(f"❌ Token invalid: {resp.status_code}")
        return

    # 2. Test connection (sfo)
    print("\nConnecting to sfo region...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(
                f"wss://production-sfo.browserless.io/?token={token}"
            )
            page = browser.contexts[0].new_page()
            await page.goto('https://example.com', timeout=30000)
            title = await page.title()
            print(f"✓ Connected, page title: {title}")
            await browser.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # 3. Test stealth endpoint
    print("\nTesting stealth endpoint...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(
                f"wss://production-sfo.browserless.io/stealth?token={token}"
            )
            page = browser.contexts[0].new_page()
            await page.goto('https://nowsecure.nl/', timeout=30000)
            title = await page.title()
            blocked = 'just a moment' in title.lower()
            print(f"{'❌' if blocked else '✓'} Stealth: {'blocked' if blocked else 'ok'}")
            await browser.close()
    except Exception as e:
        print(f"❌ Stealth failed: {e}")

    print("\n✅ Diagnostics complete")

if __name__ == '__main__':
    asyncio.run(diagnose())
```

---

## See Also

- Error Handling Patterns: `error_handling.md`
- Session Management: `session_management.md`
- Proxy Configuration: `proxy_configuration.md`
- Browserless Status: https://status.browserless.io/
