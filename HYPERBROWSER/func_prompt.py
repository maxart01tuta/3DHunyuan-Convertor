import asyncio
import config

async def run(page, prompt: str):
    """
    Надежный ввод промта:
    1. Ожидание и фокус на поле.
    2. Мгновенная очистка через fill("").
    3. Надежная вставка текста через fill(prompt).
    4. Финальное 'касание' клавиатуры для активации интерфейса сайта.
    """
    if not prompt:
        print("Предупреждение: получен пустой промт.")
        return

    print(f"Ввод промта: {prompt[:50]}...")
    
    # 1. Ждем появления поля и фокусируемся
    input_locator = page.locator(config.input_prompt).first
    await input_locator.wait_for(state="visible", timeout=config.MAX_TIME * 1000)
    await input_locator.scroll_into_view_if_needed()
    await input_locator.click()
    
    # 2. Очищаем поле мгновенно
    await input_locator.fill("")
    await asyncio.sleep(0.5)
    
    # 3. Вставляем текст целиком (это самый стабильный метод против таймаутов)
    await input_locator.fill(prompt)
    
    # 4. Имитируем нажатие клавиши в конце для срабатывания триггеров сайта
    await input_locator.focus()
    await page.keyboard.press("End")
    await page.keyboard.press("Space")
    await page.keyboard.press("Backspace")
    
    print("Ввод промта завершен.")
    await asyncio.sleep(2) # Короткая пауза для фиксации состояния
