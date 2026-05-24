---
name: Fix #2 — OBJ dropdown click timeout after GLB download
description: page.click on dropdown fails with 180s timeout after GLB download; fixed with Escape reset + evaluate click
type: project
---

## Problem

After successful GLB download, OBJ download step fails with `page.click` timeout on the dropdown button (`func_obj.py` line 28). Error: "waiting for locator(dropdown_btn)... locator resolved to <button>" — element IS found, but click can't complete.

Logs: 17:05:11 GLB saved, 17:05:33 OBJ dropdown click failed with 180s timeout.

## Root cause

`page.click()` in Playwright runs full actionability checks (visibility, scroll-into-view, stable, no overlay). On cloud browsers (Hyperbrowser CDP) between sequential downloads, the WebGL 3D canvas or a lingering download toast can cover the dropdown button, causing actionability wait to hang for the full 180s timeout.

## Solution

Two-part fix applied to `func_obj.py`, `func_fbx.py`:

1. **Escape key reset** — press Escape twice with 1s gaps to close any open dropdown/toast/state left from previous download
2. **evaluate click** — use `page.evaluate()` with XPath to dispatch a JS click, bypassing Playwright's actionability checks entirely:

```python
await page.evaluate("""(selector) => {
    const el = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    if (el && typeof el.click === 'function') el.click();
}""", knopka_dropdown)
```

`func_glb.py` uses evaluate click without Escape (it's first in the chain).

## Why not other approaches

- **scrollIntoView** — doesn't help if a 3D canvas overlay covers the element
- **page reload** — loses session state, cookies, navigation context — too expensive
- **force: true on click** — Playwright doesn't have a force param on click; `evaluate` is the correct bypass mechanism
- **locator.click({force:true})** — Playwright Python API doesn't support this in the way Playwright TS does

## When this breaks

If the site changes to use event delegation where `el.click()` doesn't work, we'll need `dispatchEvent('click')` instead. Current button uses standard onClick/onClick handler, so native click works.
