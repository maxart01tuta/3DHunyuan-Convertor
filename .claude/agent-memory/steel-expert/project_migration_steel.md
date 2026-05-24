---
name: Project Browser Migration to Steel.dev
description: Migration from local Playwright to Steel.cloud browser with Files API
type: project

## Why
Current project uses local Chromium via `playwright.chromium.launch()` with direct file paths (`D:\...\photo.jpg`). Steel runs browsers remotely, so local paths are inaccessible. Requires Files API upload + CDP for file inputs.

## How to Apply

### 1. Installation
```bash
pip install steel-sdk playwright
playwright install chromium
```

### 2. Replace browser.py launch function
Use `create_steel_browser_with_retry()` pattern with retry logic (3 attempts per API key) and proper cleanup in finally.

CDP URL format:
```python
f'wss://connect.steel.dev?apiKey={api_key}&sessionId={session.id}'
```

### 3. File Uploads - CRITICAL CHANGE
Local paths DON'T WORK in Steel. Must:
- Upload file via `client.sessions.files.upload(session.id, file=f)`
- Get `session_file.path` (e.g., `/sessions/xxx/files/photo.jpg`)
- Set input via CDP: `DOM.setFileInputFiles` (not Playwright's `set_input_files` directly)

Simplified (steel-sdk >= 0.17.0):
```python
session_file = await client.sessions.files.upload(session.id, file=f)
await locator.set_input_files(session_file.path)  # Works if SDK version supports it
```

### 4. Cleanup
ALWAYS release session:
```python
client.sessions.release(session.id)
```
Track in `finally` block or context manager.

### 5. Timeouts
Increase to 300000ms (5 min) due to network latency.

### 6. Configuration
Add `API_LIST` to `config.py`. Store keys in env vars preferred.

## Files Modified / Created
- `BROWSER-STEEL/browser.py` - New Steel CDP connection
- `BROWSER-STEEL/func_upload_photo_*.py` - Files API integration
- `BROWSER-STEEL/config.py` - Add API_LIST, API_TIME

## Windows Notes
Absolute paths must use raw strings or Path objects when uploading:
```python
with open(r'D:\MAX\PYTHON\STOCK-PYTHON\Upload\photo.jpg', 'rb') as f:
    session_file = await client.sessions.files.upload(session.id, file=f)
```

## Validation
- Verify steel-sdk version: `pip show steel-sdk`
- Test with small image first
- Check session viewer URL for live debugging
- Monitor Steel Dashboard for session leaks
