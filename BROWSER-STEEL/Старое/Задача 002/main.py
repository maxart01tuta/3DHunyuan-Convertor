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
    steel_client = None
    session = None
    sid = None

    try:
        # === 1. Запуск браузера Steel.dev ===
        print(f"[{_ts()}] Запуск браузера...")
        playwright, browser, context, page, steel_client, session = await launch_browser()
        sid = session.id
        print(f"[{_ts()}] Сессия Steel.dev создана: {sid}")

        # === 2. Загрузка cookies ===
        # (не требуется для fabconvert.com)

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
        await func_upload_run(page, steel_client, session.id, baza_id)
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
        await func_upload_run(page, steel_client, session.id, baza_id)
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
        await func_upload_run(page, steel_client, session.id, baza_id)
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
        await release_browser(playwright, browser, steel_client, session.id if session else None)


async def main():
    """
    Основной цикл: бесконечный поиск строк, обработка, обновление статусов.
    """
    print("=" * 60)
    print(f"[{_ts()}] Скрипт FabConvert (Steel.dev) запущен")
    print(f"[{_ts()}] Сайт: {config.site}")
    print(f"[{_ts()}] Excel: {config.EXCEL_FILE}")
    print(f"[{_ts()}] Загрузка из: {config.UPLOAD_DIR}")
    print(f"[{_ts()}] Скачивание в: {config.DOWNLOAD_DIR}")
    print("=" * 60)

    # Создаем папки если их нет
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(config.SCREENSHOTS_FOLDER, exist_ok=True)

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
