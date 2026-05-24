# File Upload Size Limit Workaround (50MB CDP Limit)

## Problem

When using Hyperbrowser with Playwright CDP connection, uploading files larger than 50MB via `page.set_input_files()` fails with:

```
Error: Page.set_input_files: Cannot transfer files larger than 50Mb to a browser not co-located with the server
```

This is a **fundamental CDP (Chrome DevTools Protocol) limitation**. The CDP WebSocket connection has a message size limit (~50MB) for file transfers when the browser runs remotely from the client.

## Solution: Use Session Upload API

Hyperbrowser provides an official workaround: **upload files directly to the session's filesystem** via the REST API, then reference them by path in `set_input_files()`. This bypasses CDP entirely because the file is transferred via HTTP upload (multipart/form-data) and already exists on the VM where the browser runs.

### How It Works

1. Upload file to session: `client.sessions.upload_file(session_id, local_file_path)`
2. Response contains `file_path` (e.g., `/tmp/uploads/abc123.glb`)
3. Use that path in Playwright: `await page.set_input_files(selector, response.file_path)`

The browser reads the file directly from its local filesystem (`/tmp/uploads/`), no CDP transfer needed.

## Code Examples

### Async Version (for func_upload.py)

```python
from hyperbrowser import AsyncHyperbrowser
import os
from datetime import datetime

async def upload_glb_file(page, client: AsyncHyperbrowser, session_id: str, glb_path: str):
    """
    Upload GLB file to Hyperbrowser session and set it as file input value.

    Args:
        page: Playwright page object
        client: AsyncHyperbrowser client
        session_id: Active session ID
        glb_path: Local path to GLB file

    Returns:
        UploadFileResponse with file_path info
    """
    _ts = lambda: datetime.now().strftime('%H:%M:%S')

    print(f"[{_ts()}] 📤 Загрузка файла в сессию Hyperbrowser: {glb_path}")

    # 1. Upload file via Hyperbrowser API (bypasses CDP limit)
    upload_response = await client.sessions.upload_file(session_id, glb_path)

    print(f"[{_ts()}] ✓ Файл загружен в сессию: {upload_response.file_path}")
    print(f"[{_ts()}]   Original name: {upload_response.original_name}")

    # 2. Set input to the remote file path (already exists on VM)
    input_selector = 'input[type="file"]'  # ваш селектор
    await page.set_input_files(input_selector, upload_response.file_path)

    print(f"[{_ts()}] ✓ File input установлен на {upload_response.file_path}")

    return upload_response
```

### Sync Version

```python
from hyperbrowser import Hyperbrowser

def upload_glb_file_sync(page, client: Hyperbrowser, session_id: str, glb_path: str):
    """Sync version for существующий sync-код."""
    upload_response = client.sessions.upload_file(session_id, glb_path)
    page.set_input_files('input[type="file"]', upload_response.file_path)
    return upload_response
```

### Integration into Existing `func_upload.py`

```python
# HYPERBROWSER/func_upload.py (modified)
import asyncio
import os
from datetime import datetime
from config import MAX_TIME, WAIT_TIME, UPLOAD_DIR, input_upload, knopka_obj
from browser import wait_for_element, get_hyperbrowser_client  # предположим

async def run(page, baza_id: str, session_id: str, hb_client):
    """Загрузка GLB через Session Upload API для больших файлов."""
    glb_path = os.path.join(UPLOAD_DIR, f"{baza_id}.glb")

    if not os.path.exists(glb_path):
        raise FileNotFoundError(f"GLB файл не найден: {glb_path}")

    _ts = lambda: datetime.now().strftime('%H:%M:%S')
    print(f"[{_ts()}] Загрузка большого файла ({os.path.getsize(glb_path)//(1024*1024)}MB): {glb_path}")

    try:
        # Ожидание input элемента
        await wait_for_element(page, input_upload, timeout=MAX_TIME)

        # ⭐ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: upload_file вместо set_input_files
        upload_response = await hb_client.sessions.upload_file(session_id, glb_path)
        remote_path = upload_response.file_path
        print(f"[{_ts()}] Файл загружен в сессию: {remote_path}")

        # Устанавливаем input на уже загруженный файл
        await page.set_input_files(input_upload, remote_path)
        print(f"[{_ts()}] Input установлен на remote path")

        # Ожидание завершения (кнопка OBJ появляется)
        await wait_for_element(page, knopka_obj, timeout=MAX_TIME)
        print(f"[{_ts()}] ✓ GLB успешно загружен (через upload API)")

    except Exception as e:
        print(f"[{_ts()}] ✗ Ошибка: {type(e).__name__}: {e}")
        raise
```

## Documentation References

- **Session Uploads**: https://www.hyperbrowser.ai/docs/sessions/uploads
- **Session Parameters**: https://www.hyperbrowser.ai/docs/sessions/parameters
- **API Reference (Upload)**: https://www.hyperbrowser.ai/docs/api-reference/session-upload
- **Python SDK (upload_file)**: `SessionManager.upload_file(id, file_input)` in hyperbrowser/client/managers/
- **Memory: Computer Actions** (alternative approaches): `.claude/agent-memory/hyperbrowser-expert/computer_actions.md`

## Alternative Approaches (if upload_file unavailable)

### 1. **Computer Actions Drag & Drop**
Coordinates-based drag-drop from a pre-opened file dialog. Complex and flaky.

```python
# Не рекомендуется: требует точных координат
await client.computer_action.move_mouse(session_id, x=100, y=200)
await client.computer_action.click(session_id, x=100, y=200, button="left")
# ... manual file selection in OS dialog - brittle
```

### 2. **JavaScript File API + Sandbox**
Upload GLB to sandbox first, then fetch via `fetch()` and construct Blob. Requires site to accept URL/uploads programmatically.

```python
# ⚠️ Только если fabconvert.com принимает URL или Base64
glb_base64 = base64.b64encode(open(glb_path, 'rb').read()).decode()
await page.evaluate(f"""
    const blob = new Blob([Uint8Array.from(atob('{glb_base64}'), c => c.charCodeAt(0))], {{type: 'model/gltf-binary'}});
    const file = new File([blob], 'model.glb');
    const input = document.querySelector('input[type=file]');
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
""")
```
**Limitation**: Browser still needs to deserialize base64 → memory, may hit memory limits for 100MB files.

### 3. **Sandbox HTTP Server + fetch()**
Start a simple HTTP server in Hyperbrowser sandbox, serve the GLB file, then use fetch+FormData to POST to site. Very complex, requires site to accept custom multipart POST.

## FAQ

**Q: Есть ли лимит на размер файла в `upload_file` API?**
A: Нет публичного лимита. Upload идёт через HTTP (multipart/form-data) без CDP ограничений. Лимит только на размер сессии storage (не менее нескольких GB).

**Q: Куда сохраняются файлы в сессии?**
A: В `/tmp/uploads/` (или `/tmp/<sessionId>/uploads/` для self-hosted). Доступны для чтения браузером.

**Q: Нужно ли очищать `/tmp/uploads/` после использования?**
A:Hyperbrowser автоматически очищает временные файлы при остановке сессии. Можно удалять вручную через sandbox.files.remove() для экономии space.

**Q: Работает ли для ZIP, PDF, видео?**
A: Да, любой файл, который сайт принимает через `<input type="file">`.

**Q: Какой таймаут у upload_file?**
A: Зависит от `timeout_minutes` сессии. Рекомендуем 30-60 минут для upload больших файлов. Transfer speed ограничен пропускной способностью сети Hyperbrowser (обычно 10-100 Mbps).

**Q: Можно ли parallelism?**
A: Да, но учитывайте лимит concurrent uploads (проверьте ваш тариф). Upload лидирует по времени.

**Q: Co-located режим?**
A: "Co-located" означает что браузер запущен на той же machine что и Hyperbrowser сервер, что устраняет CDP-лимит. Это **не настраивается пользователем** — это internal инфраструктура Hyperbrowser. Используйте upload_file API вместо этого.

## Performance Estimates

| File Size | Upload Time (≈50 Mbps) | set_input_files (CDP) |
|-----------|-----------------------|----------------------|
| 50 MB     | ~8 сек                | ~8 сек               |
| 100 MB    | ~16 сек               | ❌ Fail (>50MB limit) |
| 500 MB    | ~80 сек               | ❌ Fail              |

Upload_file API — единственный способ для файлов >50MB.

## Testing Code

```python
# test_upload.py
import asyncio
import os
from hyperbrowser import AsyncHyperbrowser

async def test():
    client = AsyncHyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))
    session = await client.sessions.create(
        CreateSessionParams(
            use_stealth=True,
            timeout_minutes=30,
        )
    )
    print("Session:", session.id)

    # Подключите Playwright
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(session.ws_endpoint)
        page = browser.contexts[0].pages[0]
        await page.goto("https://httpbin.io/post")

        # Тест upload 100MB dummy file
        test_file = "/tmp/test_100mb.bin"
        with open(test_file, "wb") as f:
            f.write(os.urandom(100 * 1024 * 1024))

        try:
            resp = await client.sessions.upload_file(session.id, test_file)
            print("Uploaded to:", resp.file_path)

            # Проверка что файл доступен
            content = await page.evaluate(f"""
                fetch('/tmp/uploads/{os.path.basename(resp.file_path)}')
                    .then(r => r.blob())
                    .then(b => b.size)
            """)
            print("File size in browser:", content, "bytes")
        finally:
            await client.sessions.stop(session.id)

asyncio.run(test())
```

## Migration Checklist

- [ ] Replace `page.set_input_files(selector, local_path)` with two-step: upload + remote path
- [ ] Ensure `session_id` is available in the upload function (pass as argument)
- [ ] Pass `hb_client` instance to upload function (store after session.create)
- [ ] Update error handling (catch upload failures separately)
- [ ] Log `upload_response.file_path` for debugging
- [ ] Clean up large files in `/tmp/uploads/` if uploading many in one session
- [ ] Ensure `timeout_minutes` sufficient for upload (30+ minutes for large batches)
