# ЗАДАЧА 002: Миграция с Hyperbrowser.ai на Steel.dev

**Дата:** 2026-04-08  
**Статус:** План  
**Цель:** Полная замена Hyperbrowser.ai на Steel.dev в проекте BROWSER-STEEL/ с сохранением всей функциональности

---

## Краткое резюме

Проект использует облачный браузер для загрузки GLB файлов на fabconvert.com и скачивания конвертированных результатов (OBJ, FBX, BLEND). Текущая реализация:

- **Hyperbrowser.ai** SDK для управления облачным браузером
- **Playwright** для навигации, загрузки файлов через `set_input_files()`, скачивания через `page.expect_download()`
- **Hyperbrowser Upload API** для загрузки больших файлов (>50MB) в сессию

Необходимо заменить все Hyperbrowser-специфичные вызовы на Steel.dev эквиваленты.

---

## Сводная таблица изменений

| Файл | Изменения | Строки | Приоритет |
|------|-----------|--------|----------|
| `requirements.txt` | hyperbrowser → steel-sdk | 4 | Критично |
| `browser.py` | Полная замена API, импорты, логи, CDP URL | 13-17, 41, 76-118, 147-189 | Критично |
| `func_upload.py` | Замена upload API, удаление HyperbrowserError | 12, 92, 105-114 | Критично |
| `main.py` | Обновление логов, имен переменных | 45, 52-54, 92, 111, 149, 157 | Обязательно |
| `browser.py` (опционально) | Адаптация get_downloads() под Steel (не используется) | 192-288 | Опционально |

---

## Детальный план изменений

### 1. BROWSER-STEEL/requirements.txt

**Что:** Замена пакета Hyperbrowser на Steel.dev SDK

**Строка 4:**
```diff
- hyperbrowser
+ steel-sdk
```

**Обоснование:** Steel.dev предоставляет официальный Python SDK `steel-sdk` вместо `hyperbrowser`. Playwright, openpyxl, Pillow, aiohttp остаются без изменений.

---

### 2. BROWSER-STEEL/browser.py

#### 2.1. Импорты (строки 1-17)

**До (строки 13-14):**
```python
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import CreateSessionParams
```

**После:**
```python
from steel import AsyncSteel, SteelError
```

**Обоснование:** Steel.dev использует `AsyncSteel` для асинхронных операций. `CreateSessionParams` не требуется - параметры передаются напрямую в `create()`. Добавляем `SteelError` для обработки ошибок API.

---

#### 2.2. Сигнатура launch_browser() (строка 41)

**До:**
```python
async def launch_browser() -> Tuple[object, Browser, BrowserContext, Page, Hyperbrowser, object]:
```

**После:**
```python
async def launch_browser() -> Tuple[object, Browser, BrowserContext, Page, AsyncSteel, object]:
```

**Обоснование:** Тип клиента меняется с `Hyperbrowser` на `AsyncSteel`.

---

#### 2.3. Создание клиента и сессии (строки 69-91)

**До (строки 75-88):**
```python
# Создать Hyperbrowser клиент (каждый раз новый для чистоты)
client = Hyperbrowser(api_key=api_key)

# Создать сессию Hyperbrowser с параметрами
print(f"[{datetime.now().strftime('%H:%M:%S')}] Создание Hyperbrowser сессии...")
session = client.sessions.create(
    CreateSessionParams(
        accept_cookies=True,
        save_downloads=True,
        use_stealth=True,
        screen={"width": 1920, "height": 1080},
        timeout_minutes=30,
    )
)
```

**После:**
```python
# Создать Steel.dev клиент
client = AsyncSteel(steel_api_key=api_key)

# Создать сессию Steel.dev с параметрами
print(f"[{datetime.now().strftime('%H:%M:%S')}] Создание Steel.dev сессии...")
session = await client.sessions.create(
    api_timeout=1800000,  # 30 минут в миллисекундах
    use_proxy=True  # Включить прокси Steel (гео-локация)
)
```

**Критические отличия:**
- `AsyncSteel(steel_api_key=...)` вместо `Hyperbrowser(api_key=...)`
- Параметры: только `api_timeout` и `use_proxy`. НЕТ `accept_cookies`, `save_downloads`, `use_stealth`, `screen`, `timeout_minutes`
- `await` обязателен (асинхронный метод)
- Таймаут в **миллисекундах** (1800000 = 30 мин), не в минутах

---

#### 2.4. CDP подключение (строка 96)

**До:**
```python
browser = await playwright.chromium.connect_over_cdp(session.ws_endpoint)
```

**После:**
```python
# CDP URL для Steel.dev (обязательно с API ключом и sessionId)
browser = await playwright.chromium.connect_over_cdp(
    f"wss://connect.steel.dev?apiKey={api_key}&sessionId={session.id}"
)
```

**Обоснование:** Steel.dev не возвращает `ws_endpoint`. CDP URL строится динамически с обязательными параметрами `apiKey` и `sessionId`.

---

#### 2.5. Создание контекста с stealth-настройками (строки 98-109)

**До:**
```python
# Ждать появления хотя бы одного контекста (timing issue mitigation)
start_wait = time.time()
while not browser.contexts and (time.time() - start_wait) < 5:
    await asyncio.sleep(0.5)
if not browser.contexts:
    raise RuntimeError("Hyperbrowser сессия не создала контексты за 5 секунд")
context = browser.contexts[0]
# Взять существующую страницу или создать новую
if context.pages:
    page = context.pages[0]
else:
    page = await context.new_page()
```

**После:**
```python
# Ждать появления хотя бы одного контекста (timing issue mitigation)
start_wait = time.time()
while not browser.contexts and (time.time() - start_wait) < 5:
    await asyncio.sleep(0.5)
if not browser.contexts:
    raise RuntimeError("Steel.dev сессия не создала контексты за 5 секунд")
context = browser.contexts[0]

# Настроить контекст для stealth-эффекта (аналог use_stealth=True)
# Steel.dev НЕ имеет встроенного stealth, настраивается через context options
await context.set_viewport_size({"width": 1920, "height": 1080})
# Дополнительные anti-detection настройки можно добавить через context.add_init_script()
# Например, переопределение navigator.webdriver:
# await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Взять существующую страницу или создать новую
if context.pages:
    page = context.pages[0]
else:
    page = await context.new_page()
```

**Обоснование:**
- Steel.dev не имеет автоматического stealth режима. Нужно явно настроить контекст.
- Минимальная настройка: `set_viewport_size()` для имитации реального разрешения.
- При необходимости можно добавить `add_init_script()` для удаления webdriver флагов (см. примечания в конце плана).
- Accept cookies и save downloads в Steel.dev делаются через Playwright (не требуется).

---

#### 2.6. Логирование Hyperbrowser → Steel.dev (строки 116, 142, 180)

**Строка 116:**
```diff
- print(f"[{datetime.now().strftime('%H:%M:%S')}] Успешное подключение к Hyperbrowser.ai")
+ print(f"[{datetime.now().strftime('%H:%M:%S')}] Успешное подключение к Steel.dev")
```

**Строка 142 (сообщение об ошибке):**
```diff
- error_msg = f"Не удалось подключиться к Hyperbrowser.ai после {max_retries} попыток. Последняя ошибка: {last_error}"
+ error_msg = f"Не удалось подключиться к Steel.dev после {max_retries} попыток. Последняя ошибка: {last_error}"
```

**Строка 180:**
```diff
- print(f"[{datetime.now().strftime('%H:%M:%S')}] Сессия Hyperbrowser {session_id} освобождена")
+ print(f"[{datetime.now().strftime('%H:%M:%S')}] Сессия Steel.dev {session_id} освобождена")
```

**Обоснование:** Полная замена упоминаний Hyperbrowser на Steel.dev в логах для ясности отладки.

---

#### 2.7. release_browser() - остановка сессии (строки 176-182)

**До (строки 177-180):**
```python
if hyperbrowser_client and session_id:
    # Hyperbrowser SDK stop() - синхронный метод (на 2026-04-01)
    hyperbrowser_client.sessions.stop(session_id)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Сессия Hyperbrowser {session_id} освобождена")
```

**После:**
```python
if steel_client and session_id:
    # Steel.dev: корректное освобождение сессии (асинхронный метод)
    await steel_client.sessions.release(session_id)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Сессия Steel.dev {session_id} освобождена")
```

**Критические отличия:**
- Метод `stop()` → `release()`
- `await` обязателен
- `release()` возвращает сессию в пул для повторного использования, `terminate()` убивает сразу (используйте release всегда!)
- Не calling release → утечка ресурсов на Steel серверах

---

#### 2.8. Функция get_downloads() (строки 192-288) - ОПЦИОНАЛЬНО

**Текущее состояние:** Функция нигде не вызывается (фактически мертвый код). Содержит Hyperbrowser специфичные вызовы: `client.sessions.get_downloads_url(session_id)`.

**Рекомендация:** Оставить без изменений (как legacy код) с комментарием в начале функции:
```python
async def get_downloads(...):
    """
    ⚠️ DEPRECATED: Эта функция использует Hyperbrowser Cloud Storage API.
    В текущей архитектуре скачивание происходит через page.expect_download()
    и НЕ требует этого метода.
    """
```

**Обоснование:** Пользователь просил "не буирай" (не выбрасывать). Функция может пригодиться для будущих сценариев, но для текущей логики (скачивание ZIP через Playwright) не требуется. Steel.dev аналог `get_downloads_url()` отсутствует - downloads обрабатываются на уровне страницы.

---

### 3. BROWSER-STEEL/func_upload.py

#### 3.1. Удаление импорта HyperbrowserError (строка 12)

**До:**
```python
from hyperbrowser.exceptions import HyperbrowserError
```

**После:**
```python
# Удалить строку полностью (импорт не требуется)
```

**Обоснование:** Steel.dev использует свою иерархию исключений (`SteelError`, `RateLimitError`, `ValidationError`). Для общего обработчика достаточно `except Exception`.

---

#### 3.2. Параметр hb_client → steel_client (строка 51)

**До:**
```python
async def run(page, hb_client, session_id: str, baza_id: str):
```

**После:**
```python
async def run(page, steel_client, session_id: str, baza_id: str):
```

**Обоснование:** Переименование для ясности. Изменение имени параметра не ломает обращение по ключевому слову, но улучшает читаемость.

---

#### 3.3. Upload файла через Steel API (строки 87-98)

**До (строки 90-94):**
```python
# ⭐ Upload файла в сессию через Hyperbrowser API (обход CDP лимита 50MB)
print(f"[{_ts()}] → Загрузка в Hyperbrowser session storage...")
upload_resp = await hb_client.sessions.upload_file(session_id, upload_path)
remote_path = upload_resp.file_path
print(f"[{_ts()}] ✓ Файл загружен в сессию: {remote_path}")

# Установка input на remote файл (уже внутри сессии)
await page.set_input_files(input_upload, remote_path)
```

**После:**
```python
# ⭐ Upload файла в сессию через Steel.dev API (обход CDP лимита 50MB)
print(f"[{_ts()}] → Загрузка в Steel.dev session storage...")
with open(upload_path, 'rb') as f:
    session_file = await steel_client.sessions.files.upload(
        session_id=session_id,
        file=f
    )
remote_path = session_file.path
print(f"[{_ts()}] ✓ Файл загружен в сессию: {remote_path}")

# Установка input на remote файл (уже внутри сессии)
await page.set_input_files(input_upload, remote_path)
```

**Критические отличия:**
- `hb_client.sessions.upload_file(session_id, path)` → `steel_client.sessions.files.upload(session_id=..., file=f)`
- Требуется открыть файл в mode='rb' и передать file object (не путь)
- Возвращаемый объект: `SessionFile` с атрибутами `path`, `size`, `filename`. Используем `.path`
- Логи: "Hyperbrowser" → "Steel.dev"

---

#### 3.4. Обработка ошибок (строки 105-114)

**До:**
```python
except HyperbrowserError as e:
    if getattr(e, 'status_code', None) == 413:
        file_size = os.path.getsize(upload_path) / (1024 * 1024)
        raise RuntimeError(
            f"Файл {file_size:.1f}MB всё ещё слишком большой "
            f"для Hyperbrowser API (лимит ~64MB). "
            f"Увеличьте сжатие или обратитесь в поддержку Hyperbrowser."
        ) from e
    print(f"[{_ts()}] ✗ Ошибка Hyperbrowser: {type(e).__name__}: {e}")
    raise
```

**После:**
```python
except Exception as e:
    # Steel.dev file upload errors are generic (file size limit 100MB)
    # Let runtime error propagate with context
    file_size = os.path.getsize(upload_path) / (1024 * 1024)
    raise RuntimeError(
        f"Файл {file_size:.1f}MB не загружен в Steel.dev session. "
        f"Проверьте сжатие (лимит 100MB) или доступность сессии."
    ) from e
```

**Обоснование:**
- Убрать специфичную для Hyperbrowser обработку (status_code 413, их лимит ~64MB)
- Steel.dev имеет лимит 100MB на файл (из экспертизы)
- Общий `except Exception` достаточен - SteelError наследуется от Exception
- Сообщение об ошибке адаптировано под Steel.dev

---

#### 3.5. Удаление строки с упоминанием Hyperbrowser в комментарии (строка 53)

**До:**
```python
# Загрузка GLB файла через input[type=file] с использованием Hyperbrowser upload API.
```

**После:**
```python
# Загрузка GLB файла через input[type=file] с использованием Steel.dev upload API.
```

---

### 4. BROWSER-STEEL/main.py

#### 4.1. Импорты (без изменений, но убедиться что нет Hyperbrowser импортов)

Текущие импорты:
```python
import config
import baza
from browser import launch_browser, release_browser, wait_for_element
from func_site import run as func_site_run
from func_upload import run as func_upload_run
...
```

**Проверка:** Убедиться, что в `from browser import ...` нет прямого импорта `Hyperbrowser` или других классов. В текущем коде они не используются - только функции.

---

#### 4.2. Объявление переменных (строка 45)

**До:**
```python
hyperbrowser_client = None
```

**После:**
```python
steel_client = None
```

**Обоснование:** Переименование для соответствия новой терминологии.

---

#### 4.3. Запуск браузера - логи (строки 50-54)

**До:**
```python
# === 1. Запуск браузера Hyperbrowser.ai ===
print(f"[{_ts()}] Запуск браузера...")
playwright, browser, context, page, hyperbrowser_client, session = await launch_browser()
sid = session.id
print(f"[{_ts()}] Сессия создана: {sid}")
```

**После:**
```python
# === 1. Запуск браузера Steel.dev ===
print(f"[{_ts()}] Запуск браузера...")
playwright, browser, context, page, steel_client, session = await launch_browser()
sid = session.id
print(f"[{_ts()}] Сессия Steel.dev создана: {sid}")
```

**Изменения:**
- Комментарий: "Hyperbrowser.ai" → "Steel.dev"
- Присваивание: `hyperbrowser_client` → `steel_client`
- Лог: "Сессия создана" → "Сессия Steel.dev создана"

---

#### 4.4. Вызов func_upload_run (строки 73, 92, 111)

**До:**
```python
await func_upload_run(page, hyperbrowser_client, session.id, baza_id)
```

**После:**
```python
await func_upload_run(page, steel_client, session.id, baza_id)
```

**Изменения:** Переименование переменной `hyperbrowser_client` → `steel_client` во всех трёх местах.

---

#### 4.5. Закрытие браузера (строка 149)

**До:**
```python
await release_browser(playwright, browser, hyperbrowser_client, session.id if session else None)
```

**После:**
```python
await release_browser(playwright, browser, steel_client, session.id if session else None)
```

---

#### 4.6. Лог при старте main() (строка 157)

**До:**
```python
print(f"[{_ts()}] Скрипт FabConvert (Hyperbrowser.ai) запущен")
```

**После:**
```python
print(f"[{_ts()}] Скрипт FabConvert (Steel.dev) запущен")
```

---

### 5. ОБНОВЛЕНИЕ КОНТЕКСТА ДЛЯ STEALTH-РЕЖИМА (ДОПОЛНИТЕЛЬНО)

В `browser.py`, после создания `context = browser.contexts[0]` (строка 104), добавьте настройку stealth через `add_init_script()`:

```python
# Добавить anti-detection скрипт (опционально, но рекомендуется)
stealth_script = """
// Remove webdriver property
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
// Other anti-detection tricks
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});
"""
await context.add_init_script(stealth_script)
```

**Расположение:** После строки 109 (перед `if context.pages:`)

**Обоснование:** Steel.dev не имеет built-in stealth. Этот скрипт помогает маскировать автоматизацию. Может быть расширен при необходимости.

---

## Неизменяемые компоненты

✅ **Эти файлы НЕ требуют изменений:**
- `func_convert_obj.py` - использует только Playwright `page.expect_download()`
- `func_convert_fbx.py` - аналогично
- `func_convert_blend.py` - аналогично
- `func_screenshoot.py` - только Playwright скриншоты
- `func_site.py` - только навигация
- `baza.py` - работа с Excel
- `config.py` - только пути и селекторы (уже содержит `API_STEEL_LIST`)

---

## Проверочный чеклист (Post-Migration)

- [ ] `pip install -r requirements.txt` завершается без ошибок (hyperbrowser заменен на steel-sdk)
- [ ] `python -c "from steel import AsyncSteel"` не вызывает ImportError
- [ ] Запуск `main.py` печатает "Скрипт FabConvert (Steel.dev) запущен"
- [ ] В логах "Создание Steel.dev сессии..." вместо "Hyperbrowser сессии"
- [ ] Сессия создается успешно (ID выводится, WebSocket URL не выводится - Steel.dev его не дает)
- [ ] Загрузка GLB через `steel_client.sessions.files.upload()` работает (лог "Загрузка в Steel.dev session storage...")
- [ ] Конвертация в OBJ/FBX/BLEND завершается, файлы скачиваются в `DOWNLOAD_DIR`
- [ ] Скриншот сохраняется
- [ ] В конце лог "Сессия Steel.dev X освобождена"
- [ ] Нет ошибок ImportError или AttributeError, связанных с Hyperbrowser
- [ ] Все файлы `*_obj.zip`, `*_fbx.zip`, `*_blend.zip` существуют и имеют размер > 100 байт

---

## Возможные проблемы и решения

| Проблема | Причина | Решение |
|----------|---------|---------|
| `ImportError: No module named 'hyperbrowser'` | requirements.txt не обновлен | `pip install steel-sdk` |
| `AttributeError: 'AsyncSteel' object has no attribute 'sessions.create'` | Неправильный импорт | Проверить `from steel import AsyncSteel` |
| `RuntimeError: Не удалось подключиться к Steel.dev` | Неверный API ключ или лимиты | Проверить `API_STEEL_LIST` в config.py (ключи `ste-...`) |
| Файлы не скачиваются | Ошибка в `page.expect_download()` | Проверить селектор `knopka_download`, увеличить `MAX_TIME` |
| `File too large` при upload | Файл > 100MB (лимит Steel.dev) | Увеличить сжатие Draco (уже в коде), или проверить исходные файлы |
| Browser context not created | Проблема CDP подключения | Проверить CDP URL формат, сетевые настройки |

---

## Команды для выполнения миграции

```bash
# 1. Обновить зависимости
cd BROWSER-STEEL
pip install -r requirements.txt

# 2. Проверить импорт Steel SDK
python -c "from steel import AsyncSteel; print('Steel SDK OK')"

# 3. Запустить миграцию (вручную отредактировать файлы согласно плану)

# 4. Протестировать на одной записи (остановить после первой)
# В main.py можно временно добавить break после process_row или ограничить Excel

# 5. Проверить скачанные файлы в Download/
```

---

## Примечания по Steel.dev специфике

1. **Stealth mode:** Steel.dev НЕ имеет встроенного `use_stealth`. Рекомендуется:
   - Установить `viewport` через `context.set_viewport_size()`
   - Добавить `add_init_script()` для переопределения `navigator.webdriver`, `navigator.plugins`, `navigator.languages`
   - При необходимости настроить `user_agent`, `locale`, `timezone_id`

2. **Downloads:** Используется Playwright нативный `page.expect_download()`. Работает идентично на Steel.dev, так как это часть CDP протокола.

3. **File upload:** Steel.dev `sessions.files.upload()` принимает file-like object (не путь). Автоматически удаляет файлы после сессии.

4. **Session release:** Всегда вызывайте `await client.sessions.release(session.id)` в `finally` блоке. Невызов приводит к утечке ресурсов на сервере Steel.

5. **Retry логика:** Существующая (перебор `API_STEEL_LIST` с `MAX_STEEL_RETRIES`) работает без изменений. При 401/403 ошибках переключать ключ.

6. **Лимиты:** У Steel.dev нет ограничений на количество сессий в минуту (сообщено экспертом). Rate limiter в коде можно оставить для надежности.

7. **API Timeout:** `api_timeout=1800000` (30 мин). Если конвертация занимает больше, увеличьте значение в `launch_browser()`.

---

## Источники

- [Steel.dev Docs](https://docs.steel.dev)
- [Steel Python SDK GitHub](https://github.com/steel-dev/steel-python)
- [Connect with Playwright Guide](https://docs.steel.dev/overview/guides/connect-with-playwright-python)
- [Sessions API Reference](https://docs.steel.dev/api-reference/sessions/create)
- [Files API Reference](https://docs.steel.dev/api-reference/files/upload)

---

## Подпись

**Автор плана:** Claude (анализ и структурирование)  
**Основа:** Экспертиза steel-expert агента + анализ кода BROWSER-STEEL/  
**Дата:** 2026-04-08
