import asyncio
import config

async def run(page):
    """
    1. Прокрутка и выбор режима 4K.
    2. Прокрутка и выбор соотношения сторон 16:9.
    """
    print("Настройка интерфейса (4K и 16:9)...")

    # 1. Выбор 4K
    try:
        knopka_4k = page.locator(config.knopka_interface_4k)
        await knopka_4k.scroll_into_view_if_needed()
        await knopka_4k.wait_for(state="visible", timeout=15000)
        await knopka_4k.click()
        print("Режим 1K выбран.")
        await asyncio.sleep(config.WAIT_TIME)
    except Exception as e:
        print(f"Предупреждение: не удалось выбрать 4K ({e}). Возможно, уже выбрано.")

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
