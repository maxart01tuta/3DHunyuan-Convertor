# Planner Memory

## Project Structure
- Project: 3D Marketplaces Automation
- Task docs: `docs/NNN-english-slug.md` (numbered sequentially)
- Task list: `docs/000-tasks_list.md` — append completed tasks
- Python scripts: root directory `upload_*.py`
- Go scripts: `GO/upload_*.go`
- Blender scripts: `blender_*.py`
- Excel: `Baza-Marketplaces.xlsx` (sheets per marketplace)
- Upload folder: `Upload/` with {BAZA_ID}_* pattern files
- Browser profiles: `.browser-data-*` (persistent context)
- Cookies: `Cookies-{Marketplace}/Cookies-01.json`

## Conventions
- One main task with detailed sub-tasks only
- Sub-tasks must include: file path + line numbers OR specific insertion point
- Always include verification steps
- Final sub-task: "Test the script" or "Verify Excel update"
- Russian text for logs and comments, English for code
- Number task files sequentially from last in 000-tasks_list.md

## Go (Rod) Patterns
- Imports: "github.com/go-rod/rod", "github.com/go-rod/rod/lib/launcher", "github.com/xuri/excelize/v2"
- Browser launch: use Chrome with executable path or user-dir
- Timeouts: MINIMUM 10 minutes (600 seconds) for element waits
- Helper functions ALWAYS include:
  - `waitForElement(page, selector, maxWait)` - polls with visibility check
  - `safeClick(elem)` - scroll + click + error check
  - `safeInput(elem, text)` - clear + type char-by-char
  - `pageReloadSafe(page)` - reload + wait 10min + 3s stabilize
- Replace ALL `page.MustElement()` with `waitForElement()` + error handling
- Upload progress: use `waitForUploadProgressAdaptive()`
- Logging: `fmt.Printf("[%s] Message\n", time.Now().Format("15:04:05"))`

## Python (Playwright) Patterns
- Imports: `from playwright.sync_api import sync_playwright`
- Launch: `chromium.launch(headless=False, executable_path='C:\\...\\chrome.exe')`
- Universal selectors: detect `xpath:` prefix or `//` for XPath, else CSS
- Timeouts: `page.set_default_timeout(600000)`  # 10 minutes
- Element waits: `page.wait_for_selector(selector, timeout=600000)`
- Excel: `openpyxl.load_workbook()` for .xlsx files
- Context: reuse `.browser-data-3dexport` for persistence
- Logging: `print(f"[{datetime.now().strftime('%H:%M:%S')}] Message")`

## File Naming Conventions
- Main image: `{BAZA_ID}_bg.png` or `{BAZA_ID}_s.png`
- Wireframes: `{BAZA_ID}_wire_1.png`, `{BAZA_ID}_wire_2.png`
- Turntables: `{BAZA_ID}_0009.png`, `{BAZA_ID}_0019.png`, `{BAZA_ID}_0024.png`
- 3D models: `{BAZA_ID}.glb`, `{BAZA_ID}.fbx`, `{BAZA_ID}.obj`, `{BAZA_ID}.blend`
- ZIP packages: `{BAZA_ID}_glb.zip`, etc.

## Excel Integration
- Read: iterate rows where `BAZA_GOTOVO` is not "ГОТОВО"
- Write: update `BAZA_GOTOVO` to "ГОТОВО" after success
- Sheets: each marketplace has its own sheet name
- Columns: BAZA_ID, BAZA_TITLE, BAZA_DESCRIPTION, BAZA_KEYWORDS, BAZA_PRICE, BAZA_CATEGORY, etc.

## Marketplaces
- 3DExport: Complex form with 4 3D formats, many images, poly/vert counts
- CGTrader: Similar to 3DExport but different selectors
- Epic Fab: Uses "Made with AI" checkbox, 3D processing wait (20 min)
- Pinterest: Video upload with specific format (9:16)
- TurboSquid: Multiple categories, tax options
- ArtStation: Product + auto-post to social
- RenderHub: AI checkbox, multiple formats

## Steel.dev CDP Patterns
- Для Steel.connect_over_cdp() НЕ используйте параметры `is_local` или `slow_mo` - они вызываютBrowser.setDownloadBehavior, который Steel блокирует
- После переход�� на единый контекст (browser.contexts[0]) в Task 002_4, эти параметры стали избыточны
- Всегда используйте чистый вызов: `await playwright.chromium.connect_over_cdp(cdp_url)`
- Убедитесь, что bottleneck setDownloadBehavior не вызывается нигде (ни в connect, ни при создании контекстов)
- Upload файлов должен использовать Steel Files API (`session.files.upload()`), а не setDownloadBehavior
- См. детали: `docs/002_5-fix-steel-cdp-connection-params.md`

## Testing Checklist
☐ Compile Go script (if applicable): `go build upload_*.go`
☐ Excel file accessible (not locked)
☐ Browser profile exists (for persistent context sites)
☐ Upload folder has test files with correct naming
☐ Chrome executable path correct
☐ Logs appear in Russian
☐ Status updates to "ГОТОВО" after completion
☐ No leftover browser processes

