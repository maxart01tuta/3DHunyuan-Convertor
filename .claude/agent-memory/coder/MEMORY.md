# Steel.dev CDP загрузка больших файлов

## Проблема с `page.set_input_files()` для файлов >50MB

При загрузке файлов в Steel.dev через Playwright:
- `page.set_input_files(selector, remote_path)` **НЕ работает** с файлами в Steel.dev session storage
- CDP протокол имеет лимит ~50MB для передачи файлов через base64 encoding

## Решение: CDP DOM.setFileInputFiles

Использовать CDP подход вместо `set_input_files`:

```python
# 1. Upload в Steel.dev session storage
with open(glb_path, 'rb') as f:
    session_file = await steel_client.sessions.files.upload(
        session_id=session_id, file=f
    )
remote_path = session_file.path  # Формат: /files/...

# 2. Валидация remote_path
if not remote_path or not remote_path.startswith('/files/'):
    raise RuntimeError(f"Неверный remote_path: {remote_path}")

# 3. Проверка видимости input элемента
input_visible = await page.evaluate("""
    () => {
        const el = document.querySelector('input#fb');
        return el && el.offsetParent !== null && !el.disabled;
    }
""")

# 4. CDP DOM.setFileInputFiles
context = page.context
cdp_session = await context.new_cdp_session(page)

dom_document = await cdp_session.send("DOM.getDocument")
root_node_id = dom_document["root"]["nodeId"]

input_node = await cdp_session.send("DOM.querySelector", {
    "nodeId": root_node_id,
    "selector": "input#fb"
})

await cdp_session.send("DOM.setFileInputFiles", {
    "files": [remote_path],
    "nodeId": input_node["nodeId"]
})

# 5. Очистка
await cdp_session.detach()
```

## CSS селекторы vs XPath

Для CDP `DOM.querySelector` нужен CSS селектор, не XPath:
- XPath: `//input[@id='fb']`
- CSS: `input#fb`

Всегда хранить оба варианта в config.py:
```python
input_upload = "//input[@id='fb']"      # Для Playwright waitForSelector
input_upload_css = "input#fb"           # Для CDP DOM.querySelector
```

## Обработка ошибок CDP

Специфичные ошибки:
- `"Not allowed"` — Chrome заблокировал DOM.setFileInputFiles
- `"No node with given id found"` — Input элемент исчез из DOM

## Файлы

- `BROWSER-STEEL/config.py` — добавлен `input_upload_css`
- `BROWSER-STEEL/func_upload.py` — полная реализация CDP подхода
