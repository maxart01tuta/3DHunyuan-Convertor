# Common Questions and Answers

## Q: Как подключиться к Hyperbrowser через Playwright?
**A:** Создайте сессию через SDK, затем используйте `ws_endpoint` для CDP подключения:
```python
session = await client.sessions.create()
browser = await p.chromium.connect_over_cdp(session.ws_endpoint)
page = browser.contexts[0].pages[0]
```

## Q: Сколько времени живёт сессия?
**A:** Контролируется параметром `timeout_minutes` (мин=1, макс=720). По умолчанию — настройки команды в дашборде. Сессия автоматически закрывается после истечения таймаута.

## Q: Какое отличие HyperAgent от обычного Playwright?
**A:** HyperAgent использует AI для выполнения задач на естественном языке — не нужно писать селекторы. Playwright даёт точный контроль, но требует написания кода. HyperAgent идеален для динамических сайтов и быстрого прототипирования.

## Q: Можно ли использовать свой прокси?
**A:** Да, `proxy_country="US"` для встроенных прокси Hyperbrowser, или `proxy_server="http://..."` для собственного прокси:
```python
CreateSessionParams(
    use_proxy=True,
    proxy_country="DE"
)
```

## Q: Как включить stealth режим?
**A:** `use_stealth=True` — стандартный stealth на всех планах. `use_ultra_stealth=True` — только для enterprise планов.

## Q: Как сохранить cookies/состояние между сессиями?
**A:** Используйте Profiles:
```python
CreateSessionParams(
    profile={"id": "my-profile-id", "persistChanges": True}
)
```

## Q: Как загрузить локальный файл?
**A:** Через Sandbox файлы или Computer Actions. Hyperbrowser не имеет прямого доступа к локальным файлам. Варианты:
1. Sandbox: `sandbox.files.write_text()` для создания файлов
2. Computer Actions: через `press_keys` с координатами
3. Загрузить файл в облако и использовать URL

## Q: Какие есть интеграции с AI frameworks?
**A:** Hyperbrowser поддерживает: BrowserUse, Claude Computer Use, Gemini Computer Use, OpenAI CUA, LangChain, LlamaIndex.

## Q: Как решить капчу автоматически?
**A:** Включите встроенный решатель:
```python
CreateSessionParams(solve_captchas=True)
```

## Q: Можно ли видеть сессию в реальном времени?
**A:** Да, через `session.live_url` — URL для просмотра текущей сессии в браузере.

## Q: Как получить скриншот без Playwright?
**A:** Через Computer Actions:
```python
response = client.computer_action.screenshot(session_id)
print(response.screenshot)  # base64
```

## Q: Какие экраны поддерживаются?
**A:** По умолчанию 1280x720. Кастомные размеры — через `ScreenConfig(width=1920, height=1080)`.

## Q: Как мигрировать с Browserless на Hyperbrowser в проекте 3DHunyuan?
**A:** Замените `create_browserless_browser()` на создание Hyperbrowser сессии. Вместо `BROWSERLESS_REGION` и `API_LIST` используйте `HYPERBROWSER_API_KEY`. Функция `close_browserless_session()` заменяется на `client.sessions.stop(session.id)`.

## Q: Как загрузить cookies из проекта в Hyperbrowser сессию?
**A:** Проект использует `Cookies/Cookies-XX.json`. Можно: 1) загрузить через `context.add_cookies()` после подключения Playwright, 2) или использовать Hyperbrowser Profiles для постоянного состояния.
