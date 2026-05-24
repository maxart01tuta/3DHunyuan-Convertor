# Browserless-Expert Agent Persistent Memory

## Active Memories

### Project Configuration
- **Mode**: CDP (Chrome DevTools Protocol) with Playwright connectOverCDP()
- **Playwright**: python package `playwright` installed (use `playwright-core` for production)
- **API Token**: Stored in `config.json` → `BROWSERLESS_API_TOKEN` (never hardcode!)
- **Timeout**: `MAX_WAIT = 300000` ms (5 minutes) - Browserless has network latency
- **Retry**: 3 attempts per token, random token selection, `API_TIME = 5` sec between attempts
- **Browser cleanup**: Always `await browser.close()` in finally block
- **Browser type**: chromium only (project-specific)
- **Installation**: `pip install playwright` + `playwright install chromium`
- **Working directory**: `BROWSERLESS/` - all scripts analyzed only inside this folder

### Critical Patterns - MUST KNOW

#### 1. File Uploads (THE MOST IMPORTANT!)
**Problem**: Browserless browser runs on remote servers, NOT on your local machine.
Local paths (`/home/user/photo.jpg`) are INACCESSIBLE in remote browser.

**Solution A: Base64 + DataTransfer** (for private/local files) - RECOMMENDED:
```python
import base64

async def upload_local_file(page, file_path: str, selector: str = 'input[type="file"]'):
    """Upload local file to remote Browserless browser using base64."""
    with open(file_path, 'rb') as f:
        file_content = f.read()
    file_name = file_path.split('/')[-1]
    mime_type = _detect_mime_type(file_path)  # implement based on extension

    base64_data = base64.b64encode(file_content).decode('utf-8')

    await page.evaluate(
        '''
        ({ selector, fileName, mimeType, base64Data }) => {
            function b64ToUint8Array(b64) {
                const binary = atob(b64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) {
                    bytes[i] = binary.charCodeAt(i);
                }
                return bytes;
            }
            const input = document.querySelector(selector);
            const file = new File([b64ToUint8Array(base64Data)], fileName, {
                type: mimeType,
            });
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            input.files = dataTransfer.files;
            const event = new Event("change", { bubbles: true });
            input.dispatchEvent(event);
        }
        ''',
        {
            'selector': selector,
            'fileName': file_name,
            'mimeType': mime_type,
            'base64Data': base64_data
        }
    )
```
**IMPORTANT**: Always trigger `change` event after setting files!

**Solution B: Public URL** (if file already in cloud):
```python
await page.locator('input[type="file"]').set_input_files('https://cloud.com/photo.jpg')
```

#### 2. CDP Connection (Project's Main Mode)
```python
from playwright.async_api import async_playwright
import asyncio
import os

async def create_browserless_browser(api_token: str, region: str = "sfo", timeout: int = 300000):
    """Connect to Browserless via CDP with proper configuration."""
    ws_endpoint = f"wss://production-{region}.browserless.io/?token={api_token}&timeout={timeout}"

    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp(ws_endpoint)

    # Create context with custom settings
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        locale='en-US',
        timezone_id='America/New_York',
        ignore_https_errors=True,
    )
    page = await context.new_page()

    return {
        'playwright': playwright,
        'browser': browser,
        'context': context,
        'page': page
    }

# Usage example
async def main():
    token = os.getenv('BROWSERLESS_API_TOKEN')
    resources = await create_browserless_browser(token)
    try:
        page = resources['page']
        await page.goto('https://example.com', wait_until='domcontentloaded')
        # ... your automation
    finally:
        # Cleanup
        await resources['page'].close()
        await resources['context'].close()
        await resources['browser'].close()
        await resources['playwright'].stop()
```

**Alternative with retry logic**:
```python
async def connect_with_retry(api_tokens: list, region: str = "sfo"):
    max_attempts = len(api_tokens) * 3

    for attempt in range(max_attempts):
        token = random.choice(api_tokens)
        try:
            print(f"[INFO] Attempt {attempt + 1}: connecting to Browserless")

            resources = await create_browserless_browser(token, region)
            print(f"[SUCCESS] Connected with token {token[:10]}...")
            return resources

        except Exception as e:
            print(f"[ERROR] Failed with token {token[:10]}...: {e}")
            await asyncio.sleep(5)

    raise Exception("All API tokens exhausted")
```

#### 3. Proper Cleanup (AVOID RESOURCE LEAKS!)
```python
async def close_browserless_browser(resources: dict):
    """Correctly close all resources in reverse order."""
    try:
        if resources.get('page'):
            await resources['page'].close()
        if resources.get('context'):
            await resources['context'].close()
        if resources.get('browser'):
            await resources['browser'].close()
        if resources.get('playwright'):
            await resources['playwright'].stop()
        print("Browserless session closed")
    except Exception as e:
        print(f"[ERROR] Cleanup error: {e}")
```

**Cleanup order** (must be reverse of creation):
1. page.close()
2. context.close()
3. browser.close()
4. playwright.stop()

#### 4. Configuration
Project uses `config.json`:
```json
{
  "perekluchatel": 1,
  "MAX_WAIT": 300000,
  "API_TIME": 5,
  "BROWSERLESS_TOKENS": [
    "2Ss2Vu5IqgsaTwI8a9fd930995a3d55c09833428b4358be31"
  ],
  "BROWSERLESS_REGION": "sfo",
  "PHOTO_BASE_URL": null
}
```

#### 5. Connection URL Patterns

**Standard CDP**:
```
wss://production-sfo.browserless.io/?token=YOUR_TOKEN&timeout=300000
```

**With proxy**:
```
wss://production-sfo.browserless.io/?token=YOUR_TOKEN&proxy=residential&proxyCountry=us
```

**Stealth mode**:
```
wss://production-sfo.browserless.io/stealth?token=YOUR_TOKEN
```

**Playwright native**:
```
wss://production-sfo.browserless.io/chromium/playwright?token=YOUR_TOKEN
```

**Regional endpoints**:
- US West (San Francisco): `production-sfo.browserless.io`
- Europe (London): `production-lon.browserless.io`
- Europe (Amsterdam): `production-ams.browserless.io`

#### 6. Proxy Configuration

**Built-in Residential Proxy**:
```python
# Add to connection URL
ws_endpoint = f"wss://production-sfo.browserless.io/?token={token}&proxy=residential&proxyCountry=us"
```
or for Playwright context:
```python
context = await browser.new_context(
    proxy={
        'server': 'http://us-proxy.browserless.io:80',
    }
)
```

**Sticky sessions**: add `&proxySticky=true` to keep same IP

**City-level** (Scale plan only): `&proxyCity=chicago`

**Third-party proxy**:
```python
# Method 1: externalProxyServer (RECOMMENDED)
ws_endpoint = f"wss://production-sfo.browserless.io/?token={token}&externalProxyServer=http://user:pass@proxy:8080"

# Method 2: Chrome flag (for CDP mode)
ws_endpoint = f"wss://production-sfo.browserless.io/?--proxy-server=http://proxy:8080&token={token}"
```

#### 7. Stealth Mode & Bot Detection

**Use stealth endpoints** for strict bot detectors:
```python
# Stealth browser (hardened binary)
ws_endpoint = f"wss://production-sfo.browserless.io/stealth?token={token}"

# Or stealth on Chromium
ws_endpoint = f"wss://production-sfo.browserless.io/chromium/stealth?token={token}"
```

**With proxy locale matching** (auto-set browser language):
```python
ws_endpoint = f"wss://production-sfo.browserless.io/stealth?token={token}&proxy=residential&proxyCountry=de&proxyLocaleMatch=1"
```

#### 8. Session Management & Reconnect

Browserless позволяет сохранять сессии между переподключениями через CDP команду `Browserless.reconnect`:

```python
# Prepare for reconnection (Puppeteer only, Playwright doesn't have disconnect())
async def prepare_reconnect(cdp_session, browser, timeout: int = 30000):
    """Call before disconnecting to keep browser alive."""
    response = await cdp_session.send("Browserless.reconnect", {
        "timeout": timeout  # How long browser stays alive (ms)
    })
    if response.get('error'):
        raise Exception(f"Reconnect failed: {response['error']}")

    browserWSEndpoint = response.get('browserWSEndpoint')
    await browser.disconnect()  # Detach locally; browser keeps running
    return browserWSEndpoint

# Reconnect later
async def reconnect_session(browserWSEndpoint: str, token: str):
    reconnect_url = f"{browserWSEndpoint}?token={token}"
    browser = await playwright.chromium.connectOverCDP(reconnect_url)
    context = browser.contexts()[0]
    page = await context.new_page()
    return browser, context, page
```

**⚠️ WARNING**: Standard Sessions require `browser.disconnect()` - Playwright does NOT expose this method reliably. Use for Puppeteer only. For Playwright, consider state persistence via cookies/localStorage manually.

**Timeout limits by plan**:
- Free: 10 seconds
- Prototyping (15k-100k): 30 seconds
- Starter (180k): 60 seconds
- Scale (500k+): 5 minutes
- Enterprise: Custom

**Max session duration**:
- Free: 1 minute
- Prototyping (20k): 15 minutes
- Starter (180k): 30 minutes
- Scale (500k+): 60 minutes

#### 9. Screenshots & PDFs

**Screenshot via CDP**:
```python
await page.screenshot(path='screenshot.png', full_page=True)
# Or base64
screenshot_bytes = await page.screenshot()
import base64
screenshot_base64 = base64.b64encode(screenshot_bytes).decode()
```

**Screenshot via REST API** (no Playwright needed):
```python
import requests
response = requests.post(
    'https://production-sfo.browserless.io/screenshot?token=YOUR_TOKEN',
    json={
        'url': 'https://example.com',
        'options': {
            'fullPage': True,
            'format': 'png',
            'viewport': {'width': 1920, 'height': 1080}
        }
    }
)
with open('screenshot.png', 'wb') as f:
    f.write(response.content)
```

**PDF via REST API**:
```python
response = requests.post(
    'https://production-sfo.browserless.io/pdf?token=YOUR_TOKEN',
    json={
        'url': 'https://example.com',
        'options': {
            'printBackground': True,
            'landscape': False,
            'format': 'A4'
        }
    }
)
with open('output.pdf', 'wb') as f:
    f.write(response.content)
```

#### 10. Error Handling & Retry Patterns

**Common errors and solutions**:

| Error Code | Cause | Solution |
|------------|-------|----------|
| 400 Bad Request | Invalid JSON, timeout too high, conflicting params | Validate payload, check timeout limits |
| 401 Unauthorized | Missing/invalid token, or endpoint not supported by plan | Verify token, upgrade plan if needed |
| 403 Forbidden | Wrong regional endpoint, insufficient permissions | Use correct region for your account |
| 404 Not Found | Endpoint doesn't exist | Check URL spelling |
| 408 Request Timeout | Timeout too low, waiting for non-existent selector | Increase timeout, verify selectors |
| 429 Too Many Requests | Exceeded concurrency limit (unclosed sessions) | Close browser in finally blocks |

**Retry pattern**:
```python
async def with_retry(operation, max_retries: int = 3, delay: int = 5):
    """Retry operation with exponential backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            return await operation()
        except Exception as e:
            if attempt == max_retries:
                raise
            wait_time = delay * attempt
            print(f"[WARN] Attempt {attempt} failed: {e}. Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
```

**Concurrency limits by plan**:
- Free: 2 concurrent (monthly), 2 (yearly)
- Prototyping: 5 concurrent (monthly), 10 (yearly)
- Starter: 30 concurrent (monthly), 40 (yearly)
- Scale: 80 concurrent (monthly), 100 (yearly)
- Enterprise: Custom

#### 11. Best Practices

✅ **DO**:
- Use environment variables: `BROWSERLESS_API_TOKEN`
- Always `await browser.close()` in finally blocks
- Call nearest regional endpoint (reduce latency)
- Wrap multiple operations in `page.evaluate()` to reduce round-trips
- Use `waitUntil` appropriately: `domcontentloaded` (fast), `networkidle` (thorough)
- Set viewport: `1920x1080` or device-specific
- Implement retry logic with multiple tokens
- Monitor your dashboard for usage patterns
- Take screenshots on errors: `await page.screenshot(path='error.png')`
- Use `playwright-core` in production (smaller bundle)

❌ **DON'T**:
- Hardcode API tokens
- Forget to close browser (leaks resources, hits concurrency limit)
- Use `networkidle` on busy pages (unnecessary timeouts)
- Create multiple contexts when default context suffices (CDP mode limitation)
- Use low timeouts (< 30 seconds)
- Ignore network errors (always retry)

**Reduce network round-trips**:
```python
# BAD - multiple round-trips
button = await page.$('.buy-now')
text = await button.text_content()
visible = await button.is_visible()
await button.click()

# GOOD - single round-trip
result = await page.evaluate('''() => {
    const btn = document.querySelector('.buy-now');
    return {
        text: btn.innerText,
        visible: btn.offsetParent !== null,
        clicked: (function(){ btn.click(); return true; })()
    };
}''')
```

#### 12. Launch Options & Query Parameters

Common parameters for connection URL:
- `token` - Your API token (required)
- `timeout` - Session timeout in ms (default varies by plan)
- `proxy` - `residential` to enable built-in proxy
- `proxyCountry` - ISO country code (us, de, uk, etc.)
- `proxyCity` - City name (Scale plan only)
- `proxySticky` - `true` to keep same proxy IP
- `proxyLocaleMatch` - `1` to auto-set browser locale to match proxy
- `externalProxyServer` - External proxy URL
- `--proxy-server` - Chrome flag for proxy
- `blockAds` - `true` to block ads
- `stealth` - Use stealth routes (better: use /stealth path)

See full list: https://docs.browserless.io/baas/launch-options

#### 13. Common Questions Archive

**Q: Файлы не загружаются в Browserless - почему?**
**A**: Локальные пути недоступны! Нужно либо:
1. Загрузить через base64 + DataTransfer (RECOMMENDED):
   ```python
   with open('photo.jpg', 'rb') as f:
       content = base64.b64encode(f.read()).decode()
   await page.evaluate(...create_virtual_file..., {base64Data: content})
   ```
2. Использовать публичный URL:
   ```python
   await input.set_input_files('https://cloud.com/photo.jpg')
   ```

**Q: Сессии висят в Browserless Dashboard даже после закрытия скрипта**
**A**: Убедись что вызываешь `await browser.close()` в finally блоке. Также проверь что закрываются все контексты и страницы.

**Q: Как добавить proxy?**
**A**: Built-in residential:
```python
ws_endpoint = f"wss://production-sfo.browserless.io/?token={token}&proxy=residential&proxyCountry=us"
```

**Q: Таймауты на медленной сети**
**A**: Увеличь `timeout` параметр в URL до 300000+ ms. Также увеличь задержку между ретраями.

**Q: Какие типы браузеров доступны?**
**A**: Chromium (рекомендуется), Firefox, WebKit. Для Chrome native binary используй `/chrome` путь.

**Q: Session Viewer URL - что это?**
**A**: Browserless не имеет встроенного Live Debugger как Steel. Для дебага используй скриншоты и логирование.

**Q: Максимальный размер файла для загрузки?**
**A**: Ограничений на размер через base64 нет, но существуют лимиты на память и время выполнения. Рекомендуется < 50MB.

**Q: Browserless не подключается, что проверять?**
**A**:
1. Токен верный? (`echo $BROWSERLESS_API_TOKEN`)
2. Интернет есть? (`ping production-sfo.browserless.io`)
3. Правильный регион endpoint?
4. Браузер закрывается в finally?
5. Проверь Dashboard на ошибки
6. Убедись, что endpoint соответствует твоему плану (free=production-sfo, enterprise=custom)

**Q: connect vs connectOverCDP - что использовать?**
**A**: Для большинства задач используй `connectOverCDP` (поддерживает stealth, BQL, расширения). Используй `connect` когда нужен `page.route()`, `APIRequestContext`, или Firefox/WebKit.

**Q: Как загружать несколько файлов одновременно?**
**A**: Добавь несколько File объектов в DataTransfer:
```javascript
// В page.evaluate
const files = [file1, file2, file3].map(data => new File([b64ToUint8Array(data.base64)], data.name, {type: data.mime}));
const dataTransfer = new DataTransfer();
files.forEach(file => dataTransfer.items.add(file));
input.files = dataTransfer.files;
```

**Q: Как смотреть live-видео происходящего в браузере?**
**A**: Browserless не предоставляет live video streaming. Используй периодические скриншоты:
```python
for i in range(10):
    await page.screenshot(path=f'screenshot_{i:03d}.png')
    await asyncio.sleep(2)
```

### API Reference - Browserless

#### WebSocket Connection Patterns

**CDP Mode** (Py):
```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp(
        f'wss://production-sfo.browserless.io/?token={token}'
    )
    context = browser.contexts[0]  # Default context exists in CDP mode
    page = await context.new_page()
```

**Playwright Native**:
```python
browser = await playwright.chromium.connect(
    f'wss://production-sfo.browserless.io/chromium/playwright?token={token}'
)
page = await browser.new_page()
```

#### REST API Endpoints

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/content` | POST | Scrape HTML | `token` query |
| `/screenshot` | POST | Capture screenshot | `token` query |
| `/pdf` | POST | Generate PDF | `token` query |
| `/download` | POST | Download files | `token` query |
| `/function` | POST | Execute Puppeteer script | `token` query |
| `/unblock` | POST | Bypass bot detection | `token` query |
| `/bql` | POST | BrowserQL queries | `token` query |
| `/proxy/cities` | GET | List available cities | `token` query |

**Example - Content API**:
```python
import requests
resp = requests.post(
    'https://production-sfo.browserless.io/content?token=TOKEN',
    json={'url': 'https://example.com', 'waitFor': 5000}
)
html = resp.text
```

**Example - Screenshot API**:
```python
resp = requests.post(
    'https://production-sfo.browserless.io/screenshot?token=TOKEN',
    json={
        'url': 'https://example.com',
        'options': {
            'fullPage': True,
            'format': 'jpg',
            'quality': 80
        }
    }
)
with open('shot.jpg', 'wb') as f:
    f.write(resp.content)
```

**Example - Download API**:
```python
import requests
resp = requests.post(
    'https://production-sfo.browserless.io/download?token=TOKEN',
    json={
        'url': 'https://example.com/file.pdf',
        'waitFor': 5000
    }
)
# Returns base64 encoded file data
file_data = base64.b64decode(resp.json()['data'])
with open('file.pdf', 'wb') as f:
    f.write(file_data)
```

### Context Configuration Options

```python
context = await browser.new_context(
    viewport={'width': 1920, 'height': 1080},
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    locale='en-US',
    timezone_id='America/New_York',
    geolocation={'latitude': 40.7128, 'longitude': -74.0060},
    permissions=['geolocation'],
    color_scheme='light',
    device_scale_factor=1,
    ignore_https_errors=True,
    bypass_csp=True,
    # Proxy for third-party providers
    proxy={
        'server': 'http://proxy.example.com:8080',
        'username': 'user',  # optional
        'password': 'pass'   # optional
    }
)
```

### Use Cases Examples

#### Web Scraping with stealth
```python
token = os.getenv('BROWSERLESS_TOKEN')
ws = f"wss://production-sfo.browserless.io/stealth?token={token}&proxy=residential&proxyCountry=us"

async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp(ws)
    context = browser.contexts[0]
    page = await context.new_page()

    await page.goto('https://target-site.com', wait_until='networkidle')
    content = await page.content()
    screenshot = await page.screenshot(full_page=True)

    await browser.close()
```

#### Form Automation with file upload
```python
async def fill_and_submit(page, data: dict, photo_path: str = None):
    await page.fill('input[name="email"]', data['email'])
    await page.fill('input[name="password"]', data['password'])

    if photo_path:
        await upload_local_file(page, photo_path, 'input[name="photo"]')

    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')
```

#### CAPTCHA Handling
```python
async def solve_captcha_if_present(page, timeout: int = 120000):
    """Check for CAPTCHA and wait for resolution (stealth mode recommended)."""
    try:
        # Check for reCAPTCHA iframe
        captcha_frame = page.frame_locator('iframe[src*="captcha"]')
        if await captcha_frame.is_visible(timeout=5000):
            print("CAPTCHA detected, waiting for resolution...")
            # In stealth mode, Browserless may auto-solve
            await page.wait_for_selector(
                'iframe[src*="captcha"]',
                state='detached',
                timeout=timeout
            )
            print("CAPTCHA solved")
            return True
    except:
        pass
    return False
```

### Common Troubleshooting

#### Problem: Browser not launching
- Check token validity: `echo $BROWSERLESS_TOKEN`
- Verify internet: `ping production-sfo.browserless.io`
- Ensure `token` is in connection URL
- Check Dashboard for active sessions and errors
- Verify your plan supports the region/endpoint you're using

#### Problem: Files not uploading
- **DO NOT** use local paths directly: `/path/to/file.jpg` ❌
- Use base64 + DataTransfer method ✅
- Or use public URLs ✅
- Check file size (recommended < 50MB)
- Verify selector exists on page
- Ensure `change` event is dispatched

#### Problem: Sessions hanging in Dashboard
- Ensure `await browser.close()` is called in finally block
- Check that all contexts and pages are closed
- Monitor Dashboard for leaked sessions

#### Problem: Timeouts
Browserless has higher network latency than local.
- Increase `timeout` parameter in URL (300000+ ms)
- Increase delay between retries (10+ seconds)
- Use `wait_for_selector` instead of fixed waits where possible
- Use regional endpoint closest to your infrastructure

#### Problem: Using wrong mode (connect vs connectOverCDP)
- `connectOverCDP` returns browser with default context already exists
- Access it: `context = browser.contexts()[0]`
- `connect` returns browser without contexts, use: `page = await browser.new_page()`

### Limits & Pricing (Verify in docs!)
- **Max file size (upload)**: Recommended < 50MB (no hard limit but memory constraints)
- **Session duration**: 1-60 minutes depending on plan
- **Concurrent sessions**: plan-dependent (Free: 2, Scale: 80, Enterprise: custom)
- **Free tier**: Included credits monthly, sessions limited to 1 min each
- **Pay-per-use**: Credits consumed based on session duration and features
- **Upload speed**: ~10MB/s typical
- **Rate limit**: ~1000 requests/hour

**Always check https://docs.browserless.io/pricing for current rates**

### Feature Comparison: Steel.dev vs Browserless

| Feature | Steel.dev | Browserless.io |
|---------|-----------|----------------|
| Connection | CDP WebSocket | CDP WebSocket |
| File upload API | REST Files API | base64 + DataTransfer |
| Session persistence | session.release() | browser.disconnect() / reconnect |
| Live debugger | Yes (Session Viewer) | No (use screenshots) |
| Built-in proxy | Yes (`proxy` param) | Yes (`proxy=residential`) |
| Stealth mode | Via context options | Special `/stealth` endpoints |
| Session duration max | 60 min | 60 min (Scale+) |
| SDK | steel-sdk Python | No SDK (direct Playwright) |
| REST APIs | Limited | Extensive (PDF, Screenshot, Content, etc.) |

Both excellent; Browserless has richer REST API, Steel has simpler file uploads.

### Project-Specific Files (Current Implementation)
- `BROWSERLESS/browser.py` - `create_browserless_browser()` & `close_browserless_browser()`
- `BROWSERLESS/upload.py` - `upload_local_file()` - uses base64 + DataTransfer
- `BROWSERLESS/main.py` - main automation orchestration
- `config.json` - API token storage
- `memory/browserless_quick_reference.md` - quick reference

### Warning Flags
⚠️ **Critical**:
- Never use local file paths directly - always base64 + DataTransfer or public URLs
- Always close browser - causes resource leaks and concurrency limit hits
- Use finally blocks for cleanup - prevents hanging sessions
- Keep timeouts high - Browserless has network latency (min 30000 ms)
- Respect plan limits - session duration, concurrency

⚠️ **Common Pitfalls**:
- Forgetting to dispatch `change` event after file upload → site doesn't detect file
- Using `browser.new_context()` in CDP mode without understanding default context
- Not handling `await browser.close()` on errors → sessions accumulate
- Low timeouts → false timeout errors
- Single token → no redundancy, implement rotation
- Using wrong regional endpoint → 403 errors

### Installation & Setup

```bash
pip install playwright
playwright install chromium

# Optional: use playwright-core for smaller production deployments
pip install playwright-core
```

Set environment:
```bash
export BROWSERLESS_API_TOKEN="YOUR_TOKEN_HERE"
# optional: export BROWSERLESS_REGION="sfo"
```

### Browserless Modes
1. **CDP** (recommended) - `connect_over_cdp()` - Full Playwright control + extensions support
2. **Playwright Native** - `connect()` - Native Playwright protocol, supports all browsers
3. **Stealth CDP** - `/stealth` path - Hardened browser for bot detection
4. **REST APIs** - HTTP endpoints - No Playwright required, simple API calls

### Version Info
- playwright: latest or >= 1.40.0
- Documentation: https://docs.browserless.io/
- GitHub: https://github.com/browserless/browserless
- Community: https://github.com/browserless/browserless/discussions

---

Last updated: 2026-03-30
Agent: browserless-expert
Project: 3DHunyuan
