# Searcher Memory

## Project Context
- Project: 3D Marketplaces Automation (upload scripts + Blender processing)
- Primary languages: Python (Playwright), Go (Rod), Blender Python API (bpy)
- Documentation: `docs/*.md` contains detailed task implementations
- Code location: root directory for Python, `GO/` for Go scripts

## Search Priorities
When asked to search, follow this order:
1. Check `docs/*.md` files first - answers often already there
2. Use Exa for internet searches - verify with 3+ sources
3. Use Context7 for official library docs (playwright, rod, excelize, openpyxl, bpy)

## What to Search For
- **Playwright**: selectors, wait strategies, file upload, iframe handling, screenshots
- **Rod (Go)**: element finding, safe clicks, adaptive waits, browser launch options
- **Excel**: openpyxl (Python), excelize (Go) - reading/writing .xlsx
- **Blender**: bpy.context, bpy.ops, rendering, camera setups, material handling
- **Marketplaces**: specific CSS/XPath selectors for forms, upload buttons, validation
- **File handling**: image conversion, video generation, 3D format support

## Common Search Patterns
- Error messages: "element not found", "timeout", "file upload failed"
- Library version compatibility: Playwright 1.40+, Rod 0.114+, Go 1.21+
- Platform-specific quirks: Epic Fab's Made AI checkbox, Pinterest aspect ratios
- Performance: reducing memory, speeding up uploads, parallel processing

## Useful Resources (bookmark these)
- Playwright Python: https://playwright.dev/python/docs/
- Rod (Go): https://go-rod.github.io/
- Excelize: https://xuri.me/excelize/
- Blender Python API: https://docs.blender.org/api/current/
- Marketplaces' developer docs (if available)

## Past Search Log
(To be populated - summarize key findings from searches)
