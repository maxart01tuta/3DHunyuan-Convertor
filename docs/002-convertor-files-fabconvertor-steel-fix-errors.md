# Задачи 002_1 - 002_N : Исправление ошибок Задачи 002

# ЗАДАЧИ 002_1
Теперь, когда анализ завершён и корневая проблема ясна, нужно представить пользователю краткий план исправлений и объяснить, чем он отличается от предыдущей задачи 002.## Анализ проблемы

**Что происходит:**
1. Файл `3d-582.glb` (70.7MB) **успешно** загружается в Steel.dev session storage через `upload_file()` API
2. Но сразу после этого ошибка при `page.set_input_files(remote_path)` — Playwright не может найти файл по пути `/files/25e4b0db-...`

**Корневая причина:**
`page.set_input_files()` работает только с **локальными** файлами на вашей машине. Файл уже в session VM Steel.dev, но Playwright через CDP не может обратиться к нему напрямую через `set_input_files()`.

---

## План исправления (3 шага)

### 1. **func_upload.py** — замена `set_input_files` на CDP `DOM.setFileInputFiles`

**Текущий код (строка 56):**
```python
await page.set_input_files(input_upload, remote_path)
```

**Заменить на:**
```python
# Получаем CDP сессию
cdp_session = await page.context.new_cdp_session(page)
# Находим input элемент через CDP
dom_document = await cdp_session.send("DOM.getDocument")
input_node = await cdp_session.send("DOM.querySelector", {
    "nodeId": dom_document["root"]["nodeId"],
    "selector": input_upload  # XPath нужно конвертировать в CSS
})
# Устанавливаем файл через CDP
await cdp_session.send("DOM.setFileInputFiles", {
    "files": [remote_path],
    "nodeId": input_node["nodeId"]
})
```

**Важно:** XPath `//input[@id='fb']` нужно заменить на CSS селектор `input#fb` для CDP.

### 2. **config.py** — обновить селектор `input_upload`

```python
# Было:
input_upload = "//input[@id='fb']"
# Стало:
input_upload = "input#fb"  # CSS селектор для CDP
```

### 3. **func_upload.py** — добавить обработку ошибок CDP

Обернуть CDP вызовы в try/except с понятным сообщением об ошибке.

---

## Отличие от задачи 002

В **задаче 002** была общая миграция с Hyperbrowser.ai на Steel.dev — заменялись SDK, API вызовы, импорты. Но там **не рассматривалась проблема больших файлов >50MB** через CDP.

**Ключевое отличие:** задача 002 использовала стандартный `set_input_files()`, который работает ТОЛЬКО для малых файлов. Для файлов >50MB Steel.dev **требует** использование CDP `DOM.setFileInputFiles`, что **не было документировано** в предыдущей задаче. Это специфичная проблема работы с большими файлами в Steel.dev, а не общая миграция SDK.
Получил ответ от агента steel-expert, теперь нужно резюмировать ключевые моменты и уточняющие детали для пользователя.Отлично! Steel-expert подтвердил план и дал важные уточнения. Вот итоговая сводка:

---

## Анализ от Steel-expert

### ✅ План подтверждён — подход правильный

**Ключевые моменты от эксперта:**

1. **CDP `DOM.setFileInputFiles` — это официальный рекомендуемый метод** от Steel.dev для файлов >50MB. Текущий `set_input_files()` работает только для малых файлов.

2. **Файл после upload УЖЕ готов** — никаких дополнительных действий не нужно, `remote_path` сразу можно использовать.

3. **XPath → CSS обязателен** — `DOM.querySelector` не поддерживает XPath, только CSS селекторы.

### 🔧 Важные дополнения от эксперта:

**Добавить в код:**
- Проверку видимости input элемента перед CDP вызовом
- Валидацию `remote_path` (должен начинаться с `/files/`)
- Специфичную обработку ошибок CDP ("Not allowed", "No node found")
- `cdp_session.detach()` в `finally` для очистки ресурсов
- Таймауты на CDP операции

**Альтернатива для будущих оптимизаций:**
- **Global Files API** — если один и тот же GLB используется многократно, можно загрузить разово в global storage и монтировать в сессию при создании (экономит время upload)

### 📋 Итоговый план (с учётом дополнений):

1. **config.py** — добавить CSS селектор `input_upload_css = "input#fb"`
2. **func_upload.py** — полная замена блока `set_input_files` на CDP подход с проверками
3. Добавить обработку ошибок и очистку CDP сессии

**Отличие от задачи 002:** там была общая миграция SDK, но проблема больших файлов через CDP не рассматривалась — это новый специфичный баг.

---

 │ Файл          │ Что изменилось                                                                      │
    ├───────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
    │ config.py     │ Без изменений (синтаксис ✅)                                                        │
    │ **func_uploa... │ Добавлен клик knopka_vibor_type + WAIT_TIME после upload. CDP upload код НЕ тронут
      │
    │ func_obj.py   │ Переименован из func_convert_obj.py. Схема: клик OBJ → WAIT_TIME → convert → download
    │
    │ func_fbx.py   │ Переименован из func_convert_fbx.py. Схема: клик FBX → WAIT_TIME → convert → download
    │
    │ func_blend.py │ Переименован из func_convert_blend.py. Схема: клик BLEND → WAIT_TIME → convert → d...
    │
    │ main.py       │ Обновлены импорты, порядок вызовов соответствует твоей схеме                        │
    └───────────────┴─────────────────────────────────────────────────────────────────────────────────────┘


    Итоговая схема работы (по твоему плану):

      1 1. func_site      → зайти на сайт, ждать input_upload
      2 2. func_upload    → CDP upload GLB → WAIT_TIME → клик knopka_vibor_type → WAIT_TIME
      3 3. func_obj       → клик knopka_obj → WAIT_TIME → convert → download → {BAZA_ID}_obj.zip
      4
      5 4. func_site      → зайти на сайт заново
      6 5. func_upload    → CDP upload GLB → WAIT_TIME → клик knopka_vibor_type → WAIT_TIME
      7 6. func_fbx       → клик knopka_fbx → WAIT_TIME → convert → download → {BAZA_ID}_fbx.zip
      8
      9 7. func_site      → зайти на сайт заново
     10 8. func_upload    → CDP upload GLB → WAIT_TIME → клик knopka_vibor_type → WAIT_TIME
     11 9. func_blend     → клик knopka_blend → WAIT_TIME → convert → download → {BAZA_ID}_blend.zip
     12
     13 10. func_screenshoot → скриншот
     14 11. Проверка файлов → статус ГОТОВО → закрытие браузера
===============
# ЗАДАЧА 002_2:
Теперь представлю короткий план пользователю на основе анализа — две проблемы и их решения, и чем это отличается от задачи 002.## Анализ проблемы

**Из логов:**
1. `[20:05:44]` "Ожидание завершения конвертации..." → сразу "Скачивание архива"
2. `download.failure()` — **coroutine object был never awaited** — пропущен `await`
3. Download начался СРАЗУ после появления кнопки, но конвертация ещё не завершила

**Корневая причина:**
- `wait_for_element(knopka_download)` находит элемент в DOM, но кнопка может быть **disabled** или без `href` — сайт показывает кнопку заранее
- `download.failure()` — async метод, требует `await`

---

## План исправления (2 шага)

### 1. **func_obj.py / func_fbx.py / func_blend.py** — исправить проверку готовности download кнопки

**Было:**
```python
await wait_for_element(page, knopka_download, timeout=MAX_TIME)
```

**Стало:**
```python
# Ждём пока кнопка станет АКТИВНОЙ (enabled и с href)
print(f"[{_ts()}] 3. Ожидание готовности кнопки Download...")
await page.wait_for_function("""
    () => {
        const el = document.querySelector('a#yj');
        return el && el.href && !el.classList.contains('disabled');
    }
""", timeout=MAX_TIME * 1000)
await asyncio.sleep(WAIT_TIME)  # доп. пауза перед кликом
```

### 2. **func_obj.py / func_fbx.py / func_blend.py** — исправить `download.failure()`

**Было:**
```python
if download.failure():
    raise RuntimeError(f"Download failed: {download.failure()}")
```

**Стало:**
```python
failure = await download.failure()
if failure:
    raise RuntimeError(f"Download failed: {failure}")
```

---

## Отличие от задачи 002

В **задаче 002** была миграция SDK + CDP upload для больших файлов. Здесь **два других бага**:
1. **async/await ошибка** — `download.failure()` без `await` (кодинг ошибка)
2. **Слишком ранняя проверка** — `wait_for_element` находит disabled кнопку (логика ожидания)

Это **не связано** с предыдущей миграцией.
===========
# ЗАДАЧА 002_3
✦ Понял! Проблема в том, что проверка el.href проходит слишком рано — у кнопки href уже есть сразу после
    нажатия Convert, но это ещё не реальный URL файла. Нужно ждать пока href станет полным URL (начинается с
    http/https), что означает что сервер реально подготовил файл для скачивания.

    Нужно изменить проверку: ждать пока el.href содержит "http" (реальный URL, а не placeholder).

  ✦ Теперь понял проблему. Кнопка имеет href сразу после нажатия Convert, но это placeholder. Нужно ждать пока
     href станет реальным URL скачивания (содержит http). Делегирую coder'у:

  ✦ Все 3 файла прошли проверку синтаксиса. Теперь нужно подвести итог изменений.

  ✦ ✅ Исправлено. Теперь проверка ждёт реальный URL скачивания:

    Было: el.href — находил кнопку сразу (href мог быть placeholder)
    Стало: el.href.startsWith('http') — ждёт пока href станет полным URL (реальная ссылка на файл)

    Можно запускать тест!
==========
# ЗАДАЧА 002_4
   1. Click Convert
     2. Wait for Download button to have real URL (wait_for_function)
     3. WAIT_TIME
     4. Click Download → expect_download starts

    But the user says the order is confusing in logs. They see:
     - "Ожидание готовности кнопки Download..."
     - Then immediately "Скачивание архива" 14 seconds later

    The user wants a clear sequential flow:
     1. Click Convert
     2. Wait for Download button to appear (visible in DOM)
     3. Print "Download обнаружен"
     4. Click Download
     5. WAIT_TIME
     6. Then download happens

    The problem is that wait_for_function waits for the href to be real, but it doesn't print when it
    actually finds it. Then immediately after, it says "Скачивание архива" which is confusing.

    Let me rewrite the flow to be clearer:
     1. Click Convert
     2. Wait for Download button to be visible (wait_for_element) → print "Download обнаружен"
     3. Click Download
     4. WAIT_TIME
     5. Handle the download (expect_download already triggered by the click)

    Actually, the issue is that page.expect_download is an async context manager that captures downloads
    triggered INSIDE it. So the flow should be:
     1. Click Convert
     2. Wait for Download button (visible, has href)
     3. Print "Download обнаружен"
     4. Set up expect_download
     5. Click Download inside expect_download
     6. WAIT_TIME after download starts
 2. Запуск конвертации
     2 3. Ожидание кнопки Download...
     3    ✓ Download обнаружен!
     4 4. Клик на Download...
     5 5. Сохранение файла...
     6    ✓ Конвертация в OBJ завершена
=========