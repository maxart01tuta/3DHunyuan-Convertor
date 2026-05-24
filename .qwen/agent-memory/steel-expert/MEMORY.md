# Steel-Expert Agent Persistent Memory

## Active Memories

### Project Configuration
- **Mode**: CDP (Chrome DevTools Protocol) with Steel SDK session management
- **Steel SDK**: python package `steel-sdk` installed in BROWSER-STEEL/venv (version >= 0.17.0)
- **API Keys**: Stored in `config.json` → `API_LIST` array (never hardcode!)
- **Timeout**: `MAX_WAIT = 300000` ms (5 minutes) - Steel has higher network latency
- **Retry**: 3 attempts per API key, random key selection, `API_TIME = 5` sec between attempts
- **Session cleanup**: Always `client.sessions.release(session.id)` in finally block (prevents leaks)
- **Browser type**: chromium only (project-specific)
- **Installation**: `pip install steel-sdk playwright openpyxl` + `playwright install chromium`
- **Current migration**: Switching from local Playwright to Steel.dev (March 2026) - see `project_migration_steel.md`

### Active Migration: Browser → Steel.dev
- [Project Migration Plan](project_migration_steel.md) - Complete migration guide for 3DHunyuan automation
- Replacing `browser.py` `launch_browser()` with `create_steel_browser_with_retry()`
- Updating upload functions to use Files API + CDP
- Config changes: add `API_LIST` to `config.py`


### Critical Patterns - MUST KNOW

#### 1. File Uploads (THE MOST IMPORTANT!)
**Problem**: Steel browser runs on Steel servers, NOT on your local machine.
Local paths (`/home/user/photo.jpg`) are INACCESSIBLE in remote browser.

**Solution A: Steel Files API** (for private/local files)
```python
from steel import Steel

# 1. Upload file to Steel server
with open('photo.jpg', 'rb') as f:
    session_file = await client.sessions.files.upload(
        session.id,  # your Steel session ID
        file=f
    )
# session_file.path returns path inside Steel: '/sessions/xxx/files/photo.jpg'

# 2. Set input using Steel file path
await page.locator('input[type="file"]').set_input_files(session_file.path)
```

**Solution B: Public URL** (if file already in cloud)
```python
# Playwright/CDP will download the file from URL
await page.locator('input[type="file"]').set_input_files(
    'https://example.com/photos/photo.jpg'
)
```

**Project-specific index pattern** (from upload.py):
- Index 2: first photo (`baza_photo_1`)
- Index 6: second photo (`baza_photo_2`)
- Index 1: third photo (`baza_photo_3`, optional)

#### 2. CDP Connection (Project's Main Mode)
```python
from steel import Steel
from playwright.async_api import async_playwright
import random
import asyncio

async def create_steel_browser(api_list: list, api_time: int = 5):
    """Create Steel browser with retry logic."""
    max_attempts = len(api_list) * 3

    for attempt in range(max_attempts):
        api_key = random.choice(api_list)
        try:
            print(f"[INFO] Attempt {attempt + 1}: connecting to Steel")

            # 1. Create Steel client & session
            client = Steel(steel_api_key=api_key)
            session = client.sessions.create()

            # 2. Start Playwright
            playwright = await async_playwright().start()

            # 3. Connect via CDP - sessionId is MANDATORY!
            browser = await playwright.chromium.connect_over_cdp(
                f'wss://connect.steel.dev?apiKey={api_key}&sessionId={session.id}'
            )

            # 4. Create context & page
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()

            print(f"[SUCCESS] Session created: {session.id}")
            print(f"[INFO] Viewer URL: {session.session_viewer_url}")

            return {
                'client': client,
                'session': session,
                'playwright': playwright,
                'browser': browser,
                'context': context,
                'page': page
            }

        except Exception as e:
            print(f"[ERROR] Failed with API {api_key[:10]}...: {e}")
            await asyncio.sleep(api_time)

    raise Exception("All API keys exhausted")
```

#### 3. Proper Cleanup (AVOID SESSION LEAKS!)
```python
async def close_steel_browser(resources: dict):
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
        # CRITICAL: Release Steel session to prevent leaks!
        if resources.get('client') and resources.get('session'):
            resources['client'].sessions.release(resources['session'].id)
            print(f"Session {resources['session'].id} released")
    except Exception as e:
        print(f"[ERROR] Cleanup error: {e}")
```

**Cleanup order** (must be reverse of creation):
1. page.close()
2. context.close()
3. browser.close()
4. playwright.stop()
5. client.sessions.release(session.id)

#### 4. Configuration
Project uses `config.json`:
```json
{
  "perekluchatel": 1,
  "MAX_WAIT": 300000,
  "API_TIME": 5,
  "API_LIST": [
    "ste-xxxxxxxxxxxxxxxx",
    "ste-yyyyyyyyyyyyyyyy"
  ],
  "PHOTO_BASE_URL": null
}
```

#### 5. Error Handling Patterns
- **"检测失败"**: Photo recognition failed, retry upload (see upload.py:86-96)
- **Timeouts**: Increase `MAX_WAIT` to 600000 for slow networks
- **Connection failures**: Retry logic handles it, check API key validity
- **Session leaks**: Monitor Steel Dashboard, ensure `release()` is called

### API Reference - Steel Python SDK

#### Steel Client
```python
from steel import Steel

client = Steel(steel_api_key="ste-...")

# Sessions
session = client.sessions.create()                    # Create new session
client.sessions.release(session.id)                   # Delete/close session
sessions = client.sessions.list()                     # List active sessions
viewer_url = session.session_viewer_url               # Live debug URL

# Files
session_file = await client.sessions.files.upload(
    session.id,
    file=open('photo.jpg', 'rb')
)  # Returns: .path, .size, .filename
await client.sessions.files.delete(
    session.id,
    session_file.path
)  # Delete file from Steel

# Screenshots
screenshot_bytes = await client.sessions.screenshot.capture(
    session.id,
    format='png',
    full_page=True
)

# PDFs
pdf_bytes = await client.sessions.pdf.generate(session.id)
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
    ignore_https_errors=True,
    bypass_csp=True,
    proxy={
        'server': 'us-proxy.steel.dev:80',
        'bypass': 'localhost'
    }
)
```

### Use Cases Examples

#### Web Scraping
```python
page = await context.new_page()
await page.goto('https://target-site.com', wait_until='networkidle')
content = await page.content()
screenshot = await page.screenshot(path='screenshot.png')
```

#### Form Automation
```python
await page.fill('input[name="email"]', 'test@example.com')
await page.fill('input[name="password"]', 'password123')
await page.click('button[type="submit"]')
await page.wait_for_navigation()
```

#### CAPTCHA Handling
```python
async def solve_captcha_if_present(page, timeout: int = 120000):
    """Check for CAPTCHA and wait for resolution."""
    try:
        captcha_frame = page.frame_locator('iframe[src*="captcha"]')
        if await captcha_frame.is_visible(timeout=5000):
            print("CAPTCHA detected, waiting for resolution...")
            # Steel may auto-solve if configured
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
- Check API key validity: `echo $STEEL_API_KEY`
- Verify internet: `ping connect.steel.dev`
- Ensure `sessionId` is in CDP URL
- Check Steel Dashboard for active sessions

#### Problem: Files not uploading
- **DO NOT use local paths**: `/path/to/file.jpg` ❌
- Use Files API or public URLs ✅
- Check file size (< 100MB limit)
- Verify session is active

#### Problem: Sessions hanging in Dashboard
- Ensure `client.sessions.release(session.id)` is called in finally block
- Check that `browser.close()` executes (requires both)
- Monitor Steel Dashboard for leaks

#### Problem: Timeouts
Steel has higher network latency than local.
- Increase `MAX_WAIT` to `600000` (10 minutes)
- Increase `API_TIME` to `10` seconds between retries
- Use `wait_for_selector` instead of `wait_for_timeout` where possible

### Limits & Pricing (Verify in docs!)
- **Max file size**: 100MB
- **Session duration**: 1-60 minutes (depends on plan)
- **Free tier**: ~10 sessions/month, up to 1 minute each
- **Pay-per-use**: ~$0.05-0.15 per browser minute
- **Concurrent sessions**: plan-dependent
- **Upload speed**: ~10MB/s
- **API rate limit**: ~1000 requests/hour

**Always check https://docs.steel.dev/pricing for current rates**

### Best Practices
✅ DO:
- Use environment variables for API keys: `os.getenv('STEEL_API_KEY')`
- Implement retry logic with multiple API keys
- Call `session.release()` in finally blocks
- Monitor Steel Dashboard for anomalies
- Use `session.session_viewer_url` for debugging
- Take screenshots on errors: `await page.screenshot(path='error.png')`
- Keep timeouts high (300000+ ms)
- Validate file existence before upload
- Use random API key selection for load balancing

❌ DON'T:
- Hardcode API keys in source code
- Forget to release sessions (causes leaks & billing)
- Use local file paths with `set_input_files()`
- Set low timeouts (< 30 seconds)
- Ignore network errors (always retry)
- Share Session Viewer URLs (contain session info)

### Modes Comparison

| Feature | Local Playwright | Steel.dev |
|---------|-----------------|-----------|
| Browser install | Required (`playwright install`) | Managed in cloud |
| Proxy handling | Manual setup | Built-in rotation |
| Fingerprinting | Your real browser | Anonymized |
| Scaling | Limited by hardware | Nearly unlimited |
| Cost | Free | Pay-per-use |
| Speed | Fast (local) | Medium (network latency) |
| Geo-targeting | No | Yes (proxy zones) |
| CAPTCHA | External services | Built-in integrations |
| CI/CD | Possible but complex | Ideal |

**Use Steel when**: scaling needed, geo-targeting, IP rotation, CI/CD
**Use local when**: maximum speed critical, cost sensitive, minimal latency

### Debug & Monitoring

#### Enable Debug Logging
```bash
export STEEL_DEBUG=true
```

#### Session Viewer URL
```python
print(f"Watch live: {session.session_viewer_url}")
# Opens browser to see exactly what's happening
```

#### Check Active Sessions
```python
sessions = client.sessions.list()
for s in sessions:
    print(f"{s.id} | {s.status} | {s.created_at}")
```

### Installation & Setup
```bash
pip install steel-sdk playwright openpyxl
playwright install chromium
```

Set environment:
```bash
export STEEL_API_KEY="ste-xxxxxxxxxxxxxxxx"
# optional: export STEEL_API_URL="https://api.steel.dev"
```

### Steel Modes
1. **CDP + Steel SDK** (project uses) - Full Playwright control + session management
2. **Native Steel SDK** - High-level Steel API only
3. **Steel Playwright** (TypeScript) - `@steel-dev/playwright` npm package

### CDP URL Format (CRITICAL)
```
wss://connect.steel.dev?apiKey={YOUR_API_KEY}&sessionId={SESSION_ID}
```
- `sessionId` is obtained from `client.sessions.create()`
- Both parameters required
- WebSocket secure connection

### Common Questions Archive

#### Q: Файлы не загружаются в Steel - почему?
**A**: Локальные пути недоступны! Нужно либо:
1. Загрузить через Files API:
   ```python
   with open('photo.jpg', 'rb') as f:
       session_file = await client.sessions.files.upload(session.id, file=f)
   await input.set_input_files(session_file.path)
   ```
2. Использовать публичный URL:
   ```python
   await input.set_input_files('https://cloud.com/photo.jpg')
   ```

#### Q: Сессии висят в Steel Dashboard даже после закрытия скрипта
**A**: Убедись что вызываешь `client.sessions.release(session.id)` в finally блоке. Также проверь что `browser.close()` вызывается. Оба обязательны!

#### Q: Как добавить proxy?
**A**: Steel provides built-in proxies:
```python
context = await browser.new_context(
    proxy={'server': 'us-proxy.steel.dev:80'}
)
# Or use regional: 'eu-proxy.steel.dev', 'asia-proxy.steel.dev'
```

#### Q: Таймауты на медленной сети
**A**: Увеличь `MAX_WAIT` до 600000 (10 минут) и `API_TIME` до 10 секунд между попытками. Steel имеет большую сетевую задержку чем локальный браузер.

#### Q: Какие типы браузеров доступны?
**A**: `chromium` (рекомендуется), `firefox`, `webkit`. Проект использует только chromium.

#### Q: Session Viewer URL - что это?
**A**: Это URL для live-просмотра того, что происходит в браузере. Полезно для дебага: `session.session_viewer_url`

#### Q: Максимальный размер файла?
**A**: 100MB. Большие файлы будут отклонены.

#### Q: Steel не подключается, что проверять?
**A**:
1. API ключ верный? (`echo $STEEL_API_KEY`)
2. Интернет есть? (`ping connect.steel.dev`)
3. В CDP URL есть `sessionId`?
4. Сессии освобождаются в finally?
5. Проверь Steel Dashboard на наличие ошибок

### Project-Specific Files (Current Implementation)
- `BROWSER-STEEL/browser.py` - `create_steel_browser()` & `close_steel_browser()`
- `BROWSER-STEEL/upload.py` - `upload_photo_with_check()` - uses Files API + retry
- `BROWSER-STEEL/main.py` - `process_row()` orchestrates text/photo modes
- `docs/STEEL-EXPERT-AGENT-SETUP.md` - agent setup documentation
- More docs in `docs/`: Steel-Connect-with-Playwright-Python.html, Steel-Files-Upload.html, etc.

### Warning Flags
⚠️ **Critical**:
- Never use local file paths - always Files API or public URLs
- Always release sessions - causes billing & dashboard clutter
- Use finally blocks for cleanup - prevents resource leaks
- Keep timeouts high - Steel is slower than local

⚠️ **Common Pitfalls**:
- Forgetting `sessionId` in CDP URL → connection fails
- Not handling `sameSite` cookie issues → auth problems
- Low `MAX_WAIT` → false timeout errors
- Single API key → no redundancy, implement rotation

---

## To-Do / Enhancements

- [ ] Integrate steel-sdk version check (>= 0.17.0)
- [ ] Add screenshot-on-error in process_row
- [ ] Implement session pooling for reuse
- [ ] Add metrics: session duration, bytes uploaded, retry count
- [ ] Consider Steel's built-in stealth mode if facing bot detection
- [ ] Document all index offsets for file uploads (project-specific quirk)

---

## Version Info
- steel-sdk: >= 0.17.0 (check with `pip show steel-sdk`)
- playwright: latest (keep updated)
- Documentation: https://docs.steel.dev/
- GitHub: https://github.com/steel-dev/steel-sdk-python

---

Last updated: 2026-03-27
Agent: steel-expert
Project: 3DHunyuan

### Common Questions Archive

#### Q: Файлы не загружаются в Steel - почему?
**A**: Локальные пути недоступны! Нужно либо:
1. Загрузить через Files API: `session_file = await client.sessions.files.upload(session.id, file=f)`
2. Использовать публичный URL: `set_input_files('https://...')`

#### Q: Сессии висят в Steel Dashboard даже после закрытия скрипта
**A**: Убедись что вызываешь `client.sessions.release(session.id)` в finally блоке. Также проверь что `browser.close()` вызывается (June 2024 incident: need both).

#### Q: Как добавить proxy?
**A**: Используй Steel proxy: `await browser.new_context(proxy={'server': 'us-proxy.steel.dev:80'})`. Или используй региональные прокси.

#### Q: Таймауты на медленной сети
**A**: Увеличь `MAX_WAIT` до 600000 (10 минут) и `API_TIME` до 10 секунд между попытками.

#### Q: Какие есть browser types?
**A**: `chromium` (main), `firefox`, `webkit`. Проект использует только chromium.

---

## To-Do / Enhancements

- [ ] Integrate steel-sdk version check (>= 0.17.0)
- [ ] Add screenshot-on-error in process_row
- [ ] Implement session pooling for reuse
- [ ] Add metrics: session duration, bytes uploaded, retry count
- [ ] Consider Steel's built-in stealth mode if facing bot detection

---

Last updated: 2026-03-27
Agent: steel-expert
Project: 3DHunyuan
