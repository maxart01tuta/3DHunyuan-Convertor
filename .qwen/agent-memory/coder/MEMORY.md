# Coder Memory

## Project Structure
- Python scripts: root directory, named `upload_*.py`, `blender_*.py`, `convert_*.py`
- Go scripts: `GO/` directory, named `upload_*.go`
- Browser automation: Playwright (Python), Rod (Go)
- Blender: Python API (bpy) for 3D processing
- Excel: `Baza-Marketplaces.xlsx` with multiple sheets
- Upload folder: `Upload/` with {BAZA_ID}_* files

## Implementation Workflow
1. Read the task plan from `docs/NNN-*.md` created by planner
2. Check `docs/000-tasks_list.md` to understand current task number
3. Consult `searcher` agent if need examples/docs
4. Implement EXACTLY what the plan specifies
5. Write to proper files with correct paths
6. Use Russian for logs, English for code/variables
7. After implementation: collect diffs and use giter agent to commit

## Python (Playwright) Patterns

### Basic Structure
```python
from playwright.sync_api import sync_playwright
from datetime import datetime
import os

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Начало выполнения")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            executable_path='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        )

        # For persistent login (3DExport)
        context = browser.new_context(
            user_data_dir=".browser-data-3dexport"
        )

        page = context.new_page()
        page.set_default_timeout(600000)  # 10 minutes

        # Universal selector helper
        def get_locator(page, selector):
            if selector.startswith('xpath:') or selector.startswith('//'):
                return page.locator(f"xpath={selector}")
            return page.locator(selector)

        # Your automation logic here...

        context.close()
        browser.close()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Завершено успешно")

if __name__ == "__main__":
    main()
```

### Excel Integration
```python
from openpyxl import load_workbook

wb = load_workbook("Baza-Marketplaces.xlsx")
ws = wb["3DExport"]  # or "CGTrader", "Epic", etc.

# Read rows where BAZA_GOTOVO is not "ГОТОВО"
for row in ws.iter_rows(min_row=2, values_only=True):
    baza_id = row[0]  # adjust index
    baza_gotovo = row[...]  # find correct column
    if baza_gotovo != "ГОТОВО":
        # process this product

# Update status after success
ws.cell(row=row_num, column=col_num, value="ГОТОВО")
wb.save("Baza-Marketplaces.xlsx")
```

### Universal Selector Pattern
```python
def get_locator(page, selector):
    """Accepts CSS selectors or XPath (with 'xpath:' prefix or starting with '//')"""
    if selector.startswith('xpath:') or selector.startswith('//'):
        return page.locator(f"xpath={selector}")
    return page.locator(selector)

# Usage:
elem = get_locator(page, "button[type='submit']")
elem.click()
```

### File Upload
```python
page.set_input_files(
    "input[type='file']",
    "Upload/3d-001.glb"
)
```

### Iframe Handling
```python
iframe = page.frame(url="...")  # or by name/index
iframe.locator("selector").click()
```

### Wait Strategies
```python
# Wait for element to be visible
page.wait_for_selector("css=selector", timeout=600000, state="visible")

# Wait for navigation
page.wait_for_url("**/success", timeout=600000)

# Wait for upload progress (custom)
def wait_for_upload(page, progress_selector, target_percent=95):
    import time
    start = time.time()
    while time.time() - start < 600:
        try:
            progress_text = page.locator(progress_selector).text_content()
            if "100%" in progress_text or "Complete" in progress_text:
                return True
        except:
            pass
        time.sleep(2)
    return False
```

## Go (Rod) Patterns

### Basic Structure
```go
package main

import (
    "fmt"
    "log"
    "time"
    "github.com/go-rod/rod"
    "github.com/go-rod/rod/lib/launcher"
    "github.com/go-rod/rod/lib/actions"
    "github.com/xuri/excelize/v2"
)

func main() {
    log.Printf("[%s] Начало выполнения", time.Now().Format("15:04:05"))

    // Launch browser
    u := launcher.New().
        Bin("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe").
        MustLaunch()
    browser := rod.New().ControlURL(u).MustConnect()
    page := browser.MustPage()
    page.SetWindowSize(1920, 1080)
    page.Timeout(10 * time.Minute)

    // Your automation logic here...

    browser.MustClose()
    log.Printf("[%s] Завершено успешно", time.Now().Format("15:04:05"))
}
```

### Helper Functions (REQUIRED)
See `GO/upload_3dexport.go` lines ~80-150 for reference implementations.

```go
// waitForElement polls for element with visibility check
func waitForElement(page *rod.Page, selector string, maxWait time.Duration) (*rod.Element, error) {
    // Implementation: poll every 500ms, check IsVisible
    // Return element or error after maxWait
}

// safeClick scrolls and clicks with error handling
func safeClick(elem *rod.Element) error {
    // Scroll into view, wait, click, check result
    return nil
}

// safeInput clears and types character-by-character
func safeInput(elem *rod.Element, text string) error {
    // Clear, focus, type slowly for reliability
    return nil
}

// pageReloadSafe reloads with stabilization
func pageReloadSafe(page *rod.Page) {
    page.MustReload()
    page.Timeout(10 * time.Minute).MustWaitLoad()
    time.Sleep(3 * time.Second)
}
```

### Excel Integration
```go
import "github.com/xuri/excelize/v2"

func readExcel(filePath, sheetName string) ([][]string, error) {
    f, err := excelize.OpenFile(filePath)
    if err != nil {
        return nil, err
    }
    defer f.Close()

    rows, err := f.GetRows(sheetName)
    if err != nil {
        return nil, err
    }
    return rows, nil
}

func updateCell(filePath, sheetName string, row, col int, value string) error {
    f, err := excelize.OpenFile(filePath)
    if err != nil {
        return err
    }
    defer f.Close()

    cell, err := excelize.CoordinatesToCellName(col, row)
    if err != nil {
        return err
    }

    f.SetCellValue(sheetName, cell, value)
    return f.Save()
}
```

### Universal Selector Pattern
```go
// Rod uses CSS selectors primarily
// For XPath, use page.ElementX("xpath=...")
// For CSS, use page.Element(selector)

elem, err := page.Element("button[type='submit']")
if err != nil {
    return fmt.Errorf("element not found: %v", err)
}

// XPath:
elem, err := page.ElementX("//button[@type='submit']")
```

### File Upload
```go
// Rod handles file uploads via input elements
elem, _ := page.Element("input[type='file']")
elem.MustUploadFiles("Upload/3d-001.glb")

// Or with error handling:
if elem, err := waitForElement(page, "input[type='file']", 10*time.Minute); err == nil {
    if err := safeUpload(elem, "file.glb"); err != nil {
        log.Printf("Upload failed: %v", err)
    }
}
```

## Blender Patterns

### Basic Script Structure
```python
import bpy
import os
from datetime import datetime

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def main():
    log("Начало рендеринга")

    # Clear scene (optional)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Import 3D model
    model_path = os.path.abspath("Upload/3d-001.glb")
    bpy.ops.import_scene.gltf(filepath=model_path)

    # Set up camera
    camera = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    bpy.context.scene.camera = camera
    camera.location = (5, -5, 5)
    camera.rotation_euler = (1.2, 0, 0.785)

    # Set up lighting
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))

    # Render settings
    scene = bpy.context.scene
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = os.path.abspath("Render/output.png")

    # Render
    bpy.ops.render.render(write_still=True)

    log("Рендеринг завершен")

if __name__ == "__main__":
    main()
```

### Run from Blender
```bash
blender --background --python blender_white_screenshot.py
```

Or via Blender UI: Scripting → Open → Run Script (Alt+P)

### Turnable Rotation
```python
import bpy
import math

scene = bpy.context.scene
object = bpy.context.selected_objects[0]

for angle in range(0, 360, 10):
    object.rotation_euler[2] = math.radians(angle)  # Z-axis
    scene.render.filepath = f"Render/frame_{angle:03d}.png"
    bpy.ops.render.render(write_still=True)
```

## File Naming Conventions

Files in `Upload/` folder must follow this pattern:
- `{BAZA_ID}_bg.png` - main thumbnail (white background)
- `{BAZA_ID}_s.png` - simplified thumbnail
- `{BAZA_ID}_wire_1.png`, `{BAZA_ID}_wire_2.png` - wireframe views
- `{BAZA_ID}_0009.png`, `{BAZA_ID}_0019.png`, `{BAZA_ID}_0024.png` - turnable angles
- `{BAZA_ID}.glb` - main 3D model (GL Transmission Format)
- `{BAZA_ID}.fbx` - FBX format
- `{BAZA_ID}.obj` - Wavefront OBJ
- `{BAZA_ID}.blend` - Blender native
- `{BAZA_ID}_glb.zip` - zipped package (optional)

Example: `3d-001_bg.png`, `3d-001.glb`, `3d-001_wire_1.png`

## Excel Structure

File: `Baza-Marketplaces.xlsx`

Sheets (one per marketplace):
- `3DExport`
- `CGTrader`
- `Epic` (for Epic Fab)
- `Pinterest`
- `TurboSquid`
- `ArtStation`
- `RenderHub`

Columns (may vary by sheet):
- `BAZA_ID` - ID (e.g., "3d-001")
- `BAZA_TITLE` - Product title
- `BAZA_DESCRIPTION` - Description (HTML allowed on some)
- `BAZA_KEYWORDS` - Tags (comma-separated)
- `BAZA_PRICE` - Price (number)
- `BAZA_CATEGORY` - Category path (e.g., "3D Models > Characters")
- `BAZA_POLYGONS` - Polygon count
- `BAZA_VERTICES` - Vertex count
- `BAZA_GOTOVO` - Status ("ГОТОВО" when uploaded)

**Reading logic:**
```python
# Python
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[status_col] != "ГОТОВО":
        # Process this product
```

**Writing logic:**
```python
ws.cell(row=excel_row, column=status_col, value="ГОТОВО")
wb.save("Baza-Marketplaces.xlsx")
```

## Common Pitfalls & Solutions

### Timeouts
**Problem**: Elements not found within default timeout.
**Solution**: Always set timeout to 10 minutes (600000 ms or 10*time.Minute). Use adaptive polling.

### Element not found
**Problem**: Selector doesn't match.
**Solution**: Check page source, use universal selectors, add page reloads, verify iframe context.

### File upload fails
**Problem**: Upload button not responding.
**Solution**: Use correct `input[type='file']` selector, ensure file path is absolute, wait for file to exist before upload.

### Excel locked
**Problem**: "Permission denied" when saving.
**Solution**: Ensure Excel application is closed. Use try-except with retry.

### Profile in use
**Problem**: Chrome profile already locked.
**Solution**: Close all Chrome windows before running. Use different profiles for Python and Go.

### Chrome executable path
**Problem**: Chrome not found.
**Solution**: Verify path, set `executable_path='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'`.

### Memory leaks (Go)
**Problem**: Browser processes accumulate.
**Solution**: Always call `browser.MustClose()` at the end. Use `defer` if possible.

### Russian encoding
**Problem**: Garbled characters in logs or Excel.
**Solution**: Use UTF-8 encoding everywhere. Python: `open(..., encoding='utf-8')`. Go: strings are UTF-8 by default.

## Testing Checklist

Before running any script:
- [ ] All required files exist in `Upload/` folder with correct naming
- [ ] Browser profile/cookies directory exists (if using persistence)
- [ ] `Baza-Marketplaces.xlsx` is not open in Excel application
- [ ] Chrome executable path is correct
- [ ] Go binary compiles without errors (for Go scripts): `go build GO/upload_*.go`
- [ ] Python dependencies installed: `pip install -r requirements.txt`

During/after execution:
- [ ] Logs appear in Russian with timestamps
- [ ] Browser interactions are visible (run with `headless=False`)
- [ ] After completion: `BAZA_GOTOVO` updated to "ГОТОВО" in Excel
- [ ] No zombie browser processes remain
- [ ] For Go: binary exits cleanly (no panic)
- [ ] For Python: script exits with code 0

## Useful References

- **Playwright Python**: https://playwright.dev/python/docs/
- **Rod (Go)**: https://go-rod.github.io/
- **Excelize (Go)**: https://xuri.me/excelize/
- **openpyxl (Python)**: https://openpyxl.readthedocs.io/
- **Blender Python API**: https://docs.blender.org/api/current/
- **bpy module reference**: https://docs.blender.org/api/current/bpy.ops.html

## Example Implementations (Study These)

- Simple and reliable: `upload_3dexport.py`, `upload_cgtrader.py`
- Go version patterns: `GO/upload_3dexport.go` (use helper functions from lines 80-150)
- Blender: `blender_turntable_screenshot.py`, `blender_white_screenshot.py`
- Task documentation: `docs/001-3dexport-uluchsheniye-zagruzki-files.md` (format)
