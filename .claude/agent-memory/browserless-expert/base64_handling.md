# Base64 Image & File Handling for Browserless

## Why Base64?

Browserless browsers run on remote servers. Local file paths (`C:\photo.jpg`) don't exist there. Base64 encoding lets you embed file data directly into JavaScript code executed inside the browser.

---

## Basic Base64 Conversion

### Encode file to base64 (Python)
```python
import base64
from pathlib import Path

def file_to_base64(file_path: str) -> str:
    """Convert file to base64 string."""
    with open(file_path, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode('utf-8')

# Usage
base64_str = file_to_base64('photo.jpg')
print(f"Base64 length: {len(base64_str)} chars")
```

### Decode base64 back to file (Python)
```python
def base64_to_file(base64_str: str, output_path: str):
    """Save base64 string as file."""
    data = base64.b64decode(base64_str)
    with open(output_path, 'wb') as f:
        f.write(data)

# Usage
base64_to_file(base64_str, 'output.jpg')
```

---

## Recipe 1: Convert Image to Base64 in Browser

```javascript
// In browser console or page.evaluate()
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
const img = new Image();

img.onload = function() {
    canvas.width = img.width;
    canvas.height = img.height;
    ctx.drawImage(img, 0, 0);

    // Get base64 (default PNG)
    const base64 = canvas.toDataURL('image/jpeg', 0.9); // quality 0-1
    console.log(base64);  // "data:image/jpeg;base64,/9j/4AAQ..."
};

img.src = 'data:image/png;base64,iVBORw0KGgoAAAANS...';  // or URL
```

---

## Recipe 2: Upload Base64 Image as File

```javascript
// Convert base64 to Uint8Array, create File, upload via DataTransfer
function base64ToUint8Array(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
}

function uploadBase64File(base64Data, fileName, mimeType, selector) {
    const input = document.querySelector(selector);
    const file = new File([base64ToUint8Array(base64Data)], fileName, {
        type: mimeType
    });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    input.files = dataTransfer.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
}

// Usage from Python:
await page.evaluate('''({selector, fileName, mimeType, base64Data}) => {
    function base64ToUint8Array(b64) {
        const binary = atob(b64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        return bytes;
    }
    const input = document.querySelector(selector);
    const file = new File([base64ToUint8Array(base64Data)], fileName, {type: mimeType});
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
})''', {
    'selector': 'input[type="file"]',
    'fileName': 'photo.jpg',
    'mimeType': 'image/jpeg',
    'base64Data': base64_str  # from Python
})
```

---

## Recipe 3: Download Image as Base64

```python
async def download_image_as_base64(page, image_selector: str) -> str:
    """Download image from page and return as base64."""
    # Get image src (could be data URL or regular URL)
    src = await page.get_attribute(image_selector, 'src')

    if src.startswith('data:'):
        # Already base64 - extract it
        base64_data = src.split(',')[1]
        return base64_data

    # Fetch image via Playwright request
    response = await page.request.get(src)
    image_bytes = await response.body()
    base64_str = base64.b64encode(image_bytes).decode('utf-8')

    return base64_str

# Usage
base64_img = await download_image_as_base64(page, 'img#profile-pic')
# Save to file
with open('profile.jpg', 'wb') as f:
    f.write(base64.b64decode(base64_img))
```

---

## Recipe 4: Convert Base64 to Blob URL

```python
async def base64_to_blob_url(page, base64_str: str, mime_type: str = 'image/jpeg') -> str:
    """Convert base64 to blob URL in browser."""
    blob_url = await page.evaluate(
        """({ base64, mimeType }) => {
            const byteCharacters = atob(base64);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: mimeType });
            return URL.createObjectURL(blob);
        }""",
        {'base64': base64_str, 'mimeType': mime_type}
    )
    return blob_url

# Usage
blob_url = await base64_to_blob_url(page, base64_str)
# Now you can use blob_url as image src: <img src="{blob_url}">
```

---

## Recipe 5: Resize/Compress Image Before Upload

```python
from PIL import Image
import io
import base64

def resize_and_encode_image(file_path: str, max_size: tuple = (1920, 1080),
                           quality: int = 85, format: str = 'JPEG') -> str:
    """
    Resize image and convert to base64.
    Reduces file size before sending to Browserless.
    """
    with Image.open(file_path) as img:
        # Resize if needed
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format=format, quality=quality, optimize=True)
        image_bytes = buffer.getvalue()

    # To base64
    return base64.b64encode(image_bytes).decode('utf-8')

# Usage
small_base64 = resize_and_encode_image('large_photo.jpg', max_size=(1280, 720))
# Then upload to Browserless via evaluate()
```

---

## Recipe 6: Multiple Images to Base64 Array

```python
def files_to_base64_batch(file_paths: list) -> list:
    """Convert multiple files to base64 list."""
    result = []
    for path in file_paths:
        with open(path, 'rb') as f:
            data = f.read()
        mime = 'image/jpeg' if path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
        result.append({
            'name': Path(path).name,
            'base64': base64.b64encode(data).decode('utf-8'),
            'mime': mime,
            'size': len(data)
        })
    return result

# Upload multiple
files = files_to_base64_batch(['img1.jpg', 'img2.png', 'img3.jpg'])
await page.evaluate(
    """({ files }) => {
        const input = document.querySelector('input[type="file"][multiple]');
        const dt = new DataTransfer();
        files.forEach(f => {
            const bytes = Uint8Array.from(atob(f.base64), c => c.charCodeAt(0));
            const file = new File([bytes], f.name, { type: f.mime });
            dt.items.add(file);
        });
        input.files = dt.files;
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }""",
    {'files': files}
)
```

---

## Recipe 7: Capture Screenshot as Base64

```python
async def screenshot_to_base64(page, full_page: bool = False,
                               format: str = 'png') -> str:
    """Take screenshot and return as base64 string."""
    screenshot_bytes = await page.screenshot(full_page=full_page, type=format)
    base64_str = base64.b64encode(screenshot_bytes).decode('utf-8')
    return base64_str

# Get base64 with data URL prefix
base64_img = await screenshot_to_base64(page)
data_url = f"data:image/png;base64,{base64_img}"

# Send to API or display
print(f"Data URL: {data_url[:100]}...")
```

---

## Recipe 8: Convert Base64 PDF

```python
async def upload_pdf_base64(page, pdf_path: str, selector: str):
    """Upload PDF from local file via base64."""
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()

    base64_str = base64.b64encode(pdf_data).decode('utf-8')
    file_name = Path(pdf_path).name

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
            'fileName': file_name,
            'base64Data': base64_str
        }
    )
```

---

## Recipe 9: Validate Base64 Data

```python
def validate_base64(base64_str: str) -> bool:
    """Check if string is valid base64."""
    try:
        # Remove data URL prefix if present
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]

        # Try to decode
        decoded = base64.b64decode(base64_str, validate=True)

        # Check if decodes to reasonable size
        return len(decoded) > 0
    except Exception:
        return False

def get_base64_info(base64_str: str) -> dict:
    """Get information about base64 string."""
    # Remove prefix
    if base64_str.startswith('data:'):
        parts = base64_str.split(',')
        mime = parts[0].split(';')[0].split(':')[1]
        base64_data = parts[1]
    else:
        mime = 'unknown'
        base64_data = base64_str

    decoded = base64.b64decode(base64_data)
    size = len(decoded)

    return {
        'mime_type': mime,
        'size_bytes': size,
        'size_kb': size / 1024,
        'size_mb': size / (1024 * 1024),
        'base64_length': len(base64_data),
        'valid': True
    }

# Usage
info = get_base64_info(base64_str)
print(f"Size: {info['size_kb']:.2f} KB, MIME: {info['mime_type']}")
```

---

## Recipe 10: Base64 for Canvas Drawing

```python
async def draw_base64_on_canvas(page, base64_str: str, canvas_selector: str = 'canvas'):
    """Draw base64 image onto canvas element."""
    await page.evaluate(
        """({ base64, selector }) => {
            const canvas = document.querySelector(selector);
            const ctx = canvas.getContext('2d');
            const img = new Image();

            img.onload = function() {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
            };

            img.src = 'data:image/png;base64,' + base64;
        }""",
        {'base64': base64_str, 'selector': canvas_selector}
    )

    await page.wait_for_timeout(1000)  # Wait for image to load
```

---

## MIME Types Reference

| Extension | MIME Type |
|-----------|-----------|
| .jpg, .jpeg | image/jpeg |
| .png | image/png |
| .gif | image/gif |
| .webp | image/webp |
| .svg | image/svg+xml |
| .pdf | application/pdf |
| .txt | text/plain |
| .csv | text/csv |
| .json | application/json |
| .zip | application/zip |
| .mp3 | audio/mpeg |
| .mp4 | video/mp4 |

---

## Performance Tips

1. **Compress before encoding** - Smaller file = less base64 overhead
   ```python
   from PIL import Image
   img = Image.open('photo.jpg')
   img.save('photo_compressed.jpg', quality=80)  # 20% smaller
   ```

2. **Use appropriate format** - WebP is 25-35% smaller than JPEG

3. **Batch upload efficiently** - Combine multiple files into single evaluate() call

4. **Clean up DataTransfer** - Browser may hold references; create fresh each time

5. **Monitor base64 size** - 1MB file becomes ~1.33MB base64 (33% overhead)

---

## Common Issues & Solutions

### Issue: "Failed to execute 'createObjectURL' on 'DOMWindow'"
**Cause**: Blob too large or invalid base64
**Fix**: Validate base64 string, check file size

### Issue: Image displays corrupted after upload
**Cause**: Incorrect mimeType or broken base64 string
**Fix**: Verify base64_data is pure base64 without data: prefix when passing to atob()

```python
# Remove data URL prefix
if base64_str.startswith('data:image/jpeg;base64,'):
    base64_str = base64_str.split(',')[1]
```

### Issue: Upload is very slow
**Cause**: Large file, network latency
**Fix**: Compress images, use smaller resolution, consider chunked upload

### Issue: File uploads but site says "invalid format"
**Cause**: Wrong mimeType
**Fix**: Match mimeType exactly to file type

---

## Quick Reference Functions

```python
# Python helpers
import base64
from pathlib import Path

def to_base64(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def from_base64(b64_str: str, output_path: str):
    with open(output_path, 'wb') as f:
        f.write(base64.b64decode(b64_str))

def get_mime_type(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    types = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.gif': 'image/gif',
        '.pdf': 'application/pdf'
    }
    return types.get(ext, 'application/octet-stream')
```

```javascript
// JavaScript helpers (for page.evaluate)
function base64ToUint8Array(b64) {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
}

function uploadBase64ToInput(base64, fileName, mimeType, selector) {
    const input = document.querySelector(selector);
    const file = new File([base64ToUint8Array(base64)], fileName, { type: mimeType });
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
}
```

---

## See Also

- File Upload Recipes: `file_upload_recipes.md`
- REST API Examples (for file downloads): `rest_api_quickstart.md`
- Browserless Docs: https://docs.browserless.io/baas/features/file-transfers
