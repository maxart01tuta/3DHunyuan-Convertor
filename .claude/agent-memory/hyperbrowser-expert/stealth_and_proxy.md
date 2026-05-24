# Stealth and Proxy Configuration

## Stealth Modes

### Standard Stealth (Recommended)
```python
session = client.sessions.create(
    params=CreateSessionParams(use_stealth=True)
)
```
- Evades basic bot detection
- Recommended for most websites
- Available on all plans

### Ultra Stealth (Enterprise Only!)
```python
session = client.sessions.create(
    params=CreateSessionParams(use_ultra_stealth=True)
)
```
- **Contact**: info@hyperbrowser.ai for access
- Advanced evasion techniques
- For challenging sites (Cloudflare, PerimeterX)
- Only available on enterprise plans
- **Do NOT use** without confirming enterprise access

## Proxy Configuration

### Basic Proxy by Country
```python
from hyperbrowser.models import CreateSessionParams

session = client.sessions.create(
    params=CreateSessionParams(
        use_proxy=True,
        proxy_country="US"  # ISO country code
    )
)
```

### Proxy with State (US only)
```python
session = client.sessions.create(
    params=CreateSessionParams(
        use_proxy=True,
        proxy_country="US",
        proxy_state="CA"  # Two-letter state code
    )
)
```

### Proxy with City
```python
session = client.sessions.create(
    params=CreateSessionParams(
        use_proxy=True,
        proxy_country="DE",
        proxy_city="berlin"
    )
)
```

### Custom Proxy Server
```python
session = client.sessions.create(
    params=CreateSessionParams(
        use_proxy=True,
        proxy_server="http://your-proxy-server:8080",
        proxy_server_username="user",
        proxy_server_password="pass"
    )
)
```

## Available Proxy Countries

Major countries supported: US, GB, DE, FR, CA, AU, JP, BR, IN, RU, CN, and 100+ more.
Special: `RANDOM_COUNTRY` for random rotation.

## 3DHunyuan Project Notes

- **Target**: `https://3d.hunyuan.tencent.com/` — Chinese Tencent service
- **Recommended proxy**: Use `proxy_country="CN"` or `proxy_country="SG"` for proximity to Tencent servers
- **Locale**: Set `locale='zh-CN'` and `timezone_id='Asia/Shanghai'` for consistent session
- **Stealth**: Start with `use_stealth=True`; Tencent may have anti-bot detection

## Important Notes

- `proxy_country` accepts ISO country codes (e.g., "US", "CA", "GB")
- State and city are optional filters; some locations may not be available
- Stealth and proxy can be combined in same session
- Always test stealth effectiveness on target domain before production use
