import asyncio
import config

async def run(page):
    """
    1. Открытие выпадающего списка моделей.
    2. Выбор модели Nano Banana 2 (Beta).
    """
    print("Выбор модели...")

    # 1. Открытие выпадающего списка
    try:
        dropdown = page.locator(config.knopka_dropdown_models).first
        await dropdown.wait_for(state="visible", timeout=config.MAX_TIME * 1000)
        await dropdown.click()
        print("Выпадающий список моделей открыт.")
        await asyncio.sleep(config.WAIT_TIME)
    except Exception as e:
        raise RuntimeError(f"Не удалось открыть список моделей: {e}")

    # 2. Выбор модели ChatGPT Free
    try:
        model_option = page.locator(config.mindvideo_model_foto_test).first
        await model_option.wait_for(state="visible", timeout=config.MAX_TIME * 1000)
        await model_option.click()
        print("Модель ChatGPT Free выбрана.")
        await asyncio.sleep(config.WAIT_TIME)
    except Exception as e:
        raise RuntimeError(f"Не удалось выбрать модель: {e}")
