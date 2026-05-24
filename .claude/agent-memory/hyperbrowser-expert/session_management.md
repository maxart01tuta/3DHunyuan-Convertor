# Session Management

## Quick Reference

- **API Endpoint**: `POST https://api.hyperbrowser.ai/api/session`
- **Authorization**: Header `x-api-key: YOUR_API_KEY`
- **Python SDK**: `pip install hyperbrowser`
- **Session Response**: `id`, `ws_endpoint`, `live_url`, `token`, `status`, `computer_action_endpoint`

## Session Lifecycle

1. **Create**: `client.sessions.create(params=CreateSessionParams(...))`
2. **Connect**: Use `session.ws_endpoint` with Playwright/Puppeteer/Selenium
3. **Stop**: `client.sessions.stop(session.id)` — **ALWAYS call in finally block!**

## Timeout Rules

- **Minimum**: 1 minute
- **Maximum**: 720 minutes (12 hours)
- **Default**: Based on team settings in dashboard
- Sessions auto-close after timeoutMinutes
- **Important**: Always set appropriate timeout for your task

## Session Options Summary

```python
from hyperbrowser.models import CreateSessionParams, ScreenConfig

session = client.sessions.create(
    params=CreateSessionParams(
        use_stealth=True,              # Standard stealth mode
        use_ultra_stealth=False,       # Enterprise only!
        use_proxy=True,
        proxy_country="US",
        screen=ScreenConfig(width=1920, height=1080),
        timeout_minutes=30,
        accept_cookies=True,
        solve_captchas=False,
    )
)
```

## 3DHunyuan Project Specifics

- **Target site**: `https://3d.hunyuan.tencent.com/`
- **Current stack**: Hyperbrowser + Playwright (`HYPERBROWSER_API_KEY`)
- **Cookie files**: `Cookies/Cookies-XX.json` format, per profile number
- **Key timeouts**: `MAX_TIME=180`, `WAIT_TIME=3` (from project config)
- **Session config**: Set `timeout_minutes` high enough — 3D generation takes significant time

## Important Notes

- Sessions are isolated browser instances
- Each session returns a unique WebSocket endpoint
- Live view available via `session.live_url`
- Sessions can be viewed in dashboard at Sessions page
- Credits are consumed per session based on usage
- Session tokens are returned for authentication
