# Common Questions & Answers

## Q: Как загрузить локальный файл в Browserless?

**A**: Локальные пути недоступны в удаленном браузере! Используйте base64 + DataTransfer:

```python
import base64

async def upload_file(page, file_path: str, selector: str = 'input[type="file"]'):
    with open(file_path, 'rb') as f:
        base64_data = base64.b64encode(f.read()).decode('utf-8')

    await page.evaluate(
        '''({selector, name, type, base64}) => {
            function b64ToUint8Array(b64) {
                const binary = atob(b64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                return bytes;
            }
            const input = document.querySelector(selector);
            const file = new File([b64ToUint8Array(base64)], name, { type });
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }''',
        {
            'selector': selector,
            'name': Path(file_path).name,
            'type': 'image/jpeg',
            'base64': base64_data
        }
    )

await upload_file(page, 'photo.jpg', 'input[name="photo"]')
```

**See**: `file_upload_recipes.md`, `base64_handling.md`

---

## Q: Как загрузить фото с локального ПК в браузер Browserless через base64?

**A**: Полностью покрыто в ответе выше. Ключевые шаги:

1. Прочитать файл в Python: `f.read()`
2. Закодировать в base64: `base64.b64encode(data).decode('utf-8')`
3. Передать в `page.evaluate()`
4. Внутри браузера:
   - Декодировать base64 → Uint8Array через `atob()`
   - Создать `new File([uint8array], filename, {type: mime})`
   - Добавить в `DataTransfer`
   - Установить `input.files = dataTransfer.files`
   - Dipatch `change` event

Полный код см. в `base64_handling.md`

---

## Q: Как подключить Browserless к Python Playwright?

**A**: Используйте `connect_over_cdp()`:

```python
from playwright.async_api import async_playwright

async def main():
    token = os.getenv('BROWSERLESS_TOKEN')
    ws = f"wss://production-sfo.browserless.io/?token={token}"

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws)
        context = browser.contexts[0]  # Default context exists
        page = await context.new_page()

        await page.goto('https://example.com')
        print(await page.title())

        await browser.close()

asyncio.run(main())
```

**Note**: Use `browser.contexts[0]` for CDP mode (default context). Use `browser.new_context()` for Playwright-native mode with `/chromium/playwright` endpoint.

---

## Q: Какие эндпоинты Browserless существуют?

**A**:

| Эндпоинт | Назначение |
|----------|------------|
| `/` или `/chromium` | CDP подключение (основной) |
| `/stealth` | Stealth режим с anti-detection |
| `/chromium/playwright` | Playwright native режим |
| `/screenshot` | REST API для скриншотов |
| `/pdf` | REST API для PDF |
| `/content` | REST API для скрапинга HTML |
| `/download` | REST API для загрузки файлов |
| `/function` | REST API для кастомного Puppeteer JS |
| `/unblock` | REST API для обхода защиты |
| `/chromium/bql` | BrowserQL GraphQL API |

---

## Q: В чем разница между connect() и connectOverCDP()?

**A**:

| Feature | connect() (Native) | connectOverCDP() |
|---------|-------------------|------------------|
| Path | `/chromium/playwright` | `/chromium` |
| Protocol | Playwright native | Chrome DevTools Protocol |
| Browser support | Chromium, Firefox, WebKit | Chromium only |
| Extensions | Not supported | Supported |
| BQL | Not supported | Supported |
| Captcha solving | Not supported | Supported |
| page.route() | ✅ Supported | ❌ Not supported |
| APIRequestContext | ✅ Supported | ❌ Not supported |
| Proxy in context | ✅ Works | ⚠️ Limited |
| Connection overhead | Lower | Higher |

**Recommendation**: Use `connectOverCDP()` for most Browserless tasks (stealth, BQL, extensions needed). Use `connect()` only if you need `page.route()` or Firefox/WebKit.

---

## Q: Как добавить прокси?

**A**: Есть 2 варианта:

### 1. Built-in Residential Proxy (Browserless)
```python
ws = f"wss://production-sfo.browserless.io/?token={token}&proxy=residential&proxyCountry=us"
```

### 2. Third-party Proxy
```python
from urllib.parse import quote
proxy = "http://user:pass@proxy.example.com:8080"
encoded = quote(proxy)
ws = f"wss://production-sfo.browserless.io/?token={token}&externalProxyServer={encoded}"
```

**See**: `proxy_configuration.md`

---

## Q: Как решать CAPTCHA?

**A**: Есть несколько подходов:

1. **Stealth mode** - позволяет избежать многих CAPTCHA:
```python
ws = f"wss://production-sfo.browserless.io/stealth?token={token}"
```

2. **BrowserQL с solve** - автоматическое решение:
```python
query = '''
mutation {
  goto(url: "https://example.com", waitUntil: networkIdle) { status }
  solve(type: cloudflare) { solved }
  reconnect(timeout: 30000) { browserWSEndpoint }
}
'''
# После reconnect подключиcь Playwright
```

3. **Manual** - ждем пока решат вручную:
```python
await page.goto(url)
# manually solve in browser if you can see it
# or integrate with 3rd party solver service
```

---

## Q: Как установить User-Agent?

**A**: Через `new_context()`:

```python
context = await browser.new_context(
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
)
```

**Or** via CDP:
```python
cdp = await page.context.new_cdp_session(page)
await cdp.send('Network.setUserAgentOverride', {
    'userAgent': 'Custom UA String'
})
```

---

## Q: Что делать при "429 Too Many Requests"?

**A**:

1. Проверь concurrency limit в Dashboard
2. Закрывай браузеры в finally
3. Реализуй rate limiting:

```python
class RateLimiter:
    def __init__(self, max_per_second: float):
        self.rate = max_per_second
        self.last = time.time()

    async def wait(self):
        elapsed = time.time() - self.last
        wait = max(0, 1/self.rate - elapsed)
        if wait > 0:
            await asyncio.sleep(wait)
        self.last = time.time()
```

4. Используй token rotation
5. Appscale план если нужно больше concurrent

---

## Q: Как проверить что proxy работает?

**A**: Используй IP API:

```python
async def check_proxy(page):
    await page.goto('https://ip-api.com/json/')
    data = await page.evaluate('() => JSON.parse(document.body.textContent)')
    print(f"IP: {data['query']}, Country: {data['country']}")
    return data
```

Если IP отличается от твоего реального - proxy работает.

---

## Q: Session Viewer URL есть в Browserless?

**A**: Нет, в Browserless нет аналога Session Viewer от Steel. Для дебага используй:
- `await page.screenshot(path='debug.png')`
- Логирование в консоль
- `await page.content()` для сохранения HTML
- Console messages: `page.on('console', lambda msg: print(msg.text))`

---

## Q: Можно ли сохранять куки между сессиями?

**A**: Да, через сохранение/восстановление состояния:

```python
# Сохрани
cookies = await page.context.cookies()
local_storage = await page.evaluate('() => Object.fromEntries(Object.entries(localStorage))')

state = {'cookies': cookies, 'localStorage': local_storage}

# Восстанови (в новой сессии)
await context.add_cookies(state['cookies'])
await page.goto(url)
await page.evaluate('''(storage) => {
    Object.entries(storage).forEach(([k,v]) => localStorage.setItem(k,v));
}''', state['localStorage'])
```

---

## Q: Какой максимальный размер файла можно загрузить?

**A**: Официально нет hard limit, но рекомендации:
- < 50MB для надежности
- Большие файлы (>100MB) могут вызвать OOM
- Учитывай base64 overhead (+33%)

---

## Q: Как использовать REST API вместо Playwright?

**A**: Проще чем кажется:

```python
import requests

# Скриншот
resp = requests.post(
    'https://production-sfo.browserless.io/screenshot?token=TOKEN',
    json={'url': 'https://example.com', 'options': {'fullPage': True}}
)
with open('shot.png', 'wb') as f:
    f.write(resp.content)

# PDF
resp = requests.post(
    'https://production-sfo.browserless.io/pdf?token=TOKEN',
    json={'url': 'https://example.com'}
)
with open('page.pdf', 'wb') as f:
    f.write(resp.content)

# HTML
resp = requests.post(
    'https://production-sfo.browserless.io/content?token=TOKEN',
    json={'url': 'https://example.com'}
)
html = resp.text
```

---

## Q: Какой plan выбрать?

**A**:

| Need | Plan |
|------|------|
| Testing, prototyping | Free (100 sessions/month) |
| Regular automation, ~10k sessions/month | Prototyping ($15-49) |
| Production, moderate usage | Starter ($99-299) |
| High-volume, enterprise features | Scale ($499-2000) |
| Custom requirements, on-premise | Enterprise |

**Check current pricing**: https://www.browserless.io/pricing

---

## Q: Как сделать скриншот whole page?

**A**:

```python
# Via Playwright
await page.screenshot(path='full.png', full_page=True)

# Via REST API
requests.post(
    'https://.../screenshot?token=TOKEN',
    json={'url': url, 'options': {'fullPage': True}}
)
```

---

## Q: Почему я вижу "Just a moment..." или "Checking your browser"?

**A**: Site использует bot detection (Cloudflare, DataDome, PerimeterX).

**Решения в порядке предпочтения**:

1. **Stealth mode**:
```python
ws = f"wss://production-sfo.browserless.io/stealth?token={token}"
```

2. **Stealth + Proxy**:
```python
ws = f"wss://production-sfo.browserless.io/stealth?token={token}&proxy=residential&proxyCountry=us"
```

3. **BrowserQL unblock**:
```python
query = '''
mutation {
  goto(url: "https://site.com", waitUntil: networkIdle) { status }
  unblock(strategy: aggressive) { success }
}
'''
```

4. **Increase wait times**:
```python
await page.goto(url, wait_until='networkidle', timeout=120000)
await page.wait_for_timeout(10000)  # Дать время на решение CAPTCHA
```

---

## Q: Можно ли использовать Firefox/WebKit?

**A**: Да, но через Playwright-native режим, не CDP:

```python
# Не работает с CDP, только с /playwright endpoint
ws = f"wss://production-sfo.browserless.io/firefox/playwright?token={token}"
browser = await playwright.firefox.connect(ws)

# Или WebKit
ws = f"wss://production-sfo.browserless.io/webkit/playwright?token={token}"
browser = await playwright.webkit.connect(ws)
```

**Note**: Stealth mode, BQL, extensions недоступны для non-Chromium browsers.

---

## Q: Как получить console.log из страницы?

**A**:

```python
async def capture_console_logs(page):
    logs = []
    page.on('console', lambda msg: logs.append({
        'type': msg.type,
        'text': msg.text,
        'location': msg.location
    }))

    # ... browse ...

    return logs

logs = await capture_console_logs(page)
for log in logs:
    print(f"{log['type']}: {log['text']}")
```

---

## Q: Как отключить WebRTC (чтобы избежать утечки IP)?

**A**: Добавь флаг `--disable-webrtc` в URL:

```python
ws = f"wss://production-sfo.browserless.io/?token={token}&--disable-webrtc"
```

Или используй stealth режим который включает это автоматически.

---

## Q: Что лучше: CDP или REST API?

**A**:

| Scenario | Recommendation |
|----------|----------------|
| Простой скриншот/PDF одной страницы | REST API (проще, быстрее) |
| Сложная автоматизация, клики, формы | CDP + Playwright |
| Высоконагруженное сохранение HTML | REST API (экономия ресурсов) |
| Необходимость расширений | CDP с stealth |
| Обход защиты | CDP с stealth или BQL |
| Постоянное выполнение скриптов | CDP (полный контроль) |

---

## Q: Как изменить viewport?

**A**:

```python
context = await browser.new_context(
    viewport={'width': 1920, 'height': 1080}
)

# Или конкретные размеры
context = await browser.new_context(
    viewport={'width': 375, 'height': 812}  # iPhone X
)
```

---

## Q: Browserless бесплатный?

**A**: У Browserless есть бесплатный план:
- 100 сессий в месяц
- Concurrent: 2
- Session duration: 1 minute max

Для production нужен paid план. См. https://www.browserless.io/pricing

---

## Q: Как увеличить таймаут сессии?

**A**: Через параметр `timeout` в URL:

```python
# 10 минут
ws = f"wss://production-sfo.browserless.io/?token={token}&timeout=600000"
```

**Важно**: timeout не может превышать макс. лимит твоего плана:
- Free: 10000ms (10 sec)
- Prototyping: 30000ms (30 sec)
- Starter: 60000ms (1 min)
- Scale: 300000ms (5 min)

---

## Q: Как проверить активные сессии?

**A**: Через Dashboard: https://dashboard.browserless.io/sessions

Прямого API для листинга сессий нет (в отличие от Steel.dev).

---

## Q: Можно ли использовать Browserless в Docker?

**A**: Да:

```dockerfile
FROM python:3.11
RUN pip install playwright
RUN playwright install chromium
COPY . /app
WORKDIR /app
CMD ["python", "bot.py"]
```

Внутри контейнера переменная `BROWSERLESS_TOKEN` должна быть установлена.

---

## Q: Какой размер поддержки browsers?

**A**: Рекомендуется:
- Chromium: default, full support
- Firefox: через `/firefox/playwright`
- WebKit: через `/webkit/playwright`

---

## Q: Лучший регион для России?

**A**: Рекомендуется `production-ams.browserless.io` (Amsterdam) для минимальной задержки. Но проверь сам через benchmark:

```python
# Test latency to each region
import subprocess
for region in ['sfo', 'lon', 'ams']:
    subprocess.run(['ping', f'production-{region}.browserless.io'])
```

---

## Q: Как сохранять видео записи сессии?

**A**: Browserless не поддерживает видеозапись в реальном времени. Используй скриншоты на регулярных интервалах:

```python
import asyncio

async def record_session_via_screenshots(page, output_dir: str, interval: float = 1.0):
    """Create video-like sequence of screenshots."""
    Path(output_dir).mkdir(exist_ok=True)
    frame = 0
    while True:
        screenshot = await page.screenshot()
        path = Path(output_dir) / f"frame_{frame:06d}.png"
        with open(path, 'wb') as f:
            f.write(screenshot)
        frame += 1
        await asyncio.sleep(interval)
```

Для настоящего видео используй внешний сервис или self-hosted решение.

---

## Q: Какая версия Chromium используется?

**A**: Browserless регулярно обновляет. Проверь текущую версию:

```python
async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp(ws)
    version = await browser.version()
    print(f"Browser version: {version}")
    await browser.close()
```

Или смотри на статусной странице: https://status.browserless.io/

---

## See Also

- Full Q&A archive: https://docs.browserless.io/baas/troubleshooting
- Community: https://github.com/browserless/browserless/discussions
- Discord: https://discord.browserless.io/
