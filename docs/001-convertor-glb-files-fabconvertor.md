# ЗАДАЧА 001: План реализации: Конвертация GLB в OBJ/FBX/BLEND через fabconvert.com

**Задача 001** | **Дата:** 2026-04-07  
**Статус:** План готов к реализации

---

## 1. Общая архитектура

```
HYPERBROWSER/
├── main.py                 # Оркестратор (точка входа)
├── browser.py              # Управление Hyperbrowser (без изменений)
├── baza.py                 # Работа с Excel (без изменений)
├── cookies.py              # Загрузка cookies (без изменений)
├── config.py               # Конфигурация (дополнен UPLOAD_DIR)
├── func_site.py            # Переход на fabconvert.com
├── func_upload.py          # Загрузка GLB файла
├── func_convert_obj.py     # Конвертация в OBJ
├── func_convert_fbx.py     # Конвертация в FBX
├── func_convert_blend.py   # Конвертация в BLEND
└── func_screenshoot.py     # Скриншот (без изменений)
```

**Поток данных:**
1. `main.py` читает строку из Excel → получает `BAZA_ID`
2. Запускает браузер Hyperbrowser
3. Загружает cookies профиля
4. Переходит на `https://fabconvert.com/convert/3d-model`
5. Uploads `UPLOAD_DIR/{BAZA_ID}.glb`
6. Конвертирует в OBJ → скачивает `{BAZA_ID}_obj.zip`
7. Конвертирует в FBX → скачивает `{BAZA_ID}_fbx.zip`
8. Конвертирует в BLEND → скачивает `{BAZA_ID}_blend.zip`
9. Сохраняет файлы в `DOWNLOAD_DIR`
10. Ставит статус "ГОТОВО" в Excel

---

## 2. Файлы для реализации

### 2.1 config.py (ДОПОЛНИТЬ)

**Файл:** `HYPERBROWSER/config.py`  
**Статус:** Уже существует, добавить `UPLOAD_DIR`

**Что добавить:**
```python
# Добавить после DOWNLOAD_DIR (строка ~35)
UPLOAD_DIR = r"D:\MAX\PYTHON\STOCK-PYTHON\3DHunyuan-Convertor\Upload"
```

**Существующие переменные (проверить):**
```python
MAX_TIME = 500          # Таймаут ожидания элементов (сек)
WAIT_TIME = 5           # Краткие паузы между действиями

# Селекторы fabconvert.com
input_upload = "//input[@id='fb']"
knopka_vibor_type = "//div[@class='og']"
knopka_obj = "//span[contains(text(), 'OBJ')][1]"
knopka_fbx = "//span[contains(text(), 'FBX')][1]"
knopka_blend = "//span[contains(text(), 'BLEND')][1]"
knopka_convert = "//a[@class='k x pb jf']"
knopka_download = "//a[@id='yj']"
knopka_close_reklama = "//div[@class='continue-prompt-text']"

# Пути
EXCEL_FILE = r"D:\MAX\PYTHON\STOCK-PYTHON\3DHunyuan-Convertor\Baza-3dhunyuan.xlsx"
DOWNLOAD_DIR = r"D:\MAX\PYTHON\STOCK-PYTHON\3DHunyuan-Convertor\Download"
SCREENSHOTS_FOLDER = r"D:\MAX\PYTHON\STOCK-PYTHON\3DHunyuan-Convertor\Download"

# Hyperbrowser API keys
API_STEEL_LIST = [...]  # уже есть список из 70 ключей
```

---

### 2.2 main.py (НОВЫЙ ФАЙЛ)

**Файл:** `HYPERBROWSER/main.py`  
**Основа:** `primer-download/main.py` (адаптировать под конвертацию)

**Ключевые отличия от примера:**
- Убрать `func_glb_run` (больше не нужно скачивать GLB с сайта)
- Добавить `func_upload_run` (загружать GLB из папки)
- Добавить три конвертации: OBJ, FBX, BLEND
- Использовать `baza_id` вместо `session_id` для имен файлов

**Шаблон кода:**

```python
"""
Главный оркестратор для конвертации GLB в OBJ/FBX/BLEND через fabconvert.com
"""

import asyncio
import os
import sys
from typing import Dict, Any

import config
import baza
from browser import launch_browser, release_browser, wait_for_element
from cookies import load_cookies
from func_site import run as func_site_run
from func_upload import run as func_upload_run
from func_convert_obj import run as func_convert_obj_run
from func_convert_fbx import run as func_convert_fbx_run
from func_convert_blend import run as func_convert_blend_run
from func_screenshoot import run as func_screenshoot_run


def _ts():
    """Возвращает timestamp для логов."""
    from datetime import datetime
    return datetime.now().strftime('%H:%M:%S')


async def process_row(row_data: Dict[str, Any]) -> bool:
    """
    Обрабатывает одну строку из Excel.
    Возвращает True при успехе, False при ошибке.
    """
    profile_num = row_data['BAZA_PROFILE']
    baza_id = row_data['BAZA_ID']

    try:
        profile_num = int(profile_num)
    except (ValueError, TypeError):
        print(f"[{_ts()}] Некорректный номер профиля: {profile_num}")
        return False

    playwright = None
    browser = None
    context = None
    page = None
    hyperbrowser_client = None
    session = None
    sid = None

    try:
        # === 1. Запуск браузера Hyperbrowser.ai ===
        print(f"[{_ts()}] Запуск браузера...")
        playwright, browser, context, page, hyperbrowser_client, session = await launch_browser()
        sid = session.id
        print(f"[{_ts()}] Сессия создана: {sid}")

        # === 2. Загрузка cookies ===
        print(f"[{_ts()}] Загрузка cookies профиля {profile_num}...")
        await load_cookies(context, profile_num)

        # === 3. Конвертация в OBJ ===
        print(f"[{_ts()}] === КОНВЕРТАЦИЯ OBJ ===")
        # 3.1 Переход на сайт (сбрасывает кеш)
        await func_site_run(page, config.site)
        await asyncio.sleep(config.WAIT_TIME)
        # 3.2 Закрытие рекламы
        try:
            await wait_for_element(page, config.knopka_close_reklama, timeout=5)
            await page.click(config.knopka_close_reklama)
            print(f"[{_ts()}] Реклама закрыта")
        except TimeoutError:
            pass
        # 3.3 Upload GLB
        print(f"[{_ts()}] Загрузка GLB: {baza_id}.glb")
        await func_upload_run(page, baza_id)
        await asyncio.sleep(config.WAIT_TIME * 2)
        # 3.4 Конвертация и скачивание
        await func_convert_obj_run(page, baza_id)
        await asyncio.sleep(config.WAIT_TIME)

        # === 4. Конвертация в FBX ===
        print(f"[{_ts()}] === КОНВЕРТАЦИЯ FBX ===")
        # 4.1 Переход на сайт (сброс кеша)
        await func_site_run(page, config.site)
        await asyncio.sleep(config.WAIT_TIME)
        # 4.2 Закрытие рекламы
        try:
            await wait_for_element(page, config.knopka_close_reklama, timeout=5)
            await page.click(config.knopka_close_reklama)
        except TimeoutError:
            pass
        # 4.3 Upload GLB (повторно)
        print(f"[{_ts()}] Загрузка GLB: {baza_id}.glb")
        await func_upload_run(page, baza_id)
        await asyncio.sleep(config.WAIT_TIME * 2)
        # 4.4 Конвертация и скачивание
        await func_convert_fbx_run(page, baza_id)
        await asyncio.sleep(config.WAIT_TIME)

        # === 5. Конвертация в BLEND ===
        print(f"[{_ts()}] === КОНВЕРТАЦИЯ BLEND ===")
        # 5.1 Переход на сайт (сброс кеша)
        await func_site_run(page, config.site)
        await asyncio.sleep(config.WAIT_TIME)
        # 5.2 Закрытие рекламы
        try:
            await wait_for_element(page, config.knopka_close_reklama, timeout=5)
            await page.click(config.knopka_close_reklama)
        except TimeoutError:
            pass
        # 5.3 Upload GLB (повторно)
        print(f"[{_ts()}] Загрузка GLB: {baza_id}.glb")
        await func_upload_run(page, baza_id)
        await asyncio.sleep(config.WAIT_TIME * 2)
        # 5.4 Конвертация и скачивание
        await func_convert_blend_run(page, baza_id)
        await asyncio.sleep(config.WAIT_TIME)

        # === 6. Скриншот страницы (последней сессии) ===
        print(f"[{_ts()}] Скриншот...")
        await func_screenshoot_run(page, sid)
        await asyncio.sleep(config.WAIT_TIME)

        # === 7. Проверка скачанных файлов ===
        print(f"[{_ts()}] Проверка файлов...")
        expected_files = [
            f"{baza_id}_obj.zip",
            f"{baza_id}_fbx.zip",
            f"{baza_id}_blend.zip",
        ]
        for fname in expected_files:
            fpath = os.path.join(config.DOWNLOAD_DIR, fname)
            if not os.path.exists(fpath):
                raise RuntimeError(f"Файл не найден: {fpath}")
            size = os.path.getsize(fpath)
            if size < 100:  # Меньше 100 байт = повреждённый файл
                os.remove(fpath)
                raise RuntimeError(f"Файл слишком мал {fname}: {size} байт")
            print(f"[{_ts()}] ✓ {fname}: {size:,} байт")

        print(f"[{_ts()}] Все файлы успешно скачаны")
        return True

    except Exception as e:
        print(f"[{_ts()}] ✗ Ошибка: {type(e).__name__}: {e}")
        return False

    finally:
        # === 8. Закрытие браузера ===
        print(f"[{_ts()}] Закрытие сессии...")
        await release_browser(playwright, browser, hyperbrowser_client, session.id if session else None)


async def main():
    """
    Основной цикл: бесконечный поиск строк, обработка, обновление статусов.
    """
    print("=" * 60)
    print(f"[{_ts()}] Скрипт FabConvert (Hyperbrowser.ai) запущен")
    print(f"[{_ts()}] Сайт: {config.site}")
    print(f"[{_ts()}] Excel: {config.EXCEL_FILE}")
    print(f"[{_ts()}] Загрузка из: {config.UPLOAD_DIR}")
    print(f"[{_ts()}] Скачивание в: {config.DOWNLOAD_DIR}")
    print("=" * 60)

    while True:
        row_data = baza.get_next_row()
        if row_data is None:
            print(f"[{_ts()}] Нет строк для обработки. Ожидание 60 секунд...")
            await asyncio.sleep(60)
            continue

        print(f"[{_ts()}] Обработка: ID={row_data['BAZA_ID']}, Профиль={row_data['BAZA_PROFILE']}")
        print("-" * 60)

        success = await process_row(row_data)

        if success:
            baza.mark_row_done(row_data['row_number'])
            print(f"[{_ts()}] ✓ СТАТУС: ГОТОВО")
        else:
            baza.mark_row_error(row_data['row_number'])
            print(f"[{_ts()}] ✗ СТАТУС: ОШИБКА")

        print(f"[{_ts()}] Пауза 5 секунд перед следующей строкой...")
        await asyncio.sleep(5)
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{_ts()}] Работа скрипта прервана пользователем.")
        sys.exit(0)
    except Exception as e:
        print(f"[{_ts()}] Критическая ошибка: {type(e).__name__}: {e}")
        sys.exit(1)
```

---

### 2.3 browser.py (БЕЗ ИЗМЕНЕНИЙ)

**Файл:** `HYPERBROWSER/browser.py`  
**Источник:** `primer-download/browser.py` (скопировать как есть)

**Что использовать:**
- `launch_browser()` - запуск Hyperbrowser сессии
- `release_browser()` - корректное закрытие
- `wait_for_element()` - ожидание элементов через CDP (быстрее чем wait_for_selector)
- `get_downloads()` - необязательно, можно использовать expect_download

**Важно:** В `func_site.py` нужно будет импортировать `wait_for_element`:
```python
from browser import wait_for_element
```

---

### 2.4 baza.py (БЕЗ ИЗМЕНЕНИЙ)

**Файл:** `HYPERBROWSER/baza.py`  
**Источник:** `primer-download/baza.py` (скопировать как есть)

**Функции:**
- `get_next_row()` - находит первую строку со статусом '#', возвращает Dict с `row_number`, `BAZA_ID`, `BAZA_PROFILE`, `BAZA_URL` (если есть)
- `mark_row_done(row_number)` - ставит статус 'ГОТОВО'
- `mark_row_error(row_number)` - ставит статус 'ОШИБКА'

**Важно:** В `primer-download/baza.py` уже есть удаление переменных BAZA_PHOTO_1/2/3? Нет, они там не используются. Оставляем как есть.

---

### 2.5 cookies.py (БЕЗ ИЗМЕНЕНИЙ)

**Файл:** `HYPERBROWSER/cookies.py`  
**Источник:** `primer-download/cookies.py` (скопировать)

**Функция:** `load_cookies(context, profile_number)` - загружает JSON cookies из `COOKIES_FOLDER/Cookies-{profile_num}.json`

---

### 2.6 func_site.py (НОВЫЙ ФАЙЛ)

**Файл:** `HYPERBROWSER/func_site.py`  
**Назначение:** Переход на страницу fabconvert.com (сбрасывает кеш)

**Шаблон:**
```python
"""
Переход на страницу конвертации fabconvert.com.
"""

import asyncio
from datetime import datetime
from config import MAX_TIME, WAIT_TIME, site
from browser import wait_for_element


def _ts():
    """Возвращает текущий timestamp для логов."""
    return datetime.now().strftime('%H:%M:%S')


async def run(page, url: str = site):
    """
    Переход на URL и ожидание готовности страницы.
    
    Args:
        page: объект страницы Playwright
        url: URL для перехода (по умолчанию config.site)
    """
    print(f"[{_ts()}] Переход на: {url}")
    
    # Полный переход (сбрасывает кеш и предыдущее состояние)
    await page.goto(url, timeout=MAX_TIME * 1000, wait_until="load")
    
    # Краткая пауза для стабилизации страницы
    await asyncio.sleep(WAIT_TIME)
    
    # Ожидание появления кнопки upload (индикатор готовности)
    print(f"[{_ts()}] Ожидание элемента загрузки: input_upload")
    await wait_for_element(page, "//input[@id='fb']", timeout=MAX_TIME)
    
    print(f"[{_ts()}] Страница готова к загрузке файла")
```

---

### 2.7 func_upload.py (НОВЫЙ ФАЙЛ)

**Файл:** `HYPERBROWSER/func_upload.py`  
**Назначение:** Загрузка GLB файла из `UPLOAD_DIR` на сайт

**Шаблон:**
```python
"""
Загрузка GLB файла на fabconvert.com.
"""

import asyncio
import os
from datetime import datetime
from config import MAX_TIME, WAIT_TIME, UPLOAD_DIR, input_upload
from browser import wait_for_element


def _ts():
    """Возвращает текущий timestamp для логов."""
    return datetime.now().strftime('%H:%M:%S')


async def run(page, baza_id: str):
    """
    Загрузка GLB файла через input[type=file].
    
    Args:
        page: объект страницы Playwright
        baza_id: идентификатор из Excel (для формирования имени файла)
    
    Raises:
        FileNotFoundError: если GLB файл не найден
        RuntimeError: если загрузка не удалась
    """
    # Путь к GLB файлу
    glb_path = os.path.join(UPLOAD_DIR, f"{baza_id}.glb")
    
    # Проверка существования файла
    if not os.path.exists(glb_path):
        raise FileNotFoundError(f"GLB файл не найден: {glb_path}")
    
    print(f"[{_ts()}] Загрузка файла: {glb_path}")
    
    try:
        # Ожидание input[type=file]
        await wait_for_element(page, input_upload, timeout=MAX_TIME)
        
        # Загрузка файла
        await page.set_input_files(input_upload, glb_path)
        print(f"[{_ts()}] Файл выбран, ожидание завершения загрузки...")
        
        # Ожидание завершения загрузки (можно добавить индикатор прогресса)
        # На fabconvert.com после загрузки появляются кнопки форматов
        # Ожидаем появления кнопки OBJ
        await wait_for_element(page, "//span[contains(text(), 'OBJ')][1]", timeout=MAX_TIME * 2)
        
        print(f"[{_ts()}] ✓ GLB успешно загружен")
        
    except Exception as e:
        print(f"[{_ts()}] ✗ Ошибка загрузки GLB: {type(e).__name__}: {e}")
        raise
```

---

### 2.8 func_convert_obj.py (НОВЫЙ ФАЙЛ)

**Файл:** `HYPERBROWSER/func_convert_obj.py`  
**Назначение:** Конвертация в формат OBJ и скачивание ZIP

**Шаблон (адаптировать для FBX/BLEND):**
```python
"""
Конвертация GLB в OBJ и скачивание результата.
"""

import asyncio
import os
from datetime import datetime
from config import MAX_TIME, WAIT_TIME, knopka_obj, knopka_convert, knopka_download
from browser import wait_for_element


def _ts():
    """Возвращает текущий timestamp для логов."""
    return datetime.now().strftime('%H:%M:%S')


async def _download_with_fallback(download, target_path: str) -> int:
    """
    Многоуровневое скачивание с fallback.
    
    Попытки:
    1. page.request.get(download.url)
    2. download.save_as()
    3. urllib.request.urlretrieve()
    
    Returns:
        int: размер файла в байтах
    """
    # Попытка 1: Playwright request API
    try:
        response = await download.page.request.get(download.url)
        if response.ok:
            body = await response.body()
            with open(target_path, "wb") as f:
                f.write(body)
            size = os.path.getsize(target_path)
            if size > 0:
                print(f"[{_ts()}]  ✓ Скачано через page.request: {size:,} байт")
                return size
    except Exception as e:
        print(f"[{_ts()}]  × page.request не сработал: {e}")
    
    # Попытка 2: download.save_as()
    try:
        await download.save_as(target_path)
        size = os.path.getsize(target_path)
        if size > 0:
            print(f"[{_ts()}]  ✓ Скачано через save_as: {size:,} байт")
            return size
    except Exception as e:
        print(f"[{_ts()}]  × save_as не сработал: {e}")
    
    # Попытка 3: urllib fallback
    try:
        import urllib.request
        urllib.request.urlretrieve(download.url, target_path)
        size = os.path.getsize(target_path)
        if size > 0:
            print(f"[{_ts()}]  ✓ Скачано через urllib: {size:,} байт")
            return size
    except Exception as e:
        print(f"[{_ts()}]  × urllib не сработал: {e}")
    
    return 0


async def run(page, baza_id: str):
    """
    Конвертация GLB → OBJ и скачивание ZIP.
    
    Args:
        page: объект страницы Playwright
        baza_id: идентификатор из Excel (для имени файла)
    
    Raises:
        RuntimeError: если конвертация или скачивание не удалось
    """
    print(f"[{_ts()}] Начало конвертации в OBJ")
    
    # 1. Выбор формата OBJ
    print(f"[{_ts()}] 1. Выбор формата OBJ")
    await wait_for_element(page, knopka_obj, timeout=MAX_TIME)
    await page.click(knopka_obj)
    await asyncio.sleep(WAIT_TIME)
    
    # 2. Клик на кнопку Convert
    print(f"[{_ts()}] 2. Запуск конвертации")
    await wait_for_element(page, knopka_convert, timeout=MAX_TIME)
    await page.click(knopka_convert)
    await asyncio.sleep(WAIT_TIME)
    
    # 3. Ожидание кнопки Download (конвертация может занять время)
    print(f"[{_ts()}] 3. Ожидание завершения конвертации...")
    # Увеличиваем таймаут: конвертация 3D модели может быть долгой
    await wait_for_element(page, knopka_download, timeout=MAX_TIME * 3)
    
    # 4. Скачивание ZIP
    print(f"[{_ts()}] 4. Скачивание архива")
    target_path = os.path.join(config.DOWNLOAD_DIR, f"{baza_id}_obj.zip")
    
    try:
        async with page.expect_download(timeout=MAX_TIME * 1000) as download_info:
            await page.click(knopka_download)
        
        download = await download_info.value
        
        # Проверка ошибки
        if download.failure():
            raise RuntimeError(f"Download failed: {download.failure()}")
        
        # Multi-attempt скачивание
        size = await _download_with_fallback(download, target_path)
        
        # Валидация
        if size < 100:
            if os.path.exists(target_path):
                os.remove(target_path)
            raise RuntimeError(f"Файл слишком мал: {size} байт")
        
        print(f"[{_ts()}] ✓ Конвертация в OBJ завершена: {target_path}")
        
    except Exception as e:
        # Очистка частично скачанного файла
        if os.path.exists(target_path):
            os.remove(target_path)
        print(f"[{_ts()}] ✗ Ошибка конвертации OBJ: {type(e).__name__}: {e}")
        raise
```

**Адаптация для FBX:**  
Создать `func_convert_fbx.py` - заменить:
- `knopka_obj` → `knopka_fbx`
- `"{baza_id}_obj.zip"` → `"{baza_id}_fbx.zip"`
- В логах: "OBJ" → "FBX"

**Адаптация для BLEND:**  
Создать `func_convert_blend.py` - заменить:
- `knopka_obj` → `knopka_blend`
- `"{baza_id}_obj.zip"` → `"{baza_id}_blend.zip"`
- В логах: "OBJ" → "BLEND"

---

### 2.9 func_screenshoot.py (БЕЗ ИЗМЕНЕНИЙ)

**Файл:** `HYPERBROWSER/func_screenshoot.py`  
**Источник:** `primer-download/func_screenshoot.py` (скопировать)

---

## 3. Критические моменты и Gotchas

### 3.1 Обработка рекламы/pop-ups
После загрузки страницы fabconvert.com может появляться реклама. В `main.py` после `func_site_run` добавить:

```python
try:
    await wait_for_element(page, config.knopka_close_reklama, timeout=5)
    await page.click(config.knopka_close_reklama)
    print(f"[{_ts()}] Реклама закрыта")
except TimeoutError:
    pass  # Рекламы нет, продолжаем
```

### 3.2 Таймауты
- `MAX_TIME = 500` (5 минут) - ожидание элементов
- Для конвертации: `MAX_TIME * 3 = 1500` (15 минут) - ожидание кнопки Download
- Между действиями: `WAIT_TIME = 5` секунд
- После загрузки GLB: `WAIT_TIME * 2 = 10` секунд

### 3.3 Валидация файлов
Проверять:
- Файл существует (`os.path.exists`)
- Размер > 100 байт (защита от пустых/повреждённых)
- Удалять мелкие файлы и падать с ошибкой

### 3.4 Имена файлов
**Обязательно:**
- OBJ: `{baza_id}_obj.zip`
- FBX: `{baza_id}_fbx.zip`
- BLEND: `{baza_id}_blend.zip`

Не использовать `session_id` (как в примере), только `baza_id`.

### 3.5 Многопоточность (будущее)
Пример уже поддерживает одновременную обработку нескольких строк (разные сессии). Не требуется параллелизация в рамках одной строки - последовательная конвертация трёх форматов.

### 3.6 Очистка при ошибках
В `finally` блоке `main.py` уже есть `release_browser()`. В каждом `func_convert_*.py` при ошибке удалять частично скачанный файл.

---

## 4. Интеграция - порядок действий

### Этап 1: Подготовка
1. Убедиться, что `config.py` содержит `UPLOAD_DIR`
2. Создать папку `Upload` и поместить туда GLB файлы с именами `{BAZA_ID}.glb`
3. Проверить, что в `DOWNLOAD_DIR` достаточно свободного места (3D архивы ~50-200 МБ каждый)

### Этап 2: Копирование unchanged файлов
```bash
# Из primer-download в HYPERBROWSER/ (если там их нет)
browser.py, baza.py, cookies.py, func_screenshoot.py
```

### Этап 3: Создание новых файлов
Создать в `HYPERBROWSER/`:
- `func_site.py` (шаблон выше)
- `func_upload.py` (шаблон выше)
- `func_convert_obj.py` (шаблон выше, копировать для FBX/BLEND)
- `func_convert_fbx.py` (адаптировать)
- `func_convert_blend.py` (адаптировать)

### Этап 4: Создание main.py
Создать `HYPERBROWSER/main.py` по шаблону выше.

**Важно:** Порядок обработки для КАЖДОГО формата (OBJ, FBX, BLEND) должен быть:
```
func_site() → func_upload() → func_convert_FORMAT()
```
Это означает, что GLB файл будет загружаться **трижды** (по разу для каждого формата), так как каждый раз страница сбрасывается. Это требует дополнительного времени, но соответствует требованию "сбрасывать предыдущий кеш".

### Этап 5: Тестирование
1. Запустить `python HYPERBROWSER/main.py`
2. Проверить лог: для каждого формата (OBJ/FBX/BLEND) должен быть свой цикл:
   - переход на сайт
   - загрузка GLB
   - конвертация
   - скачивание
3. Проверить, что в `DOWNLOAD_DIR` появились три ZIP-архива: `{id}_obj.zip`, `{id}_fbx.zip`, `{id}_blend.zip`
4. Проверить Excel: статус "ГОТОВО" для обработанной строки
5. В случае ошибки - статус "ОШИБКА", анализ логов

---

====================



# Промт для Claude:
Коротко основная цель скрипта, в папке HYPERBROWSER/ нужно создать скрипт main.py который будет заходить на сайт, конвертировать GLB модель в OBJ, FBX, BLEND форматы и их скачивать по очереди. 
Это все в цикле, берутся все сторкои из базы Excel. 
Как обрабатывается база, какие там столбцы, все это есть в примере из похожего проекта HYPERBROWSER/primer-download/ бери оттуда готвоый код подключения браузера Hyprebrowser, работы с базой и пирмеры скачиваня файла, чтоб он потом перемещался с обалчного скачивания на мой локальный ПК
Всее переменные и пути к папкам я уже проставил в config.py . Там может что лишнее есть, тогда убери. Теперь эти переменные  нужно тебе вставить в нужных местах в само скрипте. У меня переменные через XPATH селекторы задаются, это все правильные селекторы, првоерено, их не менять
Объясняю по тому, какие файлы внутри этой папки к чему относятся.

Так вот, так же в папке HYPERBROWSER/ создать весь этот скрипт с подключенынм внешним браузером Hyperbrowser. 

Там же есть и файл func_download.py  и func_glb.py это готовый кусок кода пример как скачивать файл с сайта и переносить в нашу папку пото в "D:\MAX\PYTHON\STOCK-PYTHON\3DHunyuan-Convertor\Download\" . Там в примере другой сайт и какието части будут другие, но пример есть.
Когда мы сформируем план, то все файлы уже перепишем под свой новый скрипт ,а какието удалим, они все просто для примера, чтоб легчео создать скрипт.
Файл HYPERBROWSER/main.py - это основной оркестратор, в нем минимально кода должно быть, только запуск других файлов.
Все селекторы в скрипте должны дожидаться элемента, а потом кликать, максимальное время ожидане элемента = MAX_TIME. 
Переменные BAZA_PHOTO_1, 2 , 3 из базы Excel не понадобяться, потому из baza.py их можно убрать.

Собрав всю информацию от агентов, сформируй финальный план для Задачи 001 и её мелкими подзадачами, с подронбым указанием, что где в коде в каком файле изменить, чтоб решить эту задачу.

(Исспользуй MCP sequential-thinking для обдумывания каждого своего шага при составление плана.). 
(Исспользуй MCP Exa для поиска в интернете советов и ответов на вопросы)
(Исспользуй MCP Context7 для поиска актуальной документации и примеров кода)
(Исспользуй агента searcher ля поиска в интернете)
(Исспользуй агента hyperbrowser-expert для анализа нашего кода и чтобы получить советы по Hyperbrowser браузеру)
(Исспользуй агента planner , чтобы он составил финальный план и сохранил его в стандартном формате в docs/*.md)

Перед формированием полного плана и сохранения его в .md файл, задай мне вопросы, что не понятно. Я отвечу и потмо сформируешь план.

----------
# СПИСОК ФАЙЛОВ (названия эти, а код сам заполнишь). (все файлы в папке HYPERBROWSER/ за ее пределами никаких файлов не создавай. Уже имеющиеся файлы переписывай как хочешь)


**main.py** - СХЕМА ПОРЯДКА ВСЕХ ФУНКЦИЙ В ОРКЕСТРАТОРЕ
Здесь порядок, как будут устроены функции, какая за какой идет
1. config.py - берется из файла все переменные и скрипт запоминает их
2. baza.py - какие надо переменные вставляются в базу и из базы берутся значения для всего дальнейшего кода
3. browser.py - запускается браузер
4. func_site.py
5. func_upload.py
6. func_obj.py
7. func_site.py - снова в этом же браузере зайти на ту же страницу или просто обновить страницу
8. func_upload.py
9. func_fbx.py
10. func_site.py
11. func_upload.py
12. func_blend.py
10. Ставит статус ГОТОВ в Excel и закрывает браузер до обработки следующей строки.

**config.py**
Я уже зписал все переменные туда, Проверь если есть ошибки в сиснтаксиске, исправь
Если будешь еще сам создавать какието переменные, тоже записывай и сюда после этих что я записал

**baza.py**
Здесь пусть будет все, что касается нашего взаимодействия с базой Excel, переменные которые мы оттуда берем и значения

**browser.py**
Все что касается запуска браузера Playwright, какой браузер откуда брать и как запускать, в папке примера есть все

**func_site.py**
Войти на site
Ждать появления элемента input_upload_glb_ilove3dm
Ждать WAIT_TIME
Проверить, есть ли на сайте knopka_close_reklama. Если есть, нажать, есть ли нет, пропустить без ошибок

**func_upload.py**
Ждать WAIT_TIME
Upload файл в input_upload из папки Upload/{{BAZA_ID}}.glb
Ждать WAIT_TIME
Клик на knopka_vibor_type
Ждать WAIT_TIME

**func_obj.py**
Ждать появления knopka_obj и клик
Ждать WAIT_TIME
Клик на кнопку knopka_convert
Ждать появления knopka_download и клик на нег. 
Вот здесь запускается скрипт отслеживания скачивания файла и переноса в мою папку DOWNLOAD_DIR с именем {{BAZA_ID}}_obj.zip

**func_fbx.py**
Ждать появления knopka_fbx и клик
Ждать WAIT_TIME
Клик на кнопку knopka_convert
Ждать появления knopka_download и клик на нег. 
Вот здесь запускается скрипт отслеживания скачивания файла и переноса в мою папку DOWNLOAD_DIR с именем {{BAZA_ID}}_fbx.zip

**func_blend.py**
Ждать появления knopka_blend и клик
Ждать WAIT_TIME
Клик на кнопку knopka_convert
Ждать появления knopka_download и клик на нег. 
Вот здесь запускается скрипт отслеживания скачивания файла и переноса в мою папку DOWNLOAD_DIR с именем {{BAZA_ID}}_blend.zip


