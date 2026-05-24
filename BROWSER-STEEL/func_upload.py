"""
Загрузка GLB файла на fabconvert.com.
"""

import asyncio
import os
from datetime import datetime
from config import MAX_TIME, WAIT_TIME, UPLOAD_DIR, input_upload, input_upload_css, knopka_vibor_type, knopka_obj
from browser import wait_for_element


def _ts():
    """Возвращает текущий timestamp для логов."""
    return datetime.now().strftime('%H:%M:%S')


async def run(page, steel_client, session_id: str, baza_id: str):
    """
    Загрузка GLB файла через CDP DOM.setFileInputFiles с использованием Steel.dev upload API.
    Поддерживает файлы >50MB.

    Args:
        page: объект страницы Playwright
        steel_client: Steel.dev клиент (для upload_file API)
        session_id: ID сессии Steel.dev
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

    file_size_mb = os.path.getsize(glb_path) / (1024 * 1024)
    print(f"[{_ts()}] 📦 Файл {file_size_mb:.1f}MB: {glb_path}")

    cdp_session = None

    try:
        # Ожидание input[type=file]
        await wait_for_element(page, input_upload, timeout=MAX_TIME)

        # Upload файла в сессию через Steel.dev API
        print(f"[{_ts()}] → Загрузка в Steel.dev session storage...")
        with open(glb_path, 'rb') as f:
            session_file = await steel_client.sessions.files.upload(
                session_id=session_id,
                file=f
            )
        remote_path = session_file.path
        
        # Валидация remote_path
        if not remote_path or not remote_path.startswith('/files/'):
            raise RuntimeError(f"Неверный remote_path: {remote_path}")
        
        print(f"[{_ts()}] ✓ Файл загружен: {remote_path}")

        # Проверка что input элемент visible и enabled
        input_visible = await page.evaluate("""
            (sel) => {
                const el = document.querySelector(sel);
                return el && el.offsetParent !== null && !el.disabled;
            }
        """, input_upload_css)
        if not input_visible:
            raise RuntimeError("Input элемент не виден или disabled")

        # CDP подход для больших файлов (>50MB)
        print(f"[{_ts()}] Применение CDP DOM.setFileInputFiles...")
        context = page.context
        cdp_session = await context.new_cdp_session(page)

        # Получить DOM документ
        dom_document = await cdp_session.send("DOM.getDocument")
        root_node_id = dom_document["root"]["nodeId"]

        # Найти input элемент по CSS селектору из конфига
        input_node = await cdp_session.send("DOM.querySelector", {
            "nodeId": root_node_id,
            "selector": input_upload_css
        })

        if not input_node.get("nodeId"):
            raise RuntimeError("Input элемент не найден через CDP")

        print(f"[{_ts()}] ✓ Input element найден, nodeId: {input_node['nodeId']}")

        # Установить файл через CDP
        await cdp_session.send("DOM.setFileInputFiles", {
            "files": [remote_path],
            "nodeId": input_node["nodeId"]
        })

        print(f"[{_ts()}] ✓ Input установлен, ожидение конвертации...")

        # Пауза после загрузки файла
        await asyncio.sleep(WAIT_TIME)

        # Клик на выпадающий список выбора типа файла
        print(f"[{_ts()}] Клик на knopka_vibor_type (открытие списка форматов)...")
        await wait_for_element(page, knopka_vibor_type, timeout=MAX_TIME)
        await page.click(knopka_vibor_type)

        # Пауза после открытия списка
        await asyncio.sleep(WAIT_TIME)

        print(f"[{_ts()}] ✅ GLB успешно загружен, список форматов открыт")

    except Exception as e:
        # Специфичная обработка ошибок CDP
        error_msg = str(e)
        if "Not allowed" in error_msg:
            raise RuntimeError("Chrome заблокировал DOM.setFileInputFiles для этого сайта")
        elif "No node with given id found" in error_msg:
            raise RuntimeError("Input элемент исчез из DOM после upload")
        else:
            file_size = os.path.getsize(glb_path) / (1024 * 1024)
            raise RuntimeError(
                f"Файл {file_size:.1f}MB не загружен в Steel.dev session. "
                f"Проверьте размер файла (лимит 100MB) или доступность сессии."
            ) from e
    finally:
        # Очистка CDP сессии
        if cdp_session:
            try:
                await cdp_session.detach()
            except Exception:
                pass
