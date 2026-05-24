"""
Функция: скриншот страницы 3D модели.
"""

import os
from datetime import datetime
from config import SCREENSHOTS_FOLDER


async def run(page, session_id: str):
    """
    Делает скриншот текущей страницы и сохраняет в SCREENSHOTS_FOLDER.
    """
    ts = datetime.now().strftime('%H:%M:%S')

    os.makedirs(SCREENSHOTS_FOLDER, exist_ok=True)

    target_path = os.path.join(SCREENSHOTS_FOLDER, f"{session_id}_screenshoot.jpg")
    await page.screenshot(path=target_path)

    print(f"[{ts}] Скриншот сохранён: {target_path}")
    return target_path
