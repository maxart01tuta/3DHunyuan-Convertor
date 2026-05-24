import asyncio
import config

async def run(page):
    """
    1. Прокрутка и выбор режима 4K.
    2. Прокрутка и выбор соотношения сторон 16:9.
    """
    print("Настройка интерфейса (Free 1K и 16:9)...")


    # 2. Выбор 16:9
    try:
        knopka_16_9 = page.locator(config.knopka_interface_ratio)
        await knopka_16_9.scroll_into_view_if_needed()
        await knopka_16_9.wait_for(state="visible", timeout=15000)
        await knopka_16_9.click()
        print("Соотношение сторон 16:9 выбрано.")
        await asyncio.sleep(config.WAIT_TIME)
    except Exception as e:
        print(f"Предупреждение: не удалось выбрать 16:9 ({e}). Возможно, уже выбрано.")
