import asyncio
import json
import os
import sys
import uuid
from playwright.async_api import async_playwright
import random
import config
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import CreateSessionParams


async def test_profile_login(profile_name: str) -> bool:
    auth_path = os.path.join(config.PROFILES_FOLDER, profile_name, config.AUTH_FILENAME)

    if not os.path.exists(auth_path):
        print(f"ОШИБКА: Файл аутентификации не найден: {auth_path}")
        return False

    print(f"ИСПОЛЬЗУЕМ ПРОФИЛЬ: {profile_name}")

    with open(auth_path, "r") as f:
        auth_data = json.load(f)

    api_keys = list(config.API_HYPERBROWSER_LIST)
    random.shuffle(api_keys)

    last_exc = None

    for attempt in range(max(1, config.MAX_HYPERBROWSER_RETRIES)):
        api_key = api_keys[attempt % len(api_keys)]
        print(f"Попытка {attempt + 1}/{config.MAX_HYPERBROWSER_RETRIES} с ключом API: {api_key[:10]}...")

        client = Hyperbrowser(api_key=api_key)
        try:
            session = client.sessions.create(
                CreateSessionParams(
                    accept_cookies=True,
                    screen={"width": 1920, "height": 1080},
                    save_downloads=True,
                )
            )

            playwright = await async_playwright().start()
            browser = await playwright.chromium.connect_over_cdp(session.ws_endpoint)

            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await context.new_page()

            try:
                # Восстанавливаем полный storage_state из сохранённого файла
                await context.add_cookies(auth_data.get("cookies", []))

                # Восстанавливаем localStorage и sessionStorage
                origins = auth_data.get("origins", [])
                for origin_data in origins:
                    origin = origin_data.get("origin", "")
                    local_storage = origin_data.get("localStorage", [])
                    session_storage = origin_data.get("sessionStorage", [])

                    if local_storage or session_storage:
                        await page.goto(origin, wait_until="domcontentloaded", timeout=config.MAX_TIME * 1000)

                        # Восстанавливаем localStorage
                        for item in local_storage:
                            await page.evaluate(f"""
                                localStorage.setItem('{item['name']}', {json.dumps(item['value'])});
                            """)

                        # Восстанавливаем sessionStorage
                        for item in session_storage:
                            await page.evaluate(f"""
                                sessionStorage.setItem('{item['name']}', {json.dumps(item['value'])});
                            """)

                # Переходим на сайт
                await page.goto(config.site_text_to_image, wait_until="networkidle", timeout=config.MAX_TIME * 1000)

                avatar_selector = config.text_account_mindvideo
                await page.wait_for_selector(avatar_selector, timeout=config.MAX_TIME * 1000)

                print("УСПЕХ: Элемент аватара найден!")

                await browser.close()
                await playwright.stop()
                client.sessions.stop(session.id)
                return True

            except Exception as e:
                print(f"ОШИБКА при работе со страницей: {e}")
                await browser.close()
                await playwright.stop()
                client.sessions.stop(session.id)
                last_exc = e

        except Exception as e:
            print(f"ОШИБКА: {e}")
            last_exc = e

        if attempt < config.MAX_HYPERBROWSER_RETRIES - 1:
            await asyncio.sleep(config.HYPERBROWSER_RETRY_DELAY)

    print(f"Не удалось выполнить вход после {config.MAX_HYPERBROWSER_RETRIES} попыток.")
    if last_exc:
        print(f"Последняя ошибка: {last_exc}")
    return False


async def main():
    if len(sys.argv) < 2:
        print("Использование: python test_mindvideo_account.py <имя_профиля>")
        print("Пример: python test_mindvideo_account.py 01")
        sys.exit(1)
        
    profile_name = sys.argv[1].strip()
    success = await test_profile_login(profile_name)
    
    if success:
        print("\n✅ ТЕСТ ПРОЙДЕН")
        sys.exit(0)
    else:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕН")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())