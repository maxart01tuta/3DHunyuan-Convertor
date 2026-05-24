# Proxy Configuration for Browserless

## Overview

Browserless supports both built-in residential proxies and third-party proxy services.

---

## 1. Built-in Residential Proxy

### Quick Start

```python
from playwright.async_api import async_playwright

async def main():
    token = "YOUR_TOKEN"
    # Add proxy parameters to connection URL
    ws_endpoint = (
        f"wss://production-sfo.browserless.io/"
        f"?token={token}"
        f"&proxy=residential"
        f"&proxyCountry=us"
    )

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_endpoint)
        context = browser.contexts[0]
        page = await context.new_page()

        await page.goto('https://ip-api.com/')
        ip_info = await page.text_content('section')
        print(f"IP Info: {ip_info}")

        await browser.close()

asyncio.run(main())
```

### Available Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `proxy` | Enable residential proxy | `&proxy=residential` |
| `proxyCountry` | ISO country code (us, de, uk, br, etc.) | `&proxyCountry=de` |
| `proxyCity` | City name (Scale plan only) | `&proxyCity=chicago` |
| `proxySticky` | Keep same IP across requests | `&proxySticky=true` |
| `proxyLocaleMatch` | Auto-set browser locale to match proxy | `&proxyLocaleMatch=1` |

### Country Codes

Common country codes:
- `us` - United States
- `uk` - United Kingdom
- `de` - Germany
- `fr` - France
- `es` - Spain
- `it` - Italy
- `ca` - Canada
- `au` - Australia
- `jp` - Japan
- `br` - Brazil

Full list: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2

### Examples by Region

```python
# US West proxy
ws = "wss://production-sfo.browserless.io/?token=TOKEN&proxy=residential&proxyCountry=us"

# UK proxy
ws = "wss://production-lon.browserless.io/?token=TOKEN&proxy=residential&proxyCountry=uk"

# Germany proxy with locale matching
ws = "wss://production-ams.browserless.io/?token=TOKEN&proxy=residential&proxyCountry=de&proxyLocaleMatch=1"

# Sticky session (same IP across requests)
ws = "wss://production-sfo.browserless.io/?token=TOKEN&proxy=residential&proxyCountry=us&proxySticky=true"

# City-level (Scale plan) - Chicago
ws = "wss://production-sfo.browserless.io/?token=TOKEN&proxy=residential&proxyCountry=us&proxyCity=chicago"
```

### Get Available Cities (Scale Plan)

```python
import requests

def get_proxy_cities(token: str, country: str = None) -> list:
    """Get list of available cities for proxy."""
    base_url = "https://production-sfo.browserless.io/proxy/cities"
    params = {'token': token}
    if country:
        params['country'] = country.upper()

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    return resp.json()

# Usage
cities = get_proxy_cities("YOUR_TOKEN", country="US")
print(f"Available US cities: {cities}")
```

---

## 2. Third-Party Proxies

### Method 1: externalProxyServer ( RECOMMENDED )

```python
# Format: http(s)://[username:password@]host:port
proxy_url = "http://user:pass@proxy.example.com:8080"
encoded = requests.utils.quote(proxy_url)  # URL-encode

ws_endpoint = f"wss://production-sfo.browserless.io/?token={token}&externalProxyServer={encoded}"
```

**Complete example**:
```python
import requests
from urllib.parse import quote

proxy_server = "http://username:password@proxy.example.com:8080"
encoded_proxy = quote(proxy_server)

ws = f"wss://production-sfo.browserless.io/?token={token}&externalProxyServer={encoded_proxy}"

async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp(ws)
    # ...
```

### Method 2: Chrome --proxy-server Flag

```python
# Pass proxy as Chrome command line flag
proxy = "http://proxy.example.com:8080"
ws_endpoint = f"wss://production-sfo.browserless.io/?--proxy-server={proxy}&token={token}"
```

**With authentication** (requires separate handling):
```python
# Proxy with basic auth
proxy = "http://proxy.example.com:8080"
ws = f"wss://production-sfo.browserless.io/?--proxy-server={proxy}&token={token}"

async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp(ws)
    context = browser.contexts[0]
    page = await context.new_page()

    # Authenticate via CDP
    cdpsession = await page.context.new_cdp_session(page)
    await cdpsession.send('Network.authenticate', {
        'username': 'user',
        'password': 'pass'
    })

    await page.goto('https://ip-api.com/')
```

### Method 3: Context-level Proxy Configuration (Limited)

⚠️ In CDP mode, `newContext()` proxy option may NOT inherit the WebSocket connection's proxy. Use WebSocket URL parameters instead for reliable proxy.

If using Playwright native mode:

```python
# Playwright native connect (NOT CDP)
ws = f"wss://production-sfo.browserless.io/chromium/playwright?token={token}"
browser = await playwright.chromium.connect(ws)

context = await browser.new_context(
    proxy={
        'server': 'http://proxy.example.com:8080',
        'username': 'user',
        'password': 'pass'
    }
)
page = await context.new_page()
```

---

## 3. Proxy Verification Examples

### Verify Proxy is Working

```python
async def verify_proxy(page):
    """Check that proxy is active by querying IP service."""
    await page.goto('https://ip-api.com/json/', wait_until='domcontentloaded')

    # Get IP info
    ip_data = await page.evaluate('''() => {
        const el = document.body;
        try {
            return JSON.parse(el.textContent);
        } catch {
            return { error: 'Cannot parse IP info' };
        }
    }''')

    if 'query' in ip_data:
        print(f"✓ Connected via proxy. IP: {ip_data['query']}")
        print(f"  Country: {ip_data.get('country', 'unknown')}")
        print(f"  City: {ip_data.get('city', 'unknown')}")
        print(f"  ISP: {ip_data.get('isp', 'unknown')}")
        return ip_data
    else:
        print(f"✗ Proxy check failed: {ip_data}")
        return None

# Usage
ip_info = await verify_proxy(page)
```

### Compare Direct vs Proxied Requests

```python
async def compare_direct_vs_proxied():
    """Compare IP without proxy vs with proxy."""
    token = "YOUR_TOKEN"

    # Without proxy
    ws_direct = f"wss://production-sfo.browserless.io/?token={token}"
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_direct)
        page = browser.contexts[0].new_page()
        await page.goto('https://ip-api.com/json/')
        direct_ip = await page.evaluate('() => JSON.parse(document.body.textContent).query')
        await browser.close()

    # With residential proxy
    ws_proxy = f"wss://production-sfo.browserless.io/?token={token}&proxy=residential&proxyCountry=de"
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_proxy)
        page = browser.contexts[0].new_page()
        await page.goto('https://ip-api.com/json/')
        proxy_ip = await page.evaluate('() => JSON.parse(document.body.textContent).query')
        await browser.close()

    print(f"Direct IP: {direct_ip}")
    print(f"Proxy IP (DE): {proxy_ip}")
    print(f"Different: {direct_ip != proxy_ip}")
```

---

## 4. Proxy Best Practices

### ✅ DO:
- Use regional endpoint closest to your infrastructure
- Set `proxySticky=true` for consistent IP throughout session
- Match `proxyLocaleMatch=1` with `proxyCountry` for realistic browser
- Test proxy with `ip-api.com` before main automation
- Monitor usage - residential proxies have higher cost
- Rotate countries for geo-specific content testing

### ❌ DON'T:
- Use free/public proxy lists (unreliable, security risk)
- Forget URL-encoding special chars in proxy URL
- Use proxyCity without Scale plan (will get 401)
- Change proxy parameters mid-session (create new session instead)
- Assume all requests go through proxy (check site's WebRTC leaks)

---

## 5. Troubleshooting

### Problem: Proxy not working, real IP exposed
**Check**:
1. Connection URL includes `externalProxyServer` (URL-encoded!)
2. No conflicting proxy settings in context
3. Site doesn't use WebRTC to bypass proxy (enable `proxyLocaleMatch` helps)

**Fix**: Use externalProxyServer in URL, not context.proxy

### Problem: 401 error when using proxyCity
**Cause**: Your plan doesn't support city-level targeting (requires Scale 500k+)
**Fix**: Remove proxyCity or upgrade plan

### Problem: Authentication failed
**Cause**: Incorrect credentials in proxy URL
**Fix**: Verify proxy URL format: `http://user:pass@host:port`

**For externalProxyServer**:
```python
from urllib.parse import quote
proxy = "http://user:password123@proxy.example.com:8080"
encoded = quote(proxy)  # Encodes special chars like @, :, /
```

### Problem: Slow connection with proxy
**Cause**: Residential proxy adds latency, not optimized for your region
**Fix**: Choose proxyCountry closer to target site, not your location

### Problem: Proxy connection drops
**Cause**: Proxy server timeout, max connections reached
**Fix**: Implement retry logic, rotate different proxy servers

---

## 6. Proxy Rotator Pattern

```python
import random

class ProxyRotator:
    def __init__(self, proxy_urls: list):
        self.proxy_urls = proxy_urls

    def get_random_proxy_url(self, token: str, region: str = "sfo") -> str:
        """Generate WS endpoint with random proxy."""
        proxy = random.choice(self.proxy_urls)
        encoded = quote(proxy)

        return (
            f"wss://production-{region}.browserless.io/"
            f"?token={token}"
            f"&externalProxyServer={encoded}"
        )

# Usage
rotator = ProxyRotator([
    "http://user1:pass1@proxy1:8080",
    "http://user2:pass2@proxy2:8080",
    "http://user3:pass3@proxy3:8080",
])

for i in range(10):
    ws = rotator.get_random_proxy_url(token, region="sfo")
    # connect and use...
```

---

## 7. Proxy + Stealth + Region Combination

```python
def build_browserless_url(
    token: str,
    region: str = "sfo",
    use_stealth: bool = False,
    use_proxy: bool = False,
    proxy_country: str = None,
    proxy_sticky: bool = False,
    proxy_locale_match: bool = False
) -> str:
    """Build optimized Browserless connection URL."""
    base = f"wss://production-{region}.browserless.io"

    if use_stealth:
        base += "/stealth"
    elif use_proxy and proxy_country:
        # Use stealth for best results with proxy
        base += "/stealth"

    params = [f"token={token}"]

    if use_proxy and proxy_country:
        params.append("proxy=residential")
        params.append(f"proxyCountry={proxy_country}")
        if proxy_sticky:
            params.append("proxySticky=true")
        if proxy_locale_match:
            params.append("proxyLocaleMatch=1")

    return f"{base}?{'&'.join(params)}"

# Usage - German proxy with stealth and locale matching
url = build_browserless_url(
    token="TOKEN",
    region="ams",
    use_stealth=True,
    use_proxy=True,
    proxy_country="de",
    proxy_locale_match=True
)
```

---

## 8. Region Selection Guide

| Target Site Location | Recommended Region | Why |
|---------------------|-------------------|-----|
| USA, Canada, Americas | sfo | Lowest latency, best performance |
| UK, Ireland | lon | Geographic proximity |
| EU (Germany, France, Spain) | ams | Amsterdam is central EU |
| Asia, Australia | sfo (closest) or check Browserless for APAC regions |
| Global testing | sfo + lon (rotate) | Test from different regions |

**Always use regional endpoint closest to your target sites**, not your own location.

---

## References

- Browserless Proxies: https://docs.browserless.io/baas/features/proxies
- Connection URL Patterns: https://docs.browserless.io/baas/connection-url-patterns
- Regional Endpoints: https://docs.browserless.io/baas/load-balancers
