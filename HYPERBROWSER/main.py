import asyncio
import logging
import sys
import os

# Импорты наших модулей
import config
import baza
import browser
import func_site
import func_prompt
import func_model
import func_interface
import func_generate
import func_upscale
import func_download
import func_autovhod

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger("mindvideo-generator")

async def process_one_row(row_data):
    """
    Полный цикл обработки одной строки из Excel.
    """
    row_number = row_data['row_number']
    baza_id = row_data['BAZA_ID']
    prompt = row_data['BAZA_PROMT']
    profile = row_data['BAZA_PROFILE']

    logger.info(f">>> Обработка строки #{row_number} [ID: {baza_id}, Профиль: {profile}]")
    
    playwright = None
    browser_obj = None
    client = None
    session = None
    context = None

    try:
        auth_path = config.get_auth_path(profile)
        session_path = config.get_session_storage_path(profile)

        # 1. Запуск Hyperbrowser
        playwright, browser_obj, client, session = await browser.launch_hyperbrowser_with_retries(profile_id=profile)

        # 2. Настройка контекста (загрузка cookies и sessionStorage)
        context = await browser.setup_context(browser_obj, profile)

        # 3. Создание страницы
        page = await context.new_page()

        # 4. Проверка авторизации и автовход (теперь это один процесс для всех)
        await func_autovhod.run(page, profile, auth_path, session_path)

        # 5. Сбор токенов
        tokens_count = await func_site.run(page)
        logger.info(f"Токены на счету: {tokens_count}")

        # 5. Ввод промпта
        await func_prompt.run(page, prompt)

        # 6. Выбор модели
        await func_model.run(page)

        # 7. Настройка интерфейса (4K, 16:9)
        await func_interface.run(page)

        # 8. Генерация
        await func_generate.run(page)

        # 9. Upscale
        await func_upscale.run(page)

        # 10. Скачивание
        await func_download.run(page, baza_id)

        # 11. Успешное завершение
        baza.mark_row_status(row_number, "ГОТОВО", tokens=tokens_count)
        logger.info(f"Успешно обработана строка #{row_number}")
        return True

    except ValueError as e:
        # Специфическая ошибка (например, мало токенов)
        error_msg = str(e)
        logger.warning(f"Ошибка при обработке строки #{row_number}: {error_msg}")
        baza.mark_row_status(row_number, error_msg)
        return False
    except Exception as e:
        # Общая ошибка
        logger.error(f"Критическая ошибка при обработке строки #{row_number}: {e}")
        baza.mark_row_status(row_number, "ОШИБКА")
        return False
    finally:
        # Безопасное освобождение ресурсов. 
        # Передаем всё что есть, функция release_hyperbrowser сама разберется с None.
        try:
            await browser.release_hyperbrowser(
                playwright=playwright, 
                browser=browser_obj, 
                client=client, 
                session=session, 
                context=context
            )
        except Exception as e:
            logger.error(f"Критический сбой в блоке очистки ресурсов: {e}")

async def main():
    logger.info("Скрипт генерации MindVideo запущен.")
    
    while True:
        # Ищем следующую задачу в Excel
        row_data = baza.get_next_row()
        
        if row_data:
            await process_one_row(row_data)
        else:
            logger.info("Нет доступных строк для обработки со статусом '#'.")
            
            if config.POLLING_MODE:
                logger.info(f"Ожидание новых строк {config.POLLING_INTERVAL} сек...")
                await asyncio.sleep(config.POLLING_INTERVAL)
            else:
                logger.info("Завершение работы (POLLING_MODE=False).")
                break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Скрипт остановлен пользователем.")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в основном цикле: {e}")
