# Playwright Connection to Hyperbrowser

## Connection Pattern (Standard)

```python
from playwright.async_api import async_playwright
from hyperbrowser import AsyncHyperbrowser
import asyncio
import os

client = AsyncHyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))

async def main():
    session = await client.sessions.create()

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(session.ws_endpoint)
            context = browser.contexts[0]
            page = context.pages[0]

            await page.goto("https://example.com", wait_until="domcontentloaded")
            print(f"Page title: {await page.title()}")
            # Do your automation tasks here

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        await client.sessions.stop(session.id)

asyncio.run(main())
```

## Sync Version

```python
from playwright.sync_api import sync_playwright
from hyperbrowser import Hyperbrowser

client = Hyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))

def main():
    session = client.sessions.create()
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(session.ws_endpoint)

            # Get default context and page
            default_context = browser.contexts[0]
            page = default_context.pages[0]

            page.goto("https://example.com")
            print(page.title())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.sessions.stop(session.id)

if __name__ == "__main__":
    main()
```

## Creating New Pages (Tabs)

```python
context = browser.contexts[0]
page = await context.new_page()
await page.goto("https://3d.hunyuan.tencent.com/")
```

## Custom Context with Settings

```python
context = await browser.new_context(
    viewport={'width': 1920, 'height': 1080},
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    locale='zh-CN',
    timezone_id='Asia/Shanghai',
)
page = await context.new_page()
```

## Key Points

- Hyperbrowser provides the WebSocket endpoint automatically
- No direct WebSocket URL construction needed (unlike Browserless)
- Always use `connect_over_cdp()` with the `ws_endpoint`
- First `browser.contexts[0]` contains the default context
- Always close via `client.sessions.stop(session.id)` in finally block
- Session timeout is controlled by `timeout_minutes` parameter

## 3DHunyuan Migration Notes

Current project uses Browserless.io connection pattern:
- **Browserless URL**: `wss://chrome-production-{REGION}.browserless.io/v1?token=XXX`
- **Migration**: Replace Browserless `connect_over_cdp` with Hyperbrowser `session.ws_endpoint`
- **Cookies**: Currently loaded from `Cookies/Cookies-XX.json` — can use Hyperbrowser Profiles instead
- **API key**: Current project has 50 Browserless tokens → replace with single `HYPERBROWSER_API_KEY`
