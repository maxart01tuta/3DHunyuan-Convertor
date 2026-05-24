# Troubleshooting

## Сессия закрывается преждевременно
**Причина:** `timeout_minutes` истёк или ошибка в скрипте.
**Решение:** Увеличьте `timeout_minutes` при создании сессии. Убедитесь что `client.sessions.stop()` вызывается только в `finally` блоке.

## ConnectionRefusedError при подключении к ws_endpoint
**Причина:** Сессия не создана полностью или уже закрыта.
**Решение:**
1. Проверьте что `session.ws_endpoint` не пустой
2. Проверьте статус сессии: `session.status == "active"`
3. Увеличьте таймаут подключения
4. Пересоздайте сессию

## "Invalid API key" / Authentication Error
**Причина:** `HYPERBROWSER_API_KEY` не установлен или неверен.
**Решение:** Проверьте `.env` файл или environment variable. Получите ключ на https://dashboard.hyperbrowser.ai

## Сессия не решает капчу
**Причина:** Встроенный капча-солвер не справляется с конкретной капчей.
**Решение:**
1. Убедитесь `solve_captchas=True` при создании
2. Используйте `imageCaptchaParams` для ручной настройки
3. Попробуйте `use_stealth=True` для избежания капчи

## HyperAgent возвращает неожиданный результат
**Причина:** LLM не понял задачу или DOM слишком сложный.
**Решение:**
1. Уточните task description для HyperAgent
2. Увеличьте `max_steps`
3. Используйте `output_schema` для структурированного результата
4. Разбейте на меньшие подзадачи

## Ultra Stealth не работает
**Причина:** Ultra stealth доступен только на enterprise планах.
**Решение:** Обратитесь в info@hyperbrowser.ai для запроса доступа. Пока используйте `use_stealth=True`.

## Сессия "зависла"
**Причина:** Бесконечный цикл на странице или JavaScript error.
**Решение:**
1. Используйте `timeout_minutes` с разумным значением
2. Добавьте `page.set_default_timeout(30000)` для навигации
3. Остановите сессию: `client.sessions.stop(session.id)`

## Файлы не загружаются в браузер
**Причина:** Hyperbrowser не имеет доступа к локальной файловой системе.
**Решение:**
1. Используйте Sandbox файловые операции
2. Загрузите файл по URL в браузере: `page.goto("https://host.com/file.svg")`
3. Computer Actions для эмуляции UI взаимодействия

## 3DHunyuan Project Specific Troubleshooting

### Переход с Browserless на Hyperbrowser
**Проблема:** Текущий код использует `browser.close()` и `playwright.stop()`.
**Решение:** Замените на `await client.sessions.stop(session.id)`. Playwright browser закрывается автоматически при остановке сессии.

### Проблема с загрузкой файлов (Upload)
**Проблема:** Файлы из `Upload/` не загружаются через `input[type='file']`.
**Решение:** Убедитесь что пути абсолютные. В Hyperbrowser сессии файлы должны быть доступны через file chooser API или Computer Actions с `press_keys`.

### Photo upload sequence fails
**Проблема:** Загрузка фото 1/2/3 не подтверждается(successImageBg не появляется).
**Решение:**
1. Проверьте что файлы существуют по абсолютному пути
2. Увеличьте таймаут ожидания элемента: `MAX_TIME = 180`
3. Используйте `page.wait_for_selector` с правильным XPath
4. Проверьте что cookies активны и пользователь авторизован

### Session timeout при генерации
**Проблема:** Генерация 3D модели занимает больше времени чем timeout сессии.
**Решение:** Установите `timeout_minutes=60` или больше при создании сессии. Генерация может занять 30-120 секунд.
