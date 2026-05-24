"""
Диагностический скрипт для проверки загрузки GLB на fabconvert.com.
Запускает браузер Steel.dev, переходит на сайт и выполняет подробную
диагностику на этапе загрузки файла.
"""

import asyncio
import os
import sys
from datetime import datetime

import config
import baza
from browser import launch_browser, release_browser, wait_for_element
from func_site import run as func_site_run


def _ts():
    return datetime.now().strftime('%H:%M:%S')


async def diagnose_upload(page, steel_client, session_id: str):
    """
    Подробная диагностика загрузки GLB файла.
    """
    print(f"\n{'='*70}")
    print(f"[{_ts()}] 🔍 НАЧАЛО ДИАГНОСТИКИ ЗАГРУЗКИ")
    print(f"{'='*70}")

    # === 1. Найти первый GLB файл в UPLOAD_DIR ===
    upload_dir = config.UPLOAD_DIR
    glb_files = [f for f in os.listdir(upload_dir) if f.endswith('.glb')] if os.path.exists(upload_dir) else []

    if not glb_files:
        print(f"[{_ts()}] ❌ Нет GLB файлов в {upload_dir}")
        print(f"[{_ts()}] Поместите хотя бы один .glb файл в папку Upload")
        return

    glb_file = glb_files[0]
    glb_path = os.path.join(upload_dir, glb_file)
    file_size_mb = os.path.getsize(glb_path) / (1024 * 1024)
    print(f"[{_ts()}] 📦 Тестовый файл: {glb_file} ({file_size_mb:.1f}MB)")

    # === 2. ДИАГНОСТИКА: Все input элементы на странице ===
    print(f"\n{'─'*70}")
    print(f"[{_ts()}] 🔍 ДИАГНОСТИКА: Все <input> элементы на странице")
    print(f"{'─'*70}")

    all_inputs = await page.evaluate("""() => {
        const inputs = document.querySelectorAll('input');
        return Array.from(inputs).map((el, i) => ({
            index: i,
            id: el.id || '(нет)',
            type: el.type || '(нет)',
            name: el.name || '(нет)',
            accept: el.accept || '(нет)',
            className: el.className || '(нет)',
            disabled: el.disabled,
            visible: el.offsetParent !== null,
            display: getComputedStyle(el).display,
            opacity: getComputedStyle(el).opacity,
            width: el.offsetWidth,
            height: el.offsetHeight,
            multiple: el.multiple,
            files_count: el.files ? el.files.length : 0,
            parentTag: el.parentElement ? el.parentElement.tagName : '(нет)',
            parentId: el.parentElement ? (el.parentElement.id || '(нет)') : '(нет)'
        }));
    }""")

    for inp in all_inputs:
        print(f"  [{inp['index']}] id='{inp['id']}' type='{inp['type']}' name='{inp['name']}' accept='{inp['accept']}'")
        print(f"      disabled={inp['disabled']} visible={inp['visible']} display='{inp['display']}' opacity='{inp['opacity']}'")
        print(f"      size={inp['width']}x{inp['height']} multiple={inp['multiple']} files={inp['files_count']}")
        print(f"      parent=<{inp['parentTag']} id='{inp['parentId']}'>")

    # === 3. ДИАГНОСТИКА: Все input[type=file] ===
    print(f"\n{'─'*70}")
    print(f"[{_ts()}] 🔍 ДИАГНОСТИКА: Все <input type='file'> элементы")
    print(f"{'─'*70}")

    file_inputs = await page.evaluate("""() => {
        const inputs = document.querySelectorAll('input[type="file"]');
        return Array.from(inputs).map((el, i) => ({
            index: i,
            id: el.id || '(нет)',
            name: el.name || '(нет)',
            accept: el.accept || '(нет)',
            multiple: el.multiple,
            disabled: el.disabled,
            visible: el.offsetParent !== null,
            display: getComputedStyle(el).display,
            opacity: getComputedStyle(el).opacity,
            position: getComputedStyle(el).position,
            zIndex: getComputedStyle(el).zIndex,
            width: el.offsetWidth,
            height: el.offsetHeight,
            rect: el.getBoundingClientRect().toJSON(),
            files_count: el.files ? el.files.length : 0
        }));
    }""")

    if not file_inputs:
        print(f"  ❌ НЕТ ни одного <input type='file'> на странице!")
    else:
        for fi in file_inputs:
            print(f"  [{fi['index']}] id='{fi['id']}' accept='{fi['accept']}' multiple={fi['multiple']}")
            print(f"      disabled={fi['disabled']} visible={fi['visible']} display='{fi['display']}' opacity='{fi['opacity']}'")
            print(f"      position='{fi['position']}' zIndex='{fi['zIndex']}' size={fi['width']}x{fi['height']}")
            print(f"      rect={fi['rect']}")
            print(f"      files={fi['files_count']}")

    # === 4. ДИАГНОСТИКА: Проверка нашего селектора из конфига ===
    print(f"\n{'─'*70}")
    print(f"[{_ts()}] 🔍 ДИАГНОСТИКА: Проверка селектора из config.py")
    print(f"{'─'*70}")

    xpath_sel = config.input_upload
    css_sel = config.input_upload_css
    print(f"  XPath селектор: {xpath_sel}")
    print(f"  CSS селектор:   {css_sel}")

    # Проверка XPath
    xpath_result = await page.evaluate("""(sel) => {
        const r = document.evaluate(sel, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        const el = r.singleNodeValue;
        if (!el) return { found: false, reason: 'XPath не нашёл элемент' };
        return {
            found: true,
            tagName: el.tagName,
            id: el.id,
            type: el.type,
            accept: el.accept || '(нет)',
            disabled: el.disabled,
            visible: el.offsetParent !== null,
            display: getComputedStyle(el).display,
            opacity: getComputedStyle(el).opacity,
            width: el.offsetWidth,
            height: el.offsetHeight
        };
    }""", xpath_sel)

    print(f"  XPath результат: {xpath_result}")

    # Проверка CSS
    css_result = await page.evaluate("""(sel) => {
        const el = document.querySelector(sel);
        if (!el) return { found: false, reason: 'CSS селектор не нашёл элемент' };
        return {
            found: true,
            tagName: el.tagName,
            id: el.id,
            type: el.type,
            accept: el.accept || '(нет)',
            disabled: el.disabled,
            visible: el.offsetParent !== null,
            display: getComputedStyle(el).display,
            opacity: getComputedStyle(el).opacity,
            width: el.offsetWidth,
            height: el.offsetHeight
        };
    }""", css_sel)

    print(f"  CSS результат:   {css_result}")

    # === 5. ДИАГНОСТИКА: Проверка СТАРОГО селектора input#fb ===
    print(f"\n{'─'*70}")
    print(f"[{_ts()}] 🔍 ДИАГНОСТИКА: Проверка СТАРОГО селектора input#fb")
    print(f"{'─'*70}")

    old_css_result = await page.evaluate("""() => {
        const el = document.querySelector('input#fb');
        if (!el) return { found: false, reason: 'input#fb НЕ найден на странице' };
        return {
            found: true,
            tagName: el.tagName,
            id: el.id,
            type: el.type,
            accept: el.accept || '(нет)',
            disabled: el.disabled,
            visible: el.offsetParent !== null
        };
    }""")

    print(f"  input#fb результат: {old_css_result}")

    # === 6. ДИАГНОСТИКА: Все элементы с id, содержащим буквы fb/gb ===
    print(f"\n{'─'*70}")
    print(f"[{_ts()}] 🔍 ДИАГНОСТИКА: Все элементы с id содержащим 'fb' или 'gb'")
    print(f"{'─'*70}")

    fb_gb_elements = await page.evaluate("""() => {
        const all = document.querySelectorAll('[id]');
        return Array.from(all)
            .filter(el => el.id.includes('fb') || el.id.includes('gb'))
            .map(el => ({
                tag: el.tagName,
                id: el.id,
                type: el.type || '(нет)',
                className: el.className || '(нет)'
            }));
    }""")

    if not fb_gb_elements:
        print(f"  ❌ НЕТ элементов с id содержащим 'fb' или 'gb'")
    else:
        for el in fb_gb_elements:
            print(f"  <{el['tag']} id='{el['id']}' type='{el['type']}' class='{el['className']}'>")

    # === 7. Попытка загрузки файла через Steel + CDP ===
    print(f"\n{'─'*70}")
    print(f"[{_ts()}] 🔍 ПОПЫТКА ЗАГРУЗКИ ФАЙЛА")
    print(f"{'─'*70}")

    cdp_session = None
    try:
        # Шаг 7.1: Загрузить файл в Steel session storage
        print(f"[{_ts()}] → Шаг 1: Загрузка файла в Steel.dev session storage...")
        with open(glb_path, 'rb') as f:
            session_file = await steel_client.sessions.files.upload(
                session_id=session_id,
                file=f
            )
        remote_path = session_file.path
        print(f"[{_ts()}] ✓ Файл загружен в Steel: remote_path = {remote_path}")

        if not remote_path:
            print(f"[{_ts()}] ❌ remote_path пустой!")
            return
        if not remote_path.startswith('/files/'):
            print(f"[{_ts()}] ⚠️ remote_path НЕ начинается с /files/ — это может быть проблемой")

        # Шаг 7.2: Проверка input через CDP
        print(f"[{_ts()}] → Шаг 2: Поиск input через CDP DOM.querySelector...")
        context = page.context
        cdp_session = await context.new_cdp_session(page)

        dom_document = await cdp_session.send("DOM.getDocument")
        root_node_id = dom_document["root"]["nodeId"]
        print(f"[{_ts()}] ✓ DOM документ получен, root nodeId: {root_node_id}")

        # Пробуем CSS селектор из конфига
        print(f"[{_ts()}] → Попытка с CSS селектором из конфига: '{css_sel}'")
        input_node = await cdp_session.send("DOM.querySelector", {
            "nodeId": root_node_id,
            "selector": css_sel
        })

        node_id = input_node.get("nodeId")
        if not node_id or node_id == 0:
            print(f"[{_ts()}] ❌ Input НЕ найден через CDP с селектором '{css_sel}'")
            print(f"[{_ts()}]   CDP ответ: {input_node}")

            # Пробуем найти ЛЮБОЙ input[type=file]
            print(f"[{_ts()}] → Попытка найти любой input[type=file] через CDP...")
            any_file_input = await cdp_session.send("DOM.querySelector", {
                "nodeId": root_node_id,
                "selector": "input[type='file']"
            })
            any_node_id = any_file_input.get("nodeId")
            if any_node_id and any_node_id != 0:
                print(f"[{_ts()}] ✓ Найден input[type=file] через CDP, nodeId: {any_node_id}")
                # Получить атрибуты найденного элемента
                attrs = await cdp_session.send("DOM.getAttributes", {"nodeId": any_node_id})
                print(f"[{_ts()}]   Атрибуты: {attrs}")
                node_id = any_node_id
            else:
                print(f"[{_ts()}] ❌ НЕ найден даже любой input[type=file] через CDP!")
                print(f"[{_ts()}]   CDP ответ: {any_file_input}")
                return
        else:
            print(f"[{_ts()}] ✓ Input найден через CDP, nodeId: {node_id}")

        # Шаг 7.3: Установить файл через CDP
        print(f"[{_ts()}] → Шаг 3: DOM.setFileInputFiles с remote_path='{remote_path}'...")
        await cdp_session.send("DOM.setFileInputFiles", {
            "files": [remote_path],
            "nodeId": node_id
        })
        print(f"[{_ts()}] ✓ DOM.setFileInputFiles выполнен БЕЗ ошибок!")

        # Шаг 7.4: Проверить, что файл действительно установлен в input
        print(f"[{_ts()}] → Шаг 4: Проверка файлов в input после setFileInputFiles...")
        files_check = await page.evaluate("""(sel) => {
            const el = document.querySelector(sel);
            if (!el) return { found: false };
            return {
                found: true,
                files_count: el.files ? el.files.length : 0,
                file_names: el.files ? Array.from(el.files).map(f => f.name) : [],
                file_sizes: el.files ? Array.from(el.files).map(f => f.size) : []
            };
        }""", css_sel)
        print(f"[{_ts()}]   Результат проверки: {files_check}")

        # Шаг 7.5: Проверка изменений на странице после загрузки
        print(f"[{_ts()}] → Шаг 5: Проверка реакции страницы на загрузку...")
        await asyncio.sleep(3)

        # Проверяем, появился ли текст о загрузке или изменилась страница
        page_state = await page.evaluate("""() => {
            const body = document.body.innerText.substring(0, 500);
            const progressBars = document.querySelectorAll('[class*="progress"], [class*="loading"], [class*="upload"]');
            const errorElements = document.querySelectorAll('[class*="error"], [class*="alert"], [role="alert"]');
            return {
                body_preview: body,
                progress_count: progressBars.length,
                error_count: errorElements.length,
                error_texts: Array.from(errorElements).map(e => e.textContent).slice(0, 5)
            };
        }""")
        print(f"[{_ts()}]   Состояние страницы: progress={page_state['progress_count']}, errors={page_state['error_count']}")
        if page_state['error_texts']:
            print(f"[{_ts()}]   ⚠️ Тексты ошибок: {page_state['error_texts']}")
        print(f"[{_ts()}]   Превью body: {page_state['body_preview'][:200]}...")

        # Шаг 7.6: Проверка — видна ли кнопка выбора типа (индикатор успешной загрузки)
        print(f"[{_ts()}] → Шаг 6: Проверка knopka_vibor_type...")
        try:
            await wait_for_element(page, config.knopka_vibor_type, timeout=15)
            print(f"[{_ts()}] ✅ knopka_vibor_type НАЙДЕН — загрузка УСПЕШНА!")
        except TimeoutError:
            print(f"[{_ts()}] ❌ knopka_vibor_type НЕ найден за 15с — загрузка НЕ сработала")
            print(f"[{_ts()}]   Возможно файл не загрузился или сайт не распознал загрузку")

    except Exception as e:
        print(f"\n[{_ts()}] ❌ ОШИБКА при загрузке: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if cdp_session:
            try:
                await cdp_session.detach()
            except Exception:
                pass

    print(f"\n{'='*70}")
    print(f"[{_ts()}] 🔍 КОНЕЦ ДИАГНОСТИКИ")
    print(f"{'='*70}")


async def main():
    """
    Запуск диагностики: браузер → сайт → диагностика загрузки.
    """
    print("=" * 70)
    print(f"[{_ts()}] 🔍 ДИАГНОСТИЧЕСКИЙ СКРИПТ test_upload.py")
    print(f"[{_ts()}] Сайт: {config.site}")
    print(f"[{_ts()}] Upload из: {config.UPLOAD_DIR}")
    print(f"[{_ts()}] input_upload (XPath): {config.input_upload}")
    print(f"[{_ts()}] input_upload_css:     {config.input_upload_css}")
    print("=" * 70)

    playwright = None
    browser = None
    steel_client = None
    session = None

    try:
        # === 1. Запуск браузера ===
        print(f"\n[{_ts()}] Запуск браузера Steel.dev...")
        playwright, browser, context, page, steel_client, session = await launch_browser()
        sid = session.id
        print(f"[{_ts()}] Сессия создана: {sid}")

        # === 2. Переход на сайт ===
        print(f"\n[{_ts()}] Переход на сайт...")
        await func_site_run(page, config.site)

        # === 3. Закрытие рекламы ===
        try:
            await wait_for_element(page, config.knopka_close_reklama, timeout=5)
            await page.click(config.knopka_close_reklama)
            print(f"[{_ts()}] Реклама закрыта")
        except TimeoutError:
            print(f"[{_ts()}] Рекламы нет (ок)")

        # === 4. ДИАГНОСТИКА ЗАГРУЗКИ ===
        await diagnose_upload(page, steel_client, sid)

    except Exception as e:
        print(f"\n[{_ts()}] ❌ Критическая ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # === 5. Закрытие ===
        print(f"\n[{_ts()}] Закрытие сессии...")
        await release_browser(playwright, browser, steel_client, session.id if session else None)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{_ts()}] Прервано пользователем")
        sys.exit(0)
