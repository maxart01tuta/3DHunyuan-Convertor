# Browserless REST API Quickstart

## Overview

Browserless provides REST APIs for common tasks without needing Playwright/Puppeteer.

---

## Authentication

All REST endpoints require `token` query parameter:

```
https://production-sfo.browserless.io/endpoint?token=YOUR_API_TOKEN
```

Or via Authorization header (some endpoints):
```python
headers = {'Authorization': 'Bearer YOUR_TOKEN'}
```

---

## 1. Screenshot API

### Endpoint
```
POST /screenshot
```

### Purpose
Capture screenshot of webpage

### Python Example

```python
import requests

def screenshot(
    url: str,
    token: str,
    output_path: str = 'screenshot.png',
    full_page: bool = True,
    format: str = 'png',
    viewport: dict = None,
    wait_until: str = 'networkidle'
):
    """Take screenshot using Browserless REST API."""
    endpoint = f"https://production-sfo.browserless.io/screenshot?token={token}"

    payload = {
        'url': url,
        'options': {
            'fullPage': full_page,
            'type': format,  # png, jpeg, webp
            'viewport': viewport or {'width': 1920, 'height': 1080},
            'waitUntil': wait_until  # load, domcontentloaded, networkidle
        }
    }

    response = requests.post(endpoint, json=payload, timeout=60)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        f.write(response.content)

    print(f"Screenshot saved: {output_path}")

# Usage
screenshot(
    url='https://example.com',
    token='YOUR_TOKEN',
    output_path='example_full.png',
    full_page=True
)
```

### Advanced Options

```python
payload = {
    'url': url,
    'options': {
        'fullPage': True,
        'format': 'jpeg',
        'quality': 90,  # 0-100, for JPEG only
        'clip': {  # Captures only specific region
            'x': 0,
            'y': 0,
            'width': 800,
            'height': 600
        },
        'emulateMedia': 'screen'  # or 'print' for print CSS
    }
}
```

---

## 2. PDF API

### Endpoint
```
POST /pdf
```

### Purpose
Generate PDF from webpage

### Python Example

```python
def pdf(
    url: str,
    token: str,
    output_path: str = 'output.pdf',
    landscape: bool = False,
    format: str = 'A4',
    print_background: bool = True,
    margin: dict = None
):
    """Generate PDF from URL."""
    endpoint = f"https://production-sfo.browserless.io/pdf?token={token}"

    payload = {
        'url': url,
        'options': {
            'landscape': landscape,
            'format': format,  # A4, Letter, Legal
            'printBackground': print_background,
            'margin': margin or {
                'top': '1cm',
                'bottom': '1cm',
                'left': '1cm',
                'right': '1cm'
            },
            'scale': 1.0,  # 0.1-2.0
            'pageRanges': '1-3'  # Optional, e.g., "1-2" or "1,3,5"
        }
    }

    response = requests.post(endpoint, json=payload, timeout=120)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        f.write(response.content)

    print(f"PDF saved: {output_path}")

# Usage
pdf(
    url='https://example.com/report',
    token='YOUR_TOKEN',
    output_path='report.pdf',
    landscape=False,
    format='A4'
)
```

---

## 3. Content API

### Endpoint
```
POST /content
```

### Purpose
Scrape HTML content from webpage

### Python Example

```python
def scrape_content(
    url: str,
    token: str,
    wait_for: int = 5000,
    selector: str = None,
    return_type: str = 'html'  # html, text, json
) -> str:
    """
    Scrape content from URL.

    Args:
        wait_for: Milliseconds to wait for page to load
        selector: CSS selector to extract specific element
        return_type: html (full), text (stripped), json
    """
    endpoint = f"https://production-sfo.browserless.io/content?token={token}"

    payload = {
        'url': url,
        'waitFor': wait_for,
    }

    if selector:
        payload['selector'] = selector

    response = requests.post(endpoint, json=payload, timeout=60)
    response.raise_for_status()

    if return_type == 'html':
        return response.text
    elif return_type == 'json':
        return response.json()
    else:
        return response.text.strip()

# Usage - scrape full HTML
html = scrape_content('https://example.com', token='TOKEN')
print(f"HTML length: {len(html)} chars")

# Usage - scrape specific element
article = scrape_content('https://example.com', token='TOKEN', selector='article')
print(f"Article: {article[:200]}...")
```

### Extract JSON from API endpoint

```python
def scrape_json_api(url: str, token: str) -> dict:
    """Fetch JSON from API endpoint."""
    endpoint = f"https://production-sfo.browserless.io/content?token={token}"
    payload = {'url': url, 'waitFor': 2000}

    response = requests.post(endpoint, json=payload)
    response.raise_for_status()

    return response.json()

# Usage
data = scrape_json_api('https://api.example.com/data', token='TOKEN')
```

---

## 4. Download API

### Endpoint
```
POST /download
```

### Purpose
Download files from URL (handles downloads that require browser interaction)

### Python Example

```python
def download_file(
    url: str,
    token: str,
    output_path: str = 'download',
    wait_for: int = 10000
) -> str:
    """
    Download file via browser.

    Returns:
        Path to saved file
    """
    endpoint = f"https://production-sfo.browserless.io/download?token={token}"

    payload = {
        'url': url,
        'waitFor': wait_for
    }

    response = requests.post(endpoint, json=payload, timeout=120)
    response.raise_for_status()

    # Response is base64 encoded file
    data = response.json()
    file_data = base64.b64decode(data['data'])
    filename = data.get('filename', 'downloaded_file')

    full_path = output_path if output_path.endswith(filename) else f"{output_path}/{filename}"
    with open(full_path, 'wb') as f:
        f.write(file_data)

    print(f"Downloaded: {full_path}")
    return full_path

# Usage
download_file(
    url='https://example.com/report.pdf',
    token='TOKEN',
    output_path='./downloads'
)
```

---

## 5. Function API

### Endpoint
```
POST /function
```

### Purpose
Execute custom Puppeteer script (advanced)

### Python Example

```python
def run_function(
    token: str,
    script: str,
    args: dict = None,
    timeout: int = 30000
) -> dict:
    """
    Execute Puppeteer script on Browserless.

    Args:
        script: Puppeteer JavaScript code (async function)
        args: Arguments passed to script

    Example script:
    ```
    async ({page, url, selector}) => {
      await page.goto(url);
      return await page.$eval(selector, el => el.textContent);
    }
    ```
    """
    endpoint = f"https://production-sfo.browserless.io/function?token={token}"

    payload = {
        'code': script,
        'args': args or {},
        'timeout': timeout
    }

    response = requests.post(endpoint, json=payload, timeout=timeout/1000 + 10)
    response.raise_for_status()

    return response.json()

# Usage - simple script
result = run_function(
    token='TOKEN',
    script='''async ({url}) => {
      const page = browser.newPage();
      await page.goto(url);
      return await page.title();
    }''',
    args={'url': 'https://example.com'}
)
print(f"Title: {result['result']}")
```

---

## 6. Unblock API

### Endpoint
```
POST /unblock
POST /chromium/unblock
```

### Purpose
Bypass bot detection before navigation

### Python Example

```python
def unblock_url(
    url: str,
    token: str,
    output: str = 'unblocked.html',
    strategy: str = 'aggressive'  # basic, aggressive
):
    """Use unblock feature to fetch protected content."""
    endpoint = f"https://production-sfo.browserless.io/unblock?token={token}"

    payload = {
        'url': url,
        'waitFor': 10000,
        'options': {
            'strategy': strategy,
            'blockAds': True,
            'blockTrackers': True
        }
    }

    response = requests.post(endpoint, json=payload, timeout=60)
    response.raise_for_status()

    with open(output, 'wb') as f:
        f.write(response.content)

    print(f"Unblocked content saved: {output}")

# Usage
unblock_url('https://protected-site.com', token='TOKEN', output='content.html')
```

---

## 7. BrowserQL (GraphQL)

### Endpoint
```
POST /chromium/bql
```

### Purpose
Execute BrowserQL queries for advanced automation

### Python Example

```python
def bql_query(token: str, query: str, variables: dict = None):
    """Execute BrowserQL mutation/query."""
    endpoint = f"https://production-sfo.browserless.io/chromium/bql?token={token}"

    payload = {
        'query': query,
        'variables': variables or {}
    }

    response = requests.post(endpoint, json=payload, timeout=300)
    response.raise_for_status()

    return response.json()

# Example: Navigate and solve CAPTCHA
query = '''
mutation Solve($url: String!) {
  goto(url: $url, waitUntil: networkIdle) {
    status
  }
  solve(type: cloudflare) {
    found
    solved
    time
  }
  screenshot {
    base64
  }
}
'''

result = bql_query(
    token='TOKEN',
    query=query,
    variables={'url': 'https://example.com'}
)

print(f"Navigation status: {result['data']['goto']['status']}")
print(f"CAPTCHA solved: {result['data']['solve']['solved']}")
```

---

## Common Patterns

### Pattern 1: Batch Screenshots

```python
def batch_screenshots(urls: list, token: str, output_dir: str = 'screenshots'):
    """Take screenshots of multiple URLs."""
    Path(output_dir).mkdir(exist_ok=True)

    for url in urls:
        filename = safe_filename(url) + '.png'
        output_path = Path(output_dir) / filename

        try:
            screenshot(url, token, str(output_path))
            print(f"✓ {url}")
        except Exception as e:
            print(f"✗ {url}: {e}")
```

### Pattern 2: Polling with Rate Limit Handling

```python
import time

def poll_with_backoff(urls: list, token: str, delay: float = 1.0):
    """Poll URLs with rate limit awareness."""
    results = []
    for i, url in enumerate(urls):
        if i > 0:
            time.sleep(delay)  # Rate limiting

        try:
            result = scrape_content(url, token)
            results.append(result)
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                print("Rate limited! Backing off...")
                time.sleep(60)
                # Retry once
                result = scrape_content(url, token)
                results.append(result)
            else:
                raise
    return results
```

### Pattern 3: Health Check

```python
def health_check(token: str) -> dict:
    """Check Browserless service health."""
    try:
        # Check endpoint is reachable
        resp = requests.get(
            f"https://production-sfo.browserless.io/health?token={token}",
            timeout=10
        )
        return {
            'status': 'healthy' if resp.status_code == 200 else 'unhealthy',
            'response_time': resp.elapsed.total_seconds()
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
```

---

## Error Handling

```python
def rest_api_call_safe(endpoint: str, payload: dict, token: str):
    """Make REST API call with comprehensive error handling."""
    full_url = f"{endpoint}?token={token}"

    try:
        response = requests.post(full_url, json=payload, timeout=60)
        response.raise_for_status()
        return response

    except requests.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Invalid API token")
        elif e.response.status_code == 403:
            raise Exception("Endpoint not available in your plan")
        elif e.response.status_code == 429:
            raise Exception("Rate limit exceeded - reduce concurrency")
        elif e.response.status_code == 408:
            raise Exception("Request timeout - increase waitFor or reduce page complexity")
        else:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")

    except requests.ConnectionError:
        raise Exception("Cannot connect to Browserless - check internet")

    except requests.Timeout:
        raise Exception("Request timed out - increase timeout parameter")
```

---

## Response Formats

### Screenshot Response
```
Content-Type: image/png
Body: Binary PNG data
```

### PDF/Content/Download Response
```json
{
  "data": "base64-encoded-file-data",
  "filename": "optional-filename.ext",
  "size": 123456
}
```

### Content Response (text)
```
<html>...</html>
```

---

## Best Practices

1. **Use regional endpoints** closest to your infrastructure
   ```python
   # US: production-sfo.browserless.io
   # EU: production-lon.browserless.io
   ```

2. **Set appropriate wait_until** for your use case
   - Fast: `domcontentloaded`
   - Thorough: `networkidle`

3. **Handle rate limits** (429) with exponential backoff

4. **Compress outputs** if sending over network
   ```python
   import gzip
   compressed = gzip.compress(response.content)
   ```

5. **Cache responses** when possible to save credits

6. **Monitor usage** in dashboard to avoid surprise bills

---

## Quick Reference Table

| Task | Endpoint | HTTP Method | Best For |
|------|----------|-------------|----------|
| Screenshot | `/screenshot` | POST | Images of pages |
| PDF | `/pdf` | POST | Print-ready documents |
| Scrape HTML | `/content` | POST | Text extraction |
| Download | `/download` | POST | File downloads |
| Custom script | `/function` | POST | Complex Puppeteer logic |
| Unblock | `/unblock` | POST | Bot-protected sites |
| BQL | `/chromium/bql` | POST | Advanced automation |

---

## See Also

- Full REST API docs: https://docs.browserless.io/rest-apis/intro
- Launch options: https://docs.browserless.io/baas/connection-url-patterns
- Error handling: `error_handling.md`
