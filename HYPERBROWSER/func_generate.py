import asyncio
import config
from playwright.async_api import TimeoutError

async def run(page):
    """
    1. Нажатие кнопки генерации.
    2. Ожидание появления индикатора процесса.
    3. Ожидание исчезновения индикатора процесса (завершение).
    """
    print("Запуск генерации...")

    # 1. Нажатие кнопки Create
    try:
        btn_generate = page.locator(config.knopka_generate)
        await btn_generate.wait_for(state="visible", timeout=config.MAX_TIME * 1000)
        await btn_generate.click()
        print("Кнопка 'Create' нажата.")
    except Exception as e:
        raise RuntimeError(f"Не удалось нажать кнопку генерации: {e}")

    # 2. Ожидание появления индикатора процесса (начала генерации)
    print("Ожидание начала генерации...")
    try:
        indicator = page.locator(config.text_generate_process)
        await indicator.wait_for(state="visible", timeout=config.MAX_TIME * 1000)
        print("Процесс генерации начался (индикатор появился).")
    except TimeoutError:
        print("Предупреждение: индикатор процесса не появился в течение 30 секунд. Возможно, генерация очень быстрая или произошла ошибка.")
    except Exception as e:
        print(f"Ошибка при ожидании начала генерации: {e}")

    # 3. Ожидание исчезновения индикатора процесса (завершение генерации)
    print(f"Ожидание завершения генерации (таймаут {config.GENERATE_TIME} сек)...")
    try:
        await indicator.wait_for(state="hidden", timeout=config.GENERATE_TIME * 1000)
        print("Генерация завершена (индикатор исчез).")
        await asyncio.sleep(config.WAIT_TIME)
    except TimeoutError:
        raise RuntimeError(f"Превышено время ожидания генерации ({config.GENERATE_TIME} сек).")
    except Exception as e:
        raise RuntimeError(f"Ошибка при ожидании завершения генерации: {e}")
