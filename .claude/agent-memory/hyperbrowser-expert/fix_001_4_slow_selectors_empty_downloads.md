---
name: Fix 001_4 - Slow selectors and 0-byte downloads
description: Root causes and fixes for 3-4 min wait times and empty downloads in Hyperbrowser CDP
type: project
---

## Problem 1: wait_for_selector takes 3-4 minutes per element

**Symptom:** Each `page.wait_for_selector()` takes 67-203 seconds even though elements are visible in `session.live_url`. Log showed:
- 11:16:35 "Открытие dropdown" (67s gap from previous)
- 11:19:58 "Выбор GLB" (203s gap)
- 11:23:22 "Клик на скачивание" (206s gap)

**Root cause 1 (CRITICAL):** Typo in `knopka_download` XPath selector in config.py:
```
"//button[@class='download-btn linear-gradien-button t-button ...']"
                                             ^^^^^^^ missing 't' - should be 'gradient'
```
This XPath NEVER matches, so `wait_for_selector` waits the full MAX_TIME (180s) every time.

**Root cause 2:** XPath `[@class='exact-string']` is brittle - any class change/order breaks it. CSS selectors like `button.download-btn` are faster through CDP.

**Root cause 3:** CDP WebSocket latency compounds with XPath evaluation overhead. `page.evaluate()` JS polling (document.querySelector) is 10-50x faster than `wait_for_selector` with XPath through CDP.

**Fix:** 
- Use CSS selectors instead of XPath
- Add `_wait_for_element_js()` helper: poll via `document.querySelector()` every 500ms
- Give JS poll a short timeout (15s), then fallback to standard `wait_for_selector`

## Problem 2: download.save_as() returns 0 bytes for 67+ MB files

**Symptom:** `await download.save_as(path)` creates a 0-byte file for large GLB files.

**Root cause:** `save_as()` transfers file data through the CDP WebSocket protocol. For large files, the serialization fails silently. The file exists on the remote Hyperbrowser server but cannot be transferred to local disk via CDP.

**Fix:** Extract download URL via JS (`btn.getAttribute('data-url') || btn.getAttribute('href')`) BEFORE clicking the download button, then download via HTTP streaming (httpx). This bypasses CDP entirely.

**Why `save_downloads=True` doesn't help:** It stores files in Hyperbrowser's cloud storage for later retrieval via `get_downloads_url()`, which requires post-session polling and zip extraction. Not compatible with real-time download handling during the session.

## Problem 3: aiohttp not installed in venv

**Symptom:** `No module named 'aiohttp'` when HTTP fallback triggers.

**Fix:** Replace aiohttp with httpx in `_download_via_http()`. httpx has async streaming (`aiter_bytes`) equivalent to aiohttp, is already a clean install (no compilation), and is added to requirements.txt.

## Files modified (001_4):
- `config.py` - CSS selectors instead of XPath, typo fix, added JS_POLL config
- `func_glb.py` - httpx fallback, JS polling, extract URL before click
- `func_obj.py` - same pattern
- `func_fbx.py` - same pattern
- `main.py` - added `import os` (was missing)
- `requirements.txt` - added httpx

## Before running:
- `cd HYPERBROWSER && . venv/Scripts/activate && pip install httpx`
