"""
Модуль управления браузером через Playwright с Hyperbrowser.ai.
Запускает облачный браузер и создает контекст и страницу.
"""

import os
import asyncio
import time
import random
import zipfile
from typing import Tuple, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from steel import AsyncSteel, SteelError
import config
from datetime import datetime


async def wait_for_element(page, selector: str, timeout: int = 180) -> bool:
    """
    Ждёт появления элемента через page.evaluate вместо wait_for_selector.
    Значительно быстрее через CDP — один RPC-запрос вместо тяжёлого polling.
    Поддерживает XPath (начинается с //) и CSS селекторы.
    """
    start = time.time()
    is_xpath = selector.startswith("//")
    if is_xpath:
        js = """(sel) => {
            const r = document.evaluate(sel, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            return r.singleNodeValue !== null;
        }"""
    else:
        js = "(sel) => document.querySelector(sel) !== null"

    while (time.time() - start) < timeout:
        if await page.evaluate(js, selector):
            return True
        await asyncio.sleep(1)
    raise TimeoutError(f"Элемент не найден за {timeout}с: {selector}")

async def launch_browser() -> Tuple[object, Browser, BrowserContext, Page, AsyncSteel, object]:
    """
    Запускает облачный браузер Steel.dev и создает новый контекст и страницу.
    При ошибке перебирает API ключи из config.API_STEEL_LIST (max_retries попыток).
    Возвращает (playwright, browser, context, page, steel_client, session).

    Raises:
        RuntimeError: если не удалось подключиться после MAX_STEEL_RETRIES попыток
    """
    # Убедимся, что папка для скачиваний существует
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

    # Получить список API ключей
    api_keys = getattr(config, 'API_STEEL_LIST', [])
    if not api_keys:
        raise ValueError("API_STEEL_LIST не найден или пуст в config.py")

    # Получить настройки retry
    max_retries = getattr(config, 'MAX_STEEL_RETRIES', 10)
    retry_delay = getattr(config, 'STEEL_RETRY_DELAY', 5.0)

    # Перемешать ключи для рандомизации
    random.shuffle(api_keys)

    last_error = None
    client = None
    session = None

    for attempt in range(1, max_retries + 1):
        api_key = random.choice(api_keys)

        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Попытка {attempt}/{max_retries}: выбран API key ending with ...{api_key[-6:]}")

            # Создать Steel.dev клиент
            client = AsyncSteel(steel_api_key=api_key)

            # Создать сессию Steel.dev с параметрами
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Создание Steel.dev сессии...")
            session = await client.sessions.create(
                api_timeout=1800000,  # 30 минут в миллисекундах
                use_proxy=True  # Включить прокси Steel (гео-локация)
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Сессия создана: ID={session.id}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Использован API key: ...{api_key[-6:]}")

            # Подключиться через CDP
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Подключение к сессии через CDP...")
            playwright = await async_playwright().start()
            browser = await playwright.chromium.connect_over_cdp(
                f"wss://connect.steel.dev?apiKey={api_key}&sessionId={session.id}"
            )

            # Ждать появления хотя бы одного контекста (timing issue mitigation)
            start_wait = time.time()
            while not browser.contexts and (time.time() - start_wait) < 5:
                await asyncio.sleep(0.5)
            if not browser.contexts:
                raise RuntimeError("Steel.dev сессия не создала контексты за 5 секунд")
            context = browser.contexts[0]

            # Настроить контекст для stealth-эффекта (аналог use_stealth=True)
            # Steel.dev НЕ имеет встроенного stealth, настраивается через context options
            await context.set_viewport_size({"width": 1920, "height": 1080})
            # Дополнительные anti-detection настройки можно добавить через context.add_init_script()
            # Например, переопределение navigator.webdriver:
            # await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Добавить anti-detection скрипт (опционально, но рекомендуется)
            stealth_script = """
// Remove webdriver property
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
// Other anti-detection tricks
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});
"""
            await context.add_init_script(stealth_script)

            # Взять существующую страницу или создать новую
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Страница создана в контексте Steel.dev")

            # Настройка таймаутов из config
            page.set_default_timeout(config.MAX_TIME * 1000)
            page.set_default_navigation_timeout(config.MAX_TIME * 1000)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Успешное подключение к Steel.dev")

            return playwright, browser, context, page, client, session

        except Exception as e:
            last_error = e
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка попытки {attempt}: {type(e).__name__}: {e}")

            # Очистить ресурсы перед следующей попыткой
            if session and client:
                try:
                    await client.sessions.release(session.id)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Сессия {session.id} освобождена")
                except Exception as release_err:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка освобождения сессии: {release_err}")
                finally:
                    session = None
                    client = None

            if attempt < max_retries:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Ждем {retry_delay}с перед следующей попыткой...")
                await asyncio.sleep(retry_delay)
            else:
                break

    # Все попытки исчерпаны
    error_msg = f"Не удалось подключиться к Steel.dev после {max_retries} попыток. Последняя ошибка: {last_error}"
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
    raise RuntimeError(error_msg)


async def release_browser(
    playwright: Optional[object],
    browser: Optional[Browser],
    steel_client: Optional[AsyncSteel],
    session_id: Optional[str]
) -> None:
    """
    Корректно закрывает сессию Steel.dev и освобождает ресурсы.

    Args:
        playwright: объект playwright
        browser: объект browser
        steel_client: Steel.dev клиент
        session_id: ID сессии для release
    """
    try:
        # Сначала явно закроем контексты — предотвращает каскадную сериализацию
        if browser:
            for ctx in browser.contexts:
                try:
                    await ctx.close()
                except Exception as ctx_err:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка закрытия контекста: {ctx_err}")
            await browser.close()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Браузер закрыт")
    except Exception as e:
        # Playwright bug #2771: "Invalid string length" при browser.close() с большими файлами
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка при закрытии браузера (игнорируем): {e}")

    try:
        if steel_client and session_id:
            # Steel.dev: корректное освобождение сессии (асинхронный метод)
            await steel_client.sessions.release(session_id)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Сессия Steel.dev {session_id} освобождена")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка при освобождении сессии: {e}")

    try:
        if playwright:
            await playwright.stop()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Playwright остановлен")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка при остановке playwright: {e}")


async def get_downloads(
    client: Hyperbrowser,
    session_id: str,
    download_dir: str
) -> dict:
    """
    ⚠️ DEPRECATED: Эта функция использует Hyperbrowser Cloud Storage API.
    В текущей архитектуре скачивание происходит через page.expect_download()
    и НЕ требует этого метода.

    Получить скачанные файлы из облачного хранилища Hyperbrowser
    после завершения сессии.

    Hyperbrowser сохраняет файлы в виде zip-архива. Эта функция:
    1. Ждёт завершения обработки через get_downloads_url()
    2. Скачивает zip-архив
    3. Извлекает и переименовывает файлы в DOWNLOAD_DIR

    Args:
        client: Hyperbrowser клиент
        session_id: ID завершённой сессии
        download_dir: локальная папка для сохранения

    Returns:
        dict с путями к сохранённым файлам
    """
    saved = {}
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Получение загрузок из Hyperbrowser...")

        # Ждём до 30 секунд пока Hyperbrowser подготовит zip
        max_retries = 30
        downloads_response = None
        for retry in range(max_retries):
            try:
                downloads_response = client.sessions.get_downloads_url(session_id)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Статус: {downloads_response.status}")
                if downloads_response.status == "completed":
                    break
                elif downloads_response.status == "failed":
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Загрузка не удалась: {getattr(downloads_response, 'error', 'N/A')}")
                    return saved
            except Exception as poll_err:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Ожидание загрузок: {poll_err}")
            await asyncio.sleep(1)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Таймаут ожидания загрузок Hyperbrowser")
            return saved

        # Скачиваем zip
        if not downloads_response.downloads_url:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Нет URL загрузки")
            return saved

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Скачивание zip из облака...")
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(downloads_response.downloads_url) as resp:
                resp.raise_for_status()
                zip_bytes = await resp.read()

        temp_zip = os.path.join(download_dir, f"downloads_{session_id}.zip")
        with open(temp_zip, "wb") as f:
            f.write(zip_bytes)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Zip сохранён: {temp_zip}")

        # Распаковываем
        with zipfile.ZipFile(temp_zip, "r") as zf:
            zf.extractall(download_dir)
            names = zf.namelist()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Извлечено файлов: {len(names)}")

        # Удаляем временный zip
        os.remove(temp_zip)

        saved = {}
        for name in names:
            src = os.path.join(download_dir, name)
            if name.endswith(".glb"):
                dst = os.path.join(download_dir, f"{session_id}.glb")
                os.rename(src, dst)
                saved["glb"] = dst
            elif name.endswith(".obj") or (".obj." in name) or (name.endswith("_obj.zip")):
                dst = os.path.join(download_dir, f"{session_id}_obj.zip")
                os.rename(src, dst)
                saved["obj"] = dst
            elif name.endswith(".fbx"):
                dst = os.path.join(download_dir, f"{session_id}.fbx")
                os.rename(src, dst)
                saved["fbx"] = dst
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Игнорируем файл: {name}")

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Загрузки сохранены: {list(saved.keys())}")

    except ImportError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] aiohttp не установлен, пропуск Hyperbrowser загрузок")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка получения загрузок: {e}")

    return saved
