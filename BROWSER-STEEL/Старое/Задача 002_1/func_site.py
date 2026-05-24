"""
Переход на страницу конвертации fabconvert.com.
"""

import asyncio
from datetime import datetime
from config import MAX_TIME, WAIT_TIME, input_upload
from browser import wait_for_element


def _ts():
    """Возвращает текущий timestamp для логов."""
    return datetime.now().strftime('%H:%M:%S')


async def run(page, url: str):
    """
    Переход на URL и ожидание готовности страницы.

    Args:
        page: объект страницы Playwright
        url: URL для перехода (config.site)
    """
    print(f"[{_ts()}] Переход на: {url}")

    # Полный переход (сбрасывает кеш и предыдущее состояние)
    await page.goto(url, timeout=MAX_TIME * 1000, wait_until="load")

    # Краткая пауза для стабилизации страницы
    await asyncio.sleep(WAIT_TIME)

    # Ожидание появления кнопки upload (индикатор готовности)
    print(f"[{_ts()}] Ожидание элемента загрузки: input_upload")
    await wait_for_element(page, input_upload, timeout=MAX_TIME)

    print(f"[{_ts()}] Страница готова к загрузке файла")
