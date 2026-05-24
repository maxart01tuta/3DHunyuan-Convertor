import asyncio
import logging
import sys
import os

# Импорты наших модулей
import config
import baza
import browser
import cookies

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test-model-diagnostics")

async def test_model_selectors():
    logger.info("Запуск диагностики селекторов модели...")
    
    # 1. Берем строку из Excel для получения профиля
    row_data = baza.get_next_row()
    if not row_data:
        logger.error("Нет доступных строк в Excel для теста.")
        return
    
    profile = row_data['BAZA_PROFILE']
    
    playwright = None
    browser_obj = None
    client = None
    session = None
    context = None

    try:
        # 2. Подготовка авторизации
        auth_path = cookies.get_storage_state(profile)
        playwright, browser_obj, client, session = await browser.launch_hyperbrowser_with_retries()
        
        context = await browser_obj.new_context(storage_state=auth_path)
        page = await context.new_page()
        
        # 3. Переход на страницу
        logger.info(f"Переход на {config.site_text_to_image}")
        await page.goto(config.site_text_to_image, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # 4. Цикл диагностики
        logger.info("Начинаем бесконечный перебор возможных селекторов dropdown...")
        
        # Список потенциальных селекторов для выпадающего списка
        potential_dropdowns = [
            "//div[@class='ant-select-selector']",
            "//div[contains(@class, 'ant-select-selector')]",
            "//div[@aria-haspopup='listbox']",
            "//span[contains(text(), 'Nano Banana')] /ancestor::div[contains(@class, 'ant-select')]",
            "//div[img[@alt='Nano Banana 2 (Beta)']] /ancestor::div[contains(@class, 'ant-select-selector')]",
            "//div[@class='absolute bottom-2 right-0 z-0 h-[16px] w-[148px]']",
            "//div[contains(@class, 'cursor-pointer') and .//img]",
        ]

        attempt = 0
        while True:
            attempt += 1
            logger.info(f"--- Попытка #{attempt} ---")
            
            for selector in potential_dropdowns:
                try:
                    logger.info(f"Пробуем селектор dropdown: {selector}")
                    target = page.locator(selector).first
                    
                    if await target.is_visible(timeout=2000):
                        await target.click()
                        logger.info(f"Клик по {selector} успешен. Ждем {config.WAIT_TIME} сек...")
                        await asyncio.sleep(config.WAIT_TIME)
                        
                        # Проверяем, появилась ли модель в списке
                        model_selector = config.mindvideo_model_foto
                        logger.info(f"Проверяем наличие модели: {model_selector}")
                        model_locator = page.locator(model_selector).first
                        
                        if await model_locator.is_visible(timeout=3000):
                            logger.info("!!! УСПЕХ !!! Модель видна после клика.")
                            await model_locator.click()
                            logger.info("Клик по модели выполнен.")
                            
                            print("\n" + "="*50)
                            print("РАБОЧИЕ СЕЛЕКТОРЫ НАЙДЕНЫ:")
                            print(f'knopka_dropdown_models = "{selector}"')
                            print(f'mindvideo_model_foto = "{model_selector}"')
                            print("="*50 + "\n")
                            return
                        else:
                            logger.info("Модель не появилась. Закрываем dropdown (если открылся) кликом в сторону.")
                            await page.mouse.click(10, 10)
                    else:
                        logger.info(f"Селектор {selector} не виден на странице.")
                except Exception as e:
                    logger.warning(f"Ошибка при пробе {selector}: {e}")
                
                await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Критическая ошибка в тесте: {e}")
    finally:
        await browser.release_hyperbrowser(playwright, browser_obj, client, session, context)

if __name__ == "__main__":
    asyncio.run(test_model_selectors())
