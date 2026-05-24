"""
Конвертация GLB в FBX и скачивание результата.
"""

import asyncio
import os
import urllib.request
from datetime import datetime
from config import MAX_TIME, WAIT_TIME, DOWNLOAD_DIR, knopka_fbx, knopka_convert, knopka_download
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
    Конвертация GLB → FBX и скачивание ZIP.

    Args:
        page: объект страницы Playwright
        baza_id: идентификатор из Excel (для имени файла)

    Raises:
        RuntimeError: если конвертация или скачивание не удалось
    """
    print(f"[{_ts()}] Начало конвертации в FBX")

    # 1. Выбор формата FBX
    print(f"[{_ts()}] 1. Выбор формата FBX")
    await wait_for_element(page, knopka_fbx, timeout=MAX_TIME)
    await page.click(knopka_fbx)
    await asyncio.sleep(WAIT_TIME)

    # 2. Клик на кнопку Convert
    print(f"[{_ts()}] 2. Запуск конвертации")
    await wait_for_element(page, knopka_convert, timeout=MAX_TIME)
    await page.click(knopka_convert)
    await asyncio.sleep(WAIT_TIME)

    # 3. Ожидание кнопки Download (конвертация может занять время)
    print(f"[{_ts()}] 3. Ожидание завершения конвертации...")
    await wait_for_element(page, knopka_download, timeout=MAX_TIME)

    # 4. Скачивание ZIP
    print(f"[{_ts()}] 4. Скачивание архива")
    target_path = os.path.join(DOWNLOAD_DIR, f"{baza_id}_fbx.zip")

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

        print(f"[{_ts()}] ✓ Конвертация в FBX завершена: {target_path}")

    except Exception as e:
        # Очистка частично скачанного файла
        if os.path.exists(target_path):
            os.remove(target_path)
        print(f"[{_ts()}] ✗ Ошибка конвертации FBX: {type(e).__name__}: {e}")
        raise
