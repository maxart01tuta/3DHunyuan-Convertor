# File Upload Recipes for Browserless

## Overview

When uploading files to a Browserless remote browser, local file paths are NOT accessible. Use one of these methods:

1. **Base64 + DataTransfer** - For local files (RECOMMENDED)
2. **Public URL** - For files already hosted online

---

## Recipe 1: Single Image Upload (Local File)

```python
import base64
from pathlib import Path

async def upload_image(page, image_path: str, input_selector: str = 'input[type="file"]'):
    """Upload a local image file to file input."""
    # Read and encode
    with open(image_path, 'rb') as f:
        image_data = f.read()

    file_name = Path(image_path).name
    mime_type = 'image/jpeg' if image_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
    base64_data = base64.b64encode(image_data).decode('utf-8')

    # Inject into browser
    await page.evaluate(
        """({ selector, fileName, mimeType, base64Data }) => {
            function b64ToUint8Array(b64) {
                const binary = atob(b64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) {
                    bytes[i] = binary.charCodeAt(i);
                }
                return bytes;
            }
            const input = document.querySelector(selector);
            const file = new File([b64ToUint8Array(base64Data)], fileName, { type: mimeType });
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        {
            'selector': input_selector,
            'fileName': file_name,
            'mimeType': mime_type,
            'base64Data': base64_data
        }
    )

# Usage
await upload_image(page, 'C:/path/to/photo.jpg', 'input[name="photo"]')
```

---

## Recipe 2: Multiple Files Upload

```python
async def upload_multiple_files(page, file_paths: list, selector: str = 'input[type="file"]'):
    """Upload multiple files (for multi-file input)."""
    files_data = []

    for path in file_paths:
        with open(path, 'rb') as f:
            data = f.read()

        mime = 'image/jpeg' if path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
        files_data.append({
            'name': Path(path).name,
            'base64': base64.b64encode(data).decode('utf-8'),
            'mime': mime
        })

    await page.evaluate(
        """({ selector, files }) => {
            function b64ToUint8Array(b64) {
                const binary = atob(b64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                return bytes;
            }
            const input = document.querySelector(selector);
            const dt = new DataTransfer();
            files.forEach(f => {
                const file = new File([b64ToUint8Array(f.base64)], f.name, { type: f.mime });
                dt.items.add(file);
            });
            input.files = dt.files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        {'selector': selector, 'files': files_data}
    )

# Upload 3 photos
await upload_multiple_files(
    page,
    ['photo1.jpg', 'photo2.png', 'photo3.jpg'],
    'input[name="photos"]'
)
```

---

## Recipe 3: Upload via File Chooser Dialog

```python
async def upload_via_file_chooser(page, button_selector: str, file_path: str):
    """Handle file chooser dialog triggered by button click."""
    async with page.expect_file_chooser() as fc_info:
        await page.click(button_selector)
    file_chooser = await fc_info.value
    await file_chooser.set_files(file_path)

# Usage: Click button → choose file
await upload_via_file_chooser(page, 'button#upload-btn', 'C:/docs/report.pdf')
```

---

## Recipe 4: Upload PDF Document

```python
async def upload_pdf(page, pdf_path: str, selector: str = 'input[type="file"]'):
    """Upload PDF file."""
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()

    base64_data = base64.b64encode(pdf_data).decode('utf-8')

    await page.evaluate(
        """({ selector, fileName, base64Data }) => {
            function b64ToUint8Array(b64) {
                const binary = atob(b64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                return bytes;
            }
            const input = document.querySelector(selector);
            const file = new File([b64ToUint8Array(base64Data)], fileName, { type: 'application/pdf' });
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        {
            'selector': selector,
            'fileName': Path(pdf_path).name,
            'base64Data': base64_data
        }
    )
    # Some sites need extra click after upload
    await page.wait_for_load_state('networkidle')
```

---

## Recipe 5: Upload from URL (No Base64 Needed)

```python
async def upload_from_url(page, file_url: str, selector: str = 'input[type="file"]'):
    """Direct upload from public URL (file must be accessible)."""
    await page.locator(selector).set_input_files(file_url)

# Usage - file must be publicly accessible
await upload_from_url(page, 'https://example.com/files/data.csv', 'input[name="csv"]')
```

---

## Recipe 6: Drag and Drop File Upload

```python
async def drag_and_drop_file(page, file_path: str, drop_zone_selector: str):
    """Simulate drag-and-drop file upload."""
    with open(file_path, 'rb') as f:
        file_data = f.read()

    base64_data = base64.b64encode(file_data).decode('utf-8')
    file_name = Path(file_path).name

    await page.evaluate(
        """({ selector, fileName, base64Data }) => {
            function b64ToUint8Array(b64) {
                const binary = atob(b64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                return bytes;
            }
            const dropZone = document.querySelector(selector);
            const file = new File([b64ToUint8Array(base64Data)], fileName, { type: 'application/octet-stream' });

            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);

            const events = ['dragenter', 'dragover', 'drop'];
            events.forEach(eventType => {
                const event = new DragEvent(eventType, {
                    bubbles: true,
                    cancelable: true,
                    dataTransfer: dataTransfer
                });
                dropZone.dispatchEvent(event);
            });
        }""",
        {
            'selector': drop_zone_selector,
            'fileName': file_name,
            'base64Data': base64_data
        }
    )

    await page.wait_for_load_state('networkidle')
```

---

## Recipe 7: Upload with Verification

```python
async def upload_with_check(page, file_path: str, selector: str, timeout: int = 30000):
    """Upload file and verify it was accepted."""
    file_name = Path(file_path).name

    # Upload
    await upload_image(page, file_path, selector)

    # Verify: Check if file name appears in UI
    try:
        await page.wait_for_selector(f'text={file_name}', timeout=timeout)
        print(f"✓ File '{file_name}' uploaded successfully")
        return True
    except:
        # Alternative: Check preview or file size element
        preview = await page.query_selector('.file-preview')
        if preview and file_name in await preview.text_content():
            print(f"✓ File '{file_name}' detected in preview")
            return True
        print(f"✗ File '{file_name}' not found after upload")
        return False
```

---

## Recipe 8: Upload Large Files (Chunked approach)

```python
async def upload_large_file(page, file_path: str, selector: str, chunk_size: int = 5_000_000):
    """Upload large file by splitting into chunks (if site supports chunked)."""
    # Some sites support multiple file inputs for chunked upload
    # This is a simplified example - adapt to your site's specific chunked upload API

    file_size = Path(file_path).stat().st_size
    if file_size < chunk_size:
        await upload_image(page, file_path, selector)
        return

    # For chunked uploads, you typically need to:
    # 1. Upload chunks via API (not through form)
    # 2. Assemble on server
    # This recipe assumes site has chunked upload endpoint

    print(f"File size {file_size} bytes exceeds {chunk_size}, using chunked upload API")

    # Example: Read chunk, upload via fetch API
    with open(file_path, 'rb') as f:
        chunk_num = 0
        while chunk := f.read(chunk_size):
            chunk_b64 = base64.b64encode(chunk).decode('utf-8')

            await page.evaluate(
                """({ chunk, chunkNum, totalChunks, fileName }) => {
                    // Call your site's chunked upload endpoint
                    return fetch('/api/upload-chunk', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ chunk, chunkNum, totalChunks, fileName })
                    });
                }""",
                {
                    'chunk': chunk_b64,
                    'chunkNum': chunk_num,
                    'totalChunks': (file_size + chunk_size - 1) // chunk_size,
                    'fileName': Path(file_path).name
                }
            )
            chunk_num += 1

    # 3. Complete upload
    await page.evaluate(
        """({ fileName }) => {
            return fetch('/api/upload-complete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fileName })
            });
        }""",
        {'fileName': Path(file_path).name}
    )
```

---

## Recipe 9: Upload with Progress Tracking

```python
async def upload_with_progress(page, file_path: str, selector: str, interval: float = 0.5):
    """Upload file and display progress (requires site-specific hooks)."""
    import time

    file_name = Path(file_path).name
    start_time = time.time()

    # Upload
    await upload_image(page, file_path, selector)

    # Monitor progress - check for progress indicator on page
    while True:
        await asyncio.sleep(interval)
        try:
            # Try to find progress bar or text
            progress_text = await page.text_content('.upload-progress, .progress-bar')
            if progress_text:
                print(f"[{time.time() - start_time:.1f}s] {progress_text}")
            else:
                break
        except:
            break

    elapsed = time.time() - start_time
    print(f"Upload completed in {elapsed:.2f}s")
```

---

## Recipe 10: Upload and Wait for Processing

```python
async def upload_and_wait_for_processing(page, file_path: str, selector: str,
                                         completion_selector: str = None,
                                         timeout: int = 120000):
    """Upload file and wait for server-side processing to complete."""
    await upload_image(page, file_path, selector)

    # Wait for processing indicators
    # Option 1: Wait for specific element indicating completion
    if completion_selector:
        await page.wait_for_selector(completion_selector, timeout=timeout)
        return True

    # Option 2: Wait for processing spinner to disappear
    try:
        await page.wait_for_selector('.processing, .spinner', timeout=5000)
        await page.wait_for_selector('.processing, .spinner', state='hidden', timeout=timeout)
        return True
    except:
        # No spinner found, assume complete after network idle
        await page.wait_for_load_state('networkidle')
        return True
```

---

## Key Tips for File Uploads in Browserless

1. **Always trigger `change` event** after setting files:
   ```javascript
   input.dispatchEvent(new Event('change', { bubbles: true }));
   ```

2. **Set correct MIME type** for the file:
   - images: `image/jpeg`, `image/png`, `image/webp`
   - documents: `application/pdf`, `text/plain`, `application/msword`
   - archives: `application/zip`, `application/x-zip-compressed`

3. **Convert base64 correctly**:
   ```javascript
   function b64ToUint8Array(b64) {
       const binary = atob(b64);
       const bytes = new Uint8Array(binary.length);
       for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
       return bytes;
   }
   ```

4. **Handle large files carefully** - base64 increases size by ~33%. Split into chunks if needed.

5. **Some sites require additional steps** after file selection:
   - Click "Upload" button
   - Fill additional form fields
   - Wait for thumbnail/preview to appear

6. **Validate upload success**:
   ```python
   # Check for preview
   preview = await page.query_selector('.file-preview, .thumbnail')
   assert preview is not None, "Upload failed - no preview"

   # Or check for file name in list
   file_name = Path(file_path).name
   await page.wait_for_selector(f'text="{file_name}"')
   ```

---

## Common Mistakes

❌ **DON'T**:
```python
# WRONG - local path won't work in remote browser
await input.set_input_files('/home/user/photo.jpg')
```

✅ **DO**:
```python
# Correct - use base64
await upload_image(page, 'photo.jpg', 'input[type="file"]')

# OR use public URL
await input.set_input_files('https://example.com/photo.jpg')
```

---

## Troubleshooting

**Problem**: File not appearing after upload
- Check: Did you dispatch `change` event?
- Check: Is the selector correct?
- Check: Is MIME type correct for the file?

**Problem**: "File too large" error
- Solution: Check site's file size limits
- Consider compressing images before upload
- Use chunked upload if supported

**Problem**: Upload succeeds but server rejects file
- Check: File format matches expected (e.g., JPG vs JPEG)
- Check: File is not corrupted
- Check: File dimensions (some sites limit image size)

**Problem**: Upload hangs indefinitely
- Increase timeout in `wait_for_load_state()`
- Check network tab in browser DevTools (if you have access)
- Verify file path exists before reading

---

## References

- Browserless File Transfers: https://docs.browserless.io/baas/features/file-transfers
- Browserless Uploading Files Recipe: https://docs.browserless.io/baas/recipes/uploading-files
- Playwright set_input_files docs: https://playwright.dev/python/docs/api/class-page#page-set-input-files
