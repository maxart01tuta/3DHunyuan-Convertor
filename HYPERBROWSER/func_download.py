import os
import config

async def run(page, baza_id):
    """
    1. Получение URL изображения из атрибута src.
    2. Скачивание файла через Playwright request.
    3. Сохранение в DOWNLOAD_DIR.
    """
    print(f"Попытка скачивания изображения для ID: {baza_id}...")

    # 1. Получение URL изображения
    try:
        img_locator = page.locator(config.image_url).first
        await img_locator.wait_for(state="visible", timeout=30000)
        src = await img_locator.get_attribute("src")
        
        if not src:
            raise RuntimeError("Не удалось получить атрибут 'src' изображения.")
        
        print(f"URL изображения получен: {src}")
    except Exception as e:
        raise RuntimeError(f"Ошибка при получении URL изображения: {e}")

    # 2. Подготовка пути сохранения
    if not os.path.exists(config.DOWNLOAD_DIR):
        os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    
    file_name = f"{baza_id}.jpg"
    file_path = os.path.join(config.DOWNLOAD_DIR, file_name)

    # 3. Скачивание файла
    try:
        response = await page.request.get(src)
        if response.status != 200:
            raise RuntimeError(f"Ошибка скачивания: HTTP {response.status}")
        
        content = await response.body()
        with open(file_path, "wb") as f:
            f.write(content)
        
        print(f"Файл успешно сохранен: {file_path}")
        return file_path
    except Exception as e:
        raise RuntimeError(f"Ошибка при сохранении файла: {e}")
