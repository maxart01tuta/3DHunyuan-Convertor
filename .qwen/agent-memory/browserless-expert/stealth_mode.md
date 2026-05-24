# Stealth Mode & Anti-Detection for Browserless

## Overview

Browserless offers specialized stealth routes to bypass bot detection systems (Cloudflare, PerimeterX, DataDome, etc.).

---

## Stealth Route Types

| Route | Description | Best For |
|-------|-------------|----------|
| `/stealth` | Hardened Chromium binary with anti-detection patches | Highest evasion, most aggressive |
| `/chromium/stealth` | Standard Chromium + stealth layer | Balance of features & stealth |
| `/chrome/stealth` | Google Chrome binary + stealth layer | Sites requiring Chrome-specific features |

---

## Quick Start: Stealth Connection

```python
from playwright.async_api import async_playwright

async def stealth_session():
    token = "YOUR_TOKEN"

    # Use stealth endpoint
    ws = f"wss://production-sfo.browserless.io/stealth?token={token}"

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws)
        context = browser.contexts[0]
        page = await context.new_page()

        # Test with bot detection site
        await page.goto('https://nowsecure.nl/')  # Cloudflare protected
        print(f"Title: {await page.title()}")

        await browser.close()

asyncio.run(stealth_session())
```

---

## Stealth + Proxy Combination

```python
async def stealth_with_proxy():
    token = "YOUR_TOKEN"

    # German residential proxy + stealth + locale matching
    ws = (
        f"wss://production-ams.browserless.io/stealth?"
        f"token={token}"
        f"&proxy=residential"
        f"&proxyCountry=de"
        f"&proxyLocaleMatch=1"
    )

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws)
        context = browser.contexts[0]
        page = await context.new_page()

        # Browser should appear as German user
        await page.goto('https://ip-api.com/json/')
        ip_info = await page.text_content('body')
        print(f"IP Info: {ip_info}")

        await browser.close()
```

---

## Comprehensive Stealth Configuration

```python
def build_stealth_url(
    token: str,
    region: str = "sfo",
    browser: str = "chromium",  # chromium, chrome
    proxy: bool = False,
    proxy_country: str = None,
    proxy_sticky: bool = False,
    proxy_locale_match: bool = False,
    block_ads: bool = False,
    **extra_params
) -> str:
    """
    Build stealth Browserless URL with all options.

    Args:
        token: API token
        region: sfo, lon, ams
        browser: chromium or chrome
        proxy: Enable residential proxy
        proxy_country: ISO country code
        proxy_sticky: Keep same proxy IP
        proxy_locale_match: Auto-set browser locale
        block_ads: Enable ad blocking
        **extra_params: Additional query params

    Returns:
        WebSocket URL
    """
    base = f"wss://production-{region}.browserless.io"

    if browser == "stealth-only":
        # Use /stealth (hardened binary)
        base += "/stealth"
    else:
        # Use /browser/stealth
        base += f"/{browser}/stealth"

    params = [f"token={token}"]

    if proxy and proxy_country:
        params.append("proxy=residential")
        params.append(f"proxyCountry={proxy_country}")
        if proxy_sticky:
            params.append("proxySticky=true")
        if proxy_locale_match:
            params.append("proxyLocaleMatch=1")

    if block_ads:
        params.append("blockAds=true")

    # Add any extra params
    for key, value in extra_params.items():
        params.append(f"{key}={value}")

    return f"{base}?{'&'.join(params)}"

# Example: Full stealth with UK proxy, sticky, ad blocking
url = build_stealth_url(
    token="YOUR_TOKEN",
    region="lon",
    browser="chromium",
    proxy=True,
    proxy_country="uk",
    proxy_sticky=True,
    proxy_locale_match=True,
    block_ads=True
)
print(f"Stealth URL: {url}")
```

---

## Detecting Bot Protection

```python
async def detect_protection(page) -> dict:
    """
    Check what bot protection site is using.
    Returns protection type or 'none'.
    """
    protection_types = {
        'cloudflare': [
            'challenge-form', 'challenge-running', 'cf-browser-verification',
            'turnstile', 'h-captcha', 'g-recaptcha'
        ],
        'perimeterx': ['px-box', 'px-captcha'],
        'datadome': ['datadome-captcha', 'dd-', 'datadome'],
        'akamai': ['akamai', 'sensor_data'],
        'incapsula': ['incapsula', 'imp-captcha']
    }

    page_content = await page.content()
    detected = []

    for protection, selectors in protection_types.items():
        for selector in selectors:
            if selector in page_content:
                detected.append(protection)
                break

    return {
        'detected': list(set(detected)),
        'has_protection': len(detected) > 0,
        'uses_captcha': any(p in ['cloudflare', 'perimeterx'] for p in detected)
    }

# Usage
protection = await detect_protection(page)
if protection['has_protection']:
    print(f"⚠️ Bot protection detected: {', '.join(protection['detected'])}")
    # Use stealth mode or BQL
```

---

## Stealth vs Regular Comparison

```python
import asyncio

async def compare_regular_vs_stealth():
    """Compare behavior of regular vs stealth connections."""
    token = "YOUR_TOKEN"

    # Regular connection
    regular_url = f"wss://production-sfo.browserless.io/?token={token}"

    # Stealth connection
    stealth_url = f"wss://production-sfo.browserless.io/stealth?token={token}"

    # Test on bot-detection site
    test_url = 'https://nowsecure.nl/'

    print("Testing regular connection...")
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(regular_url)
        context = browser.contexts[0]
        page = await context.new_page()

        try:
            await page.goto(test_url, timeout=30000)
            title_regular = await page.title()
            print(f"  Title: {title_regular}")
        except Exception as e:
            print(f"  Error: {e}")
        finally:
            await browser.close()

    print("\nTesting stealth connection...")
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(stealth_url)
        context = browser.contexts[0]
        page = await context.new_page()

        try:
            await page.goto(test_url, timeout=30000)
            title_stealth = await page.title()
            print(f"  Title: {title_stealth}")
        except Exception as e:
            print(f"  Error: {e}")
        finally:
            await browser.close()

    # Compare results
    print(f"\n{'='*50}")
    print(f"Regular: {title_regular}")
    print(f"Stealth: {title_stealth}")
    print(f"Stealth bypassed: {title_stealth != 'Just a moment...'}")
```

---

## Using BrowserQL for CAPTCHA Solving

Browserless's BrowserQL provides integrated CAPTCHA solving.

```python
async def bql_with_captcha_solve():
    """Use BQL to navigate and solve CAPTCHA before handing off to Playwright."""
    token = "YOUR_TOKEN"

    # BQL mutation with captcha solving
    bql_query = '''
    mutation Solve($url: String!) {
      goto(url: $url, waitUntil: networkIdle) {
        status
      }
      solve(type: cloudflare) {  # or "turnstile", "captcha"
        found
        solved
        time
      }
      reconnect(timeout: 30000) {
        browserWSEndpoint
      }
    }
    '''

    response = requests.post(
        'https://production-sfo.browserless.io/chromium/bql?token=' + token,
        json={
            'query': bql_query,
            'variables': {'url': 'https://example.com'}
        }
    )

    data = response.json()
    if data['data']['solve']['solved']:
        ws_endpoint = data['data']['reconnect']['browserWSEndpoint']
        ws = f"{ws_endpoint}?token={token}"

        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(ws)
            # Site is already unblocked, continue automation
            page = browser.contexts[0].new_page()
            # ...
```

---

## Custom Stealth Context Settings

```python
async def configure_stealth_context(browser):
    """Configure browser context for maximum stealth."""
    context = await browser.new_context(
        # Viewport
        viewport={'width': 1920, 'height': 1080},

        # User Agent - Use realistic, recent Chrome
        user_agent=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/131.0.0.0 Safari/537.36'
        ),

        # Locale matching proxy country
        locale='en-US',
        timezone_id='America/New_York',

        # Geolocation (optional, match proxy location)
        geolocation={'latitude': 37.7749, 'longitude': -122.4194},
        permissions=['geolocation'],

        # Disable automation flags
        bypass_csp=True,
        ignore_https_errors=True,

        # Extra HTTP headers
        extra_http_headers={
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    )

    # Additional stealth via JavaScript
    await context.add_init_script('''
        // Hide webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Spoof plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // Spoof languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        // Override permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    ''')

    return context
```

---

## Testing Stealth Effectiveness

```python
async def test_stealth_effectiveness():
    """Test against bot-detection sites."""
    stealth_sites = [
        'https://nowsecure.nl/',
        'https://bot.sannysoft.com/',
        'https://fingerprint.com/products/bot-detection/',
        'https://httpbin.org/user-agent'
    ]

    test_url = f"wss://production-sfo.browserless.io/stealth?token={token}"

    results = []
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(test_url)
        context = browser.contexts[0]
        page = await context.new_page()

        for site in stealth_sites:
            try:
                await page.goto(site, timeout=30000, wait_until='domcontentloaded')
                title = await page.title()

                # Check for bot detection keywords
                content = await page.content()
                blocked = any(keyword in content.lower() for keyword in [
                    'access denied', 'bot detected', 'captcha',
                    'security check', 'blocked', 'suspicious'
                ])

                results.append({
                    'site': site,
                    'title': title,
                    'blocked': blocked,
                    'screenshot': await page.screenshot() if blocked else None
                })

            except Exception as e:
                results.append({
                    'site': site,
                    'error': str(e),
                    'blocked': True
                })

        await browser.close()

    # Report
    passed = sum(1 for r in results if not r.get('blocked'))
    print(f"\nResults: {passed}/{len(results)} sites passed")
    for r in results:
        status = "BLOCKED" if r.get('blocked') else "OK"
        print(f"  [{status}] {r['site']}")

    return results
```

---

## Common Stealth Issues & Solutions

### Issue: Still blocked on Cloudflare
**Cause**: miss JS challenges or turnstile CAPTCHA
**Fix**:
- Use `/stealth` endpoint (not `/chromium/stealth`)
- Increase wait times
- Add `proxy=residential` + `proxyLocaleMatch=1`
- Consider BQL with `solve(type: cloudflare)`

### Issue: Site detects automation
**Cause**: Navigator.webdriver = true
**Fix**: Use Browserless stealth routes (they patch the binary)

### Issue: WebRTC leaks real IP
**Cause**: WebRTC bypasses proxy
**Fix**: Use `--disable-webrtc` flag
```python
ws = f"wss://production-sfo.browserless.io/stealth?token={token}&--disable-webrtc"
```

### Issue: Headless mode detected
**Cause**: Some sites detect headless Chrome
**Fix**: Browserless stealth routes handle this automatically

---

## Advanced Stealth: Browser Extensions

```python
async def use_adblock_extension(browser, extension_path: str):
    """
    Load browser extension (use CDP mode, not native Playwright).
    Note: Extensions only work with CDP connect, not connect().
    """
    # Extensions loaded at browser creation via --load-extension
    # Browserless does not support loading custom extensions directly.
    # Alternative: Use stealth routes which include ad blocking.

    # Check if blockAds parameter works for your needs
    ws = f"wss://production-sfo.browserless.io/stealth?token={token}&blockAds=true"
    browser = await playwright.chromium.connect_over_cdp(ws)
    return browser
```

---

## When Stealth is NOT Enough

Some sites use advanced device fingerprinting that even stealth can't bypass. Options:

1. **BrowserQL with unblock**:
```python
# Use BQL's unblock feature for advanced evasion
mutation {
  unblock(strategy: aggressive) {
    success
  }
  goto(url: "https://target.com") {
    status
  }
}
```

2. **Multiple proxy hops** (Enterprise feature):
   - Use Browserless Enterprise with custom proxy chains

3. **Real human interaction**:
   - Slow down automation
   - Add random mouse movements
   - Simulate typing with variable speed

---

## Production Stealth Checklist

Before deploying:

- [ ] Use `/stealth` or `/chromium/stealth` endpoint
- [ ] Combine with residential proxy from target country
- [ ] Set `proxyLocaleMatch=1` for locale consistency
- [ ] Test on your target sites (not just generic test pages)
- [ ] Verify session duration limits won't interrupt long tasks
- [ ] Implement retry logic (some blocks may be temporary)
- [ ] Monitor success rate in dashboard
- [ ] Have fallback to BQL if stealth fails

---

## Performance Impact

Stealth mode has some overhead:

| Metric | Regular | Stealth |
|--------|---------|---------|
| Connection Time | 2-3s | 3-5s |
| Memory Usage | Baseline | +10-20% |
| CPU Overhead | Baseline | +15-25% |
| Bot Detection Bypass | ~60% | ~85-95% |

Stealth routes provide the highest evasion but with performance cost. Use only when needed.

---

## Testing Different Configurations

```python
configs = [
    {'name': 'regular', 'url': f"wss://production-sfo.browserless.io/?token={token}"},
    {'name': 'stealth', 'url': f"wss://production-sfo.browserless.io/stealth?token={token}"},
    {'name': 'stealth+proxy', 'url': f"wss://production-sfo.browserless.io/stealth?token={token}&proxy=residential&proxyCountry=us"},
    {'name': 'stealth+proxy+locale', 'url': f"wss://production-sfo.browserless.io/stealth?token={token}&proxy=residential&proxyCountry=de&proxyLocaleMatch=1"},
]

async def test_configs():
    for config in configs:
        print(f"\nTesting: {config['name']}")
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(config['url'])
                page = browser.contexts[0].new_page()
                await page.goto('https://nowsecure.nl/', timeout=30000)
                title = await page.title()
                blocked = 'just a moment' in title.lower() or 'access denied' in await page.content()
                print(f"  Result: {'BLOCKED' if blocked else 'OK'} - Title: {title}")
                await browser.close()
            except Exception as e:
                print(f"  Error: {e}")
```

---

## See Also

- Proxy Configuration: `proxy_configuration.md`
- Browserless Stealth Docs: https://docs.browserless.io/baas/advanced-configurations/stealth-routes
- BQL for advanced unblocking: https://docs.browserless.io/browserql/
