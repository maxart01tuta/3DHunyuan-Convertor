---
name: 3d hunyuan project reference
description: Tencent 3D Hunyuan project overview - automation flow on 3d.hunyuan.tencent.com via Hyperbrowser
type: project
---

**Discovery date**: 2026-04-05

## Project Overview: 3DHunyuan-Download

The project automates uploading photos to **3d.hunyuan.tencent.com** (Tencent's 3D model generation service) and triggering generation using Hyperbrowser.

### Target Site

- **URL**: `https://3d.hunyuan.tencent.com/`
- **Service**: Tencent 3D Hunyuan — AI 3D model generation from photos
- **Auth**: Cookie-based authentication, loaded per profile
- **Browser**: Hyperbrowser.ai cloud sessions via Playwright CDP

### Project Structure

Files are in `D:\MAX\PYTHON\STOCK-PYTHON\3DHunyuan-Convertor`:

### Key Configuration (selectors & timeouts)

```
MAX_TIME = 180          # Max element wait timeout
WAIT_TIME = 3           # Inter-action pause
```

### Selectors

| Selector | XPath/Value | Purpose |
|----------|-------------|---------|
| `knopka_3d_photo` | `//label[@class='t-radio-button t-is-checked']` | Toggle 3D photo mode |
| `knopka_multiphoto` | `//div[contains(text(), '多张图片')]` | Switch to multi-photo mode |
| `knopka_open_popup_photos` | `//button[@class='hy-multiple-views-upload-v2']` | Open upload popup |
| `knopka_generate` | `//button[@class='sideBarLeft-generateBtn linear-gradien-button t-button t-button--variant-base t-button--theme-primary t-button--variant-base']` | Start generation |
| `input_photo_1` | `input[type='file'] >> nth=2` | Upload first photo |
| `input_photo_2` | `input[type='file'] >> nth=6` | Upload second photo |
| `input_photo_3` | `input[type='file'] >> nth=5` | Upload third photo |
| `text_upload_photo_success` | `(//div[@class='successImageBg'])[N]` | Confirm upload success |
| `text_generate_success` | `//div[@class='generate-dialog__generate_cont']` | Confirm generation done |

### Processing Flow (per session)

1. Create Hyperbrowser session (`client.sessions.create()`)
2. Connect Playwright via CDP → `session.ws_endpoint`
3. Load cookies (`context.add_cookies()`)
4. Navigate to `https://3d.hunyuan.tencent.com/`
5. Click 3D Photo mode
6. Click multi-photo option
7. Open popup for photo upload
8. Upload photo 1, photo 2, photo 3 (from `Upload/` folder)
9. Click Generate and wait for completion (`text_generate_success`)
10. Cleanup: `client.sessions.stop(session.id)`

### Cookie Management

- **Location**: `Cookies/Cookies-XX.json` files
- **Format**: `Cookies-01.json`, `Cookies-02.json`, etc.
- **Per session**: Load from the appropriate profile file via `context.add_cookies()`
- **Alternative**: Use Hyperbrowser Profiles (`profile={"id": "...", "persistChanges": true}`)

### Data Source

- **Excel file**: `Baza-3dhunyuan.xlsx`
- **Columns**: `BAZA_ID`, `BAZA_PROFILE`, `BAZA_PHOTO_1`, `BAZA_PHOTO_2`, `BAZA_PHOTO_3`, status tracking
- **Upload folder**: `Upload/` — contains JPG photos to upload

### Hyperbrowser Integration Notes

- **API key**: Environment variable `HYPERBROWSER_API_KEY`
- **SDK**: `pip install hyperbrowser`
- **Session**: Each Excel row = one Hyperbrowser session
- **Timeout**: Set `timeout_minutes` high enough (generation takes time)
- **Stealth**: `use_stealth=True` recommended for avoiding Tencent anti-bot
- **Proxy**: `proxy_country="CN"` or `"SG"` for proximity to Tencent servers
- **Cleanup**: ALWAYS call `client.sessions.stop(session.id)` in `finally` block
