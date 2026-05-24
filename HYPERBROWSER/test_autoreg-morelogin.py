import asyncio
import logging
import sys
import os
import uuid
from typing import Dict, Any

# Добавляем путь для импорта config
this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, this_dir)
import config
from playwright.async_api import async_playwright

# Импортируем утилиты из основного скрипта
# Примечание: предполагается, что MoreLoginClient и функции определены в 0-mindvideo-autoreg-morelogin.py
from importlib import import_module
main_script = import_module("0-mindvideo-autoreg-morelogin")
MoreLoginClient = main_script.MoreLoginClient
parse_proxy_url_to_morelogin_proxy = main_script.parse_proxy_url_to_morelogin_proxy
choose_random_morelogin_token = main_script.choose_random_morelogin_token
choose_random_proxy_url = main_script.choose_random_proxy_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-morelogin-api")

async def test_morelogin_api_flow():
    logger.info("--- ЗАПУСК ТЕСТА MORELOGIN API (FIXED PROFILE STRATEGY) ---")
    
    token = choose_random_morelogin_token()
    proxy_url = choose_random_proxy_url()
    proxy_data = parse_proxy_url_to_morelogin_proxy(proxy_url)
    
    logger.info(f"Используемый токен: {token[:10]}...")
    logger.info(f"Выбран прокси: {proxy_url}")
    
    client = MoreLoginClient(token)
    env_id = config.MORELOGIN_PROFILE_ID
    
    try:
        logger.info(f"Шаг 1: Используем фиксированный профиль env_id: {env_id}")

        # 2. Тест установки прокси
        logger.info(f"Шаг 2: Обновление прокси для {env_id}...")
        success = await client.set_proxy(env_id, proxy_data)
        logger.info(f"Результат: {'Успешно' if success else 'Ошибка'}")
        
        # 3. Тест обновления фингерпринта
        logger.info(f"Шаг 3: Обновление фингерпринта для {env_id}...")
        success = await client.refresh_fingerprint(env_id)
        logger.info(f"Результат: {'Успешно' if success else 'Ошибка'}")
        
        # 4. Тест запуска профиля
        logger.info(f"Шаг 4: Запуск профиля {env_id}...")
        debug_port = await client.start_env(env_id)
        logger.info(f"Успех! debugPort: {debug_port}")
        
        # 5. Тест подключения CDP
        logger.info(f"Шаг 5: Тест подключения Playwright по CDP (порт {debug_port})...")
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{debug_port}")
                logger.info("Успех! Соединение с браузером установлено.")
                
                context = browser.contexts[0]
                page = await context.new_page()
                
                # Проверка кэша и куки перед тестом
                logger.info("Проверка на наличие старых данных (Cookies/localStorage)...")
                await page.goto("https://tempmail.plus/ru/#!", timeout=20000)
                
                # Проверяем localStorage маркер
                cache_test = await page.evaluate("localStorage.getItem('test_cache_marker')")
                # Проверяем наличие куки (например, 'mail' на tempmail.plus часто сохраняет почту)
                cookies = await context.cookies()
                mail_cookie = next((c for c in cookies if c['name'] == 'mail'), None)

                if cache_test or mail_cookie:
                    logger.warning(f"ОБНАРУЖЕНЫ СТАРЫЕ ДАННЫЕ! Marker: {cache_test}, Mail Cookie: {mail_cookie['value'] if mail_cookie else 'No'}")
                else:
                    logger.info("Кэш и Cookies чисты.")

                # Установка данных для проверки в следующем запуске
                logger.info("Установка тестовых данных (Cookies/localStorage) для проверки очистки...")
                await page.evaluate("localStorage.setItem('test_cache_marker', 'STILL_HERE')")
                # Устанавливаем тестовую куку
                await context.add_cookies([{"name": "mail", "value": "test-to-be-deleted@tempmail.plus", "domain": "tempmail.plus", "path": "/"}])
                
                logger.info("Проверка внешнего IP через прокси...")
                await page.goto("https://api.ipify.org?format=json", timeout=20000)
                ip_info = await page.inner_text("body")
                logger.info(f"Внешний IP браузера: {ip_info}")
                
                await page.goto("https://tempmail.plus/ru/#!", timeout=15000)
                title = await page.title()
                logger.info(f"Тестовая страница загружена. Заголовок: {title}")
                
                await browser.close()
            except Exception as e:
                logger.error(f"Ошибка подключения по CDP: {e}")
                raise
        
        # 6. Тест закрытия профиля
        logger.info(f"Шаг 6: Закрытие профиля {env_id}...")
        success = await client.close_env(env_id)
        logger.info(f"Результат: {'Успешно' if success else 'Ошибка'}")
        
        # 7. Тест очистки кэша
        logger.info(f"Шаг 7: Очистка локального кэша для {env_id}...")
        success = await client.remove_local_cache(env_id)
        logger.info(f"Результат: {'Успешно' if success else 'Ошибка'}")
        
        logger.info("--- ТЕСТ ЗАВЕРШЕН УСПЕШНО (ПРОФИЛЬ СОХРАНЕН) ---")
        
    except Exception as e:
        logger.error(f"--- ТЕСТ ПРОВАЛЕН ---")
        logger.error(f"Ошибка: {e}")
        if env_id:
            logger.info(f"Попытка экстренного закрытия для {env_id}...")
            try:
                await client.close_env(env_id)
            except:
                pass
    finally:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_morelogin_api_flow())
