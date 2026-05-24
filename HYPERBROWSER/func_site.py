import asyncio
import config

async def run(page):
    """
    1. Переход на страницу генерации.
    2. Проверка авторизации.
    3. Проверка количества токенов.
    """
    # 1. Переход на страницу
    print(f"Переход на страницу: {config.site_text_to_image}")
    await page.goto(config.site_text_to_image, wait_until="domcontentloaded", timeout=config.MAX_TIME * 1000)
    await asyncio.sleep(config.WAIT_TIME)

    # 2. Проверка авторизации (ждем аватар)
    print("Проверка авторизации...")
    try:
        await page.locator(config.text_account_mindvideo).wait_for(state="visible", timeout=30000)
        print("Авторизация подтверждена (аватар найден).")
    except Exception:
        raise RuntimeError("Ошибка авторизации: не найден аватар пользователя.")

    # 3. Получение количества токенов
    print("Получение количества токенов...")
    tokens_val = 0
    try:
        tokens_locator = page.locator(config.text_tokens_count).first
        await tokens_locator.wait_for(state="visible", timeout=15000)
        tokens_text = await tokens_locator.inner_text()
        tokens_text = tokens_text.strip()
        print(f"Токенов на счету: {tokens_text}")
        
        # Пробуем преобразовать в число для проверки
        tokens_val = int(''.join(filter(str.isdigit, tokens_text)))
    except Exception as e:
        print(f"Предупреждение: не удалось точно определить количество токенов ({e}). Продолжаем.")
        return "???" # Возвращаем строку, если не удалось распарсить

    # 4. Проверка лимита
    if tokens_val < 10:
        print(f"Недостаточно токенов: {tokens_val} < 10")
        raise ValueError("МАЛО ТОКЕНОВ")

    return str(tokens_val)
