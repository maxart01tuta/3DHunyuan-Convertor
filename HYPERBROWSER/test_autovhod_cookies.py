import asyncio
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright

# Импорт config.py из текущей директории
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
import config


# =========================
# ЛОГИРОВАНИЕ
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test-autovhod-cookies")


def get_hyperbrowser_api_key() -> str:
    keys = []
    if hasattr(config, "API_HYPERBROWSER_LIST") and config.API_HYPERBROWSER_LIST:
        keys = [k for k in config.API_HYPERBROWSER_LIST if str(k).strip()]
    
    if not keys:
        raise RuntimeError("Не найдено ни одного API ключа Hyperbrowser в config.py")

    return random.choice(keys)


async def launch_hyperbrowser_with_retries():
    from hyperbrowser import AsyncHyperbrowser
    from hyperbrowser.models import CreateSessionParams, ScreenConfig

    last_error = None

    for attempt in range(1, config.MAX_HYPERBROWSER_RETRIES + 1):
        playwright = None
        browser = None
        client = None
        session = None

        try:
            api_key = get_hyperbrowser_api_key()
            client = AsyncHyperbrowser(api_key=api_key)

            session = await client.sessions.create(
                params=CreateSessionParams(
                    accept_cookies=True,
                    use_stealth=True,
                    screen=ScreenConfig(width=1920, height=1080),
                    timeout_minutes=10,
                )
            )

            logger.info(f"Hyperbrowser session создана: {session.id}")

            playwright = await async_playwright().start()
            browser = await playwright.chromium.connect_over_cdp(session.ws_endpoint)

            logger.info("Подключение к Hyperbrowser через Playwright успешно.")
            return playwright, browser, client, session

        except Exception as e:
            last_error = e
            logger.warning(
                f"Попытка {attempt}/{config.MAX_HYPERBROWSER_RETRIES} подключения не удалась: {e}"
            )
            if browser: await browser.close()
            if session and client: await client.sessions.stop(session.id)
            if client: await client.close()
            if playwright: await playwright.stop()
            if attempt < config.MAX_HYPERBROWSER_RETRIES:
                await asyncio.sleep(config.HYPERBROWSER_RETRY_DELAY)

    raise RuntimeError(f"Не удалось подключиться к Hyperbrowser после ретраев: {last_error}")


async def release_resources(playwright=None, browser=None, client=None, session=None, context=None):
    try:
        if context: await context.close()
        if browser: await browser.close()
        if session and client: await client.sessions.stop(session.id)
        if client: await client.close()
        if playwright: await playwright.stop()
    except Exception:
        logger.exception("Ошибка при освобождении ресурсов.")


async def test_autovhod(profile_name: str):
    logger.info(f"Запуск теста для профиля: {profile_name}")
    
    # Путь к куки: COOKIES_FOLDER \ BAZA_PROFILE \ Cookies-{{BAZA_PROFILE}}.json
    cookie_path = os.path.join(config.COOKIES_FOLDER, profile_name, f"Cookies-{profile_name}.json")
    
    if not os.path.exists(cookie_path):
        logger.error(f"Файл куки не найден: {cookie_path}")
        return

    playwright = None
    browser = None
    client = None
    session = None
    context = None

    try:
        # 1. Загружаем куки из JSON V3
        if not os.path.exists(cookie_path):
            logger.error(f"Файл куки не найден: {cookie_path}")
            return

        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookies_v3 = json.load(f)
        
        playwright_cookies = []
        for c in cookies_v3:
            pc = {
                "name": c.get("name"),
                "value": c.get("value"),
                "domain": c.get("domain"),
                "path": c.get("path"),
                "secure": c.get("secure"),
                "httpOnly": c.get("httpOnly"),
                "sameSite": c.get("sameSite") if c.get("sameSite") in ["Strict", "Lax", "None"] else "Lax"
            }
            # В Playwright для сессионных кук (expirationDate: -1) поле expires должно отсутствовать
            exp = c.get("expirationDate")
            if exp is not None and exp != -1:
                pc["expires"] = float(exp)
            playwright_cookies.append(pc)

        # 2. Запуск браузера
        playwright, browser, client, session = await launch_hyperbrowser_with_retries()
        
        # 3. Создаем контекст и добавляем куки
        context = await browser.new_context()
        await context.add_cookies(playwright_cookies)
        
        # Находим токен для инъекции в localStorage
        auth_token = None
        for c in playwright_cookies:
            if c['name'] == 'token':
                auth_token = c['value']
                break
        
        if auth_token:
            logger.info("Токен найден в куках, подготавливаем инъекцию в localStorage...")
            # Инъекция токена в localStorage ПЕРЕД загрузкой страницы
            # Сайт ожидает JSON-строку в ключе 'user'
            ls_value = json.dumps({"token": auth_token})
            init_script = f"""
                try {{
                    window.localStorage.setItem('user', {json.dumps(ls_value)});
                    window.localStorage.setItem('i18nextLng', 'en');
                }} catch (e) {{
                    console.error('LocalStorage injection failed', e);
                }}
            """
            await context.add_init_script(init_script)
        else:
            logger.warning("Кука 'token' не найдена в файле! Авторизация вряд ли сработает.")

        page = await context.new_page()
        logger.info(f"Переход на сайт: {config.site_text_to_image}")
        
        # 4. Переход
        await page.goto(config.site_text_to_image, wait_until="networkidle", timeout=config.MAX_TIME * 1000)
        
        try:
            await page.wait_for_selector(config.text_account_mindvideo, state="visible", timeout=30000)
            logger.info("АВТОРИЗАЦИЯ УСПЕШНА: Селектор аккаунта найден!")
        except Exception:
            logger.error("ОШИБКА АВТОРИЗАЦИИ: Селектор аккаунта не найден за 30 секунд.")
            
            # Диагностика
            diag_dir = os.path.join(THIS_DIR, "diagnostics", profile_name)
            Path(diag_dir).mkdir(parents=True, exist_ok=True)
            
            screenshot_path = os.path.join(diag_dir, "error_auth.png")
            html_path = os.path.join(diag_dir, "error_page.html")
            
            await page.screenshot(path=screenshot_path)
            content = await page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Диагностические данные сохранены: {diag_dir}")
            
    except Exception as e:
        logger.exception(f"Критическая ошибка в тесте: {e}")
    finally:
        await release_resources(playwright, browser, client, session, context)
        logger.info("Тест завершен, ресурсы освобождены.")


async def main():
    # Можно передать профиль аргументом или взять первый из Excel для теста
    if len(sys.argv) > 1:
        profile = sys.argv[1]
    else:
        # Для примера возьмем '01' или попробуем найти в Excel
        profile = "01"
        logger.info(f"Профиль не указан в аргументах, используем по умолчанию: {profile}")
    
    await test_autovhod(profile)


if __name__ == "__main__":
    asyncio.run(main())
