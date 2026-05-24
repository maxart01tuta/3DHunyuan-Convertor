import asyncio
import random
import logging
import uuid
import os
import json
from playwright.async_api import async_playwright
from hyperbrowser import AsyncHyperbrowser
from hyperbrowser.models import CreateSessionParams, ScreenConfig
import config

# Настройка логирования
logger = logging.getLogger("browser")

def get_hyperbrowser_api_key() -> str:
    """
    Выбирает случайный API ключ из списка в config.py.
    """
    keys = []
    if hasattr(config, "API_HYPERBROWSER_LIST") and config.API_HYPERBROWSER_LIST:
        keys = [k for k in config.API_HYPERBROWSER_LIST if str(k).strip()]
    elif hasattr(config, "API_HYPERBROWSER_LIST_TEST") and config.API_HYPERBROWSER_LIST_TEST:
        keys = [k for k in config.API_HYPERBROWSER_LIST_TEST if str(k).strip()]

    if not keys:
        raise RuntimeError("Не найдено ни одного API ключа Hyperbrowser в config.py")

    return random.choice(keys)

async def launch_hyperbrowser_with_retries(profile_id: str = None):
    """
    Создает сессию Hyperbrowser с ретраями и подключается через Playwright CDP.
    Если передан profile_id, используется профиль для сохранения состояния.
    Возвращает: playwright, browser, client, session
    """
    last_error = None

    for attempt in range(1, config.MAX_HYPERBROWSER_RETRIES + 1):
        playwright = None
        browser = None
        client = None
        session = None

        try:
            api_key = get_hyperbrowser_api_key()
            client = AsyncHyperbrowser(api_key=api_key)

            # Формируем параметры сессии
            params = {
                "accept_cookies": True,
                "use_stealth": True,
                "screen": ScreenConfig(width=1920, height=1080),
                "timeout_minutes": 30,
            }

            # Если включены профили и передан ID
            if config.USE_HYPERBROWSER_PROFILES and profile_id:
                target_profile_name = f"MindVideo-{profile_id}"
                
                try:
                    # Просто создаем новый профиль каждый раз. 
                    # Это гарантирует работу даже при смене API ключей Hyperbrowser.
                    # Авторизация все равно восстановится из локальных JSON в Profiles/.
                    from hyperbrowser.models import CreateProfileParams
                    new_profile = await client.profiles.create(CreateProfileParams(name=target_profile_name))
                    
                    params["profile"] = {
                        "id": new_profile.id,
                        "persist_changes": True
                    }
                    logger.info(f"Создан новый профиль Hyperbrowser: {target_profile_name} (ID: {new_profile.id})")
                
                except Exception as profile_err:
                    logger.error(f"Ошибка при создании профиля Hyperbrowser: {profile_err}")
                    pass

            # Создаем сессию Hyperbrowser
            session = await client.sessions.create(
                params=CreateSessionParams(**params)
            )

            logger.info(f"Hyperbrowser session создана: {session.id} (Попытка {attempt})")

            playwright = await async_playwright().start()
            browser = await playwright.chromium.connect_over_cdp(session.ws_endpoint)

            logger.info("Подключение к Hyperbrowser через Playwright успешно.")
            return playwright, browser, client, session

        except Exception as e:
            last_error = e
            logger.warning(
                f"Попытка {attempt}/{config.MAX_HYPERBROWSER_RETRIES} подключения не удалась: {e}"
            )

            # Очистка ресурсов при ошибке
            if browser:
                try: await browser.close()
                except: pass
            if session and client:
                try: await client.sessions.stop(session.id)
                except: pass
            if client:
                try: await client.close()
                except: pass
            if playwright:
                try: await playwright.stop()
                except: pass

            if attempt < config.MAX_HYPERBROWSER_RETRIES:
                await asyncio.sleep(config.HYPERBROWSER_RETRY_DELAY)

    raise RuntimeError(f"Не удалось подключиться к Hyperbrowser после всех попыток: {last_error}")

async def setup_context(browser_obj, profile: str):
    """
    Создает новый контекст браузера и восстанавливает storage_state и sessionStorage из локальных файлов.
    Это гарантирует одинаковое поведение во всех скриптах.
    """
    auth_path = config.get_auth_path(profile)
    session_path = config.get_session_storage_path(profile)
    
    context = None
    
    # 1. Пытаемся создать контекст с подгруженным storage_state
    try:
        if os.path.exists(auth_path):
            context = await browser_obj.new_context(storage_state=auth_path)
            logger.info(f"Контекст создан с использованием storage_state: {auth_path}")
        else:
            logger.warning(f"Файл storage_state не найден: {auth_path}. Создаю чистый контекст.")
            context = await browser_obj.new_context()
    except Exception as e:
        logger.error(f"Ошибка при загрузке storage_state: {e}")
        context = await browser_obj.new_context()

    # 2. Восстановление sessionStorage
    if os.path.exists(session_path):
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                session_data = f.read()
            
            # Скрипт вставит данные в sessionStorage при загрузке любой страницы
            await context.add_init_script(f"""
                const data = {session_data};
                for (const [key, value] of Object.entries(data)) {{
                    sessionStorage.setItem(key, value);
                }}
            """)
            logger.info(f"sessionStorage восстановлен из файла: {session_path}")
        except Exception as e:
            logger.error(f"Ошибка при восстановлении sessionStorage: {e}")
            
    return context

async def release_hyperbrowser(playwright=None, browser=None, client=None, session=None, context=None):
    """
    Максимально безопасное завершение всех ресурсов. 
    Проверяет каждый объект на None и оборачивает каждое закрытие в try/except.
    """
    logger.info("Начало освобождения ресурсов...")
    
    # 1. Закрываем контекст (страницы и куки)
    if context is not None:
        try:
            await context.close()
            logger.info("Context закрыт.")
        except Exception as e:
            logger.debug(f"Ошибка при закрытии context: {e}")

    # 2. Закрываем браузер (соединение CDP)
    if browser is not None:
        try:
            await browser.close()
            logger.info("Browser закрыт.")
        except Exception as e:
            logger.debug(f"Ошибка при закрытии browser: {e}")

    # 3. Останавливаем сессию в облаке Hyperbrowser
    if session is not None and client is not None:
        try:
            await client.sessions.stop(session.id)
            logger.info(f"Hyperbrowser session {session.id} остановлена.")
        except Exception as e:
            logger.debug(f"Ошибка при остановке сессии Hyperbrowser: {e}")

    # 4. Закрываем клиент API
    if client is not None:
        try:
            await client.close()
            logger.info("Hyperbrowser client закрыт.")
        except Exception as e:
            logger.debug(f"Ошибка при закрытии client: {e}")

    # 5. Останавливаем Playwright
    if playwright is not None:
        try:
            await playwright.stop()
            logger.info("Playwright остановлен.")
        except Exception as e:
            logger.debug(f"Ошибка при остановке playwright: {e}")
    
    logger.info("Освобождение ресурсов завершено.")
