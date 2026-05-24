import asyncio
import config
from playwright.async_api import TimeoutError

async def run(page):
    """
    1. Нажатие кнопки Image Upscaler.
    2. Выбор 4X.
    3. Нажатие Create.
    4. Ожидание появления индикатора процесса.
    5. Ожидание исчезновения индикатора процесса.
    """
    print("Запуск Upscale процесса...")
    
    # 0. Клик на Открытие ... перед нажатием на upscale
    try:
        knopka_do_upscaler = page.locator(config.knopka_do_upscaler).first
        await knopka_do_upscaler.wait_for(state="visible", timeout=config.MAX_TIME * 1000)
        await knopka_do_upscaler.click()
        print("Кнопка перед 'Image Upscaler' нажата.")
        await asyncio.sleep(config.WAIT_TIME * 2)
    except Exception as e:
        raise RuntimeError(f"Не удалось нажать кнопку перед Image Upscaler: {e}")    
    

    # 1. Клик на knopka_image_upscaler (.first)
    try:
        btn_upscaler = page.locator(config.knopka_image_upscaler).first
        await btn_upscaler.wait_for(state="visible", timeout=config.MAX_TIME * 1000)
        await btn_upscaler.click()
        print("Кнопка 'Image Upscaler' нажата.")
        await asyncio.sleep(config.WAIT_TIME)
    except Exception as e:
        raise RuntimeError(f"Не удалось нажать кнопку Image Upscaler: {e}")

    # 2. Клик на knopka_upscale_4x
    try:
        btn_4x = page.locator(config.knopka_upscale_4x)
        await btn_4x.wait_for(state="visible", timeout=config.MAX_TIME * 1000)
        await btn_4x.click()
        print("Кнопка 'Upscale 4X' нажата.")
        await asyncio.sleep(config.WAIT_TIME)
    except Exception as e:
        raise RuntimeError(f"Не удалось нажать кнопку Upscale 4X: {e}")

    # 3. Клик на knopka_upscale_create
    try:
        btn_create = page.locator(config.knopka_upscale_create)
        await btn_create.wait_for(state="visible", timeout=config.MAX_TIME * 1000)
        await btn_create.click()
        print("Кнопка 'Create' (Upscale) нажата.")
        await asyncio.sleep(config.WAIT_TIME)
    except Exception as e:
        raise RuntimeError(f"Не удалось нажать кнопку Create для Upscale: {e}")

    # 4. Ожидание появления индикатора процесса (Ожидание появления индикатора процесса)
    print("Ожидание появления индикатора процесса Upscale...")
    try:
        indicator = page.locator(config.text_generate_process)
        await indicator.wait_for(state="visible", timeout=config.MAX_TIME * 1000)
        print("Процесс Upscale начался (индикатор появился).")
    except TimeoutError:
        print("Предупреждение: индикатор процесса Upscale не появился в течение отведенного времени. Возможно, процесс очень быстрый.")
    except Exception as e:
        print(f"Ошибка при ожидании начала Upscale: {e}")

    # 5. Исчезновение (максимальное время ожидания GENERATE_TIME * 1000 из config.py)
    print(f"Ожидание завершения Upscale (таймаут {config.GENERATE_TIME} сек)...")
    try:
        await indicator.wait_for(state="hidden", timeout=config.GENERATE_TIME * 1000)
        print("Upscale завершен (индикатор исчез).")
        await asyncio.sleep(config.WAIT_TIME)
    except TimeoutError:
        raise RuntimeError(f"Превышено время ожидания Upscale ({config.GENERATE_TIME} сек).")
    except Exception as e:
        raise RuntimeError(f"Ошибка при ожидании завершения Upscale: {e}")
