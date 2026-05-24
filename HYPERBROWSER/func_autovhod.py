import asyncio
import logging
import os
from pathlib import Path

import config
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger("func_autovhod")


async def save_auth(page, profile: str, auth_path: str, session_path: str) -> None:
    profile_dir = os.path.join(config.PROFILES_FOLDER, str(profile).strip())
    Path(profile_dir).mkdir(parents=True, exist_ok=True)

    session_storage = await page.evaluate("() => JSON.stringify(sessionStorage)")
    with open(session_path, "w", encoding="utf-8") as f:
        f.write(session_storage)

    await page.context.storage_state(path=auth_path, indexed_db=True)


async def run(page, profile: str, auth_path: str, session_path: str) -> bool:
    logger.info(f"Проверка авторизации для профиля: {profile}")
    
    # 1. Сначала идем на страницу где виден аватар
    await page.goto(
        config.site_text_to_image,
        timeout=config.MAX_TIME * 1000,
        wait_until="domcontentloaded",
    )
    await asyncio.sleep(config.WAIT_TIME)

    try:
        # Ждем аватар быстро (WAIT_TIME * 3), этого достаточно
        try:
            await page.locator(config.text_account_mindvideo).wait_for(
                state="visible",
                timeout=(config.WAIT_TIME * 3) * 1000,
            )
        except PlaywrightTimeoutError:
            # Если не нашли сразу, попробуем обновить страницу один раз.
            # Иногда это нужно, чтобы куки "прогрузились" в браузере.
            logger.info("Аватар не найден сразу. Пробуем перезагрузить страницу...")
            await page.reload(timeout=config.MAX_TIME * 1000, wait_until="domcontentloaded")
            await asyncio.sleep(config.WAIT_TIME)
            await page.locator(config.text_account_mindvideo).wait_for(
                state="visible",
                timeout=(config.WAIT_TIME * 3) * 1000,
            )
            
        logger.info("Уже авторизован: найден text_account_mindvideo")
        return False
    except PlaywrightTimeoutError:
        logger.info("Авторизация не найдена даже после перезагрузки, переходим к входу...")

    # 2. Если не авторизован, идем на страницу входа
    logger.info(f"Переход на страницу входа: {config.site_vhod}")
    await page.goto(
        config.site_vhod,
        timeout=config.MAX_TIME * 1000,
        wait_until="domcontentloaded",
    )
    await asyncio.sleep(config.WAIT_TIME)

    logger.info("Ожидание поля ввода Email...")
    await page.wait_for_selector(config.input_mail_vhod, timeout=config.MAX_TIME * 1000)
    await page.fill(config.input_mail_vhod, f"b-{profile}@merepost.com")
    logger.info(f"Email введен: b-{profile}@merepost.com")

    logger.info("Ожидание поля ввода Password...")
    await page.wait_for_selector(config.input_password_vhod, timeout=config.MAX_TIME * 1000)
    await page.fill(config.input_password_vhod, config.mindvideo_password)
    logger.info("Password введен.")

    await asyncio.sleep(config.WAIT_TIME)

    logger.info("Нажатие кнопки Login...")
    await page.wait_for_selector(config.knopka_login_vhod, timeout=config.MAX_TIME * 1000)
    await page.click(config.knopka_login_vhod)
    logger.info("Кнопка Login нажата. Ожидание аватара...")
    await asyncio.sleep(config.WAIT_TIME)

    await page.wait_for_selector(
        config.text_account_mindvideo,
        state="visible",
        timeout=config.MAX_TIME * 1000,
    )

    await page.reload(timeout=config.MAX_TIME * 1000, wait_until="domcontentloaded")
    await asyncio.sleep(config.WAIT_TIME)

    await page.wait_for_selector(
        config.text_account_mindvideo,
        state="visible",
        timeout=config.MAX_TIME * 1000,
    )

    await save_auth(page, profile, auth_path, session_path)
    logger.info("Авторизация выполнена и сохранена")

    return True
