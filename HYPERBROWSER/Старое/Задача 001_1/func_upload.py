"""
Загрузка GLB файла на fabconvert.com.
"""

import asyncio
import os
import subprocess
import tempfile
from datetime import datetime
from config import MAX_TIME, WAIT_TIME, UPLOAD_DIR, input_upload, knopka_obj
from browser import wait_for_element
from hyperbrowser.exceptions import HyperbrowserError


def _ts():
    """Возвращает текущий timestamp для логов."""
    return datetime.now().strftime('%H:%M:%S')


async def compress_glb_draco(input_path: str) -> str:
    """Compress GLB using gltf-pipeline CLI with Draco compression."""
    # Generate compressed output path
    compressed_path = input_path.replace('.glb', '_compressed.glb')

    # Use gltf-pipeline CLI
    cmd = [
        'gltf-pipeline',
        '-i', input_path,
        '-o', compressed_path,
        '-d',  # Enable Draco compression
        '--draco.compressionLevel', '10',  # Maximum compression
        '--stats'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Draco compression failed: {result.stderr}")

    if not os.path.exists(compressed_path):
        raise FileNotFoundError(f"Compressed file not created: {compressed_path}")

    # Log compression stats
    orig_size = os.path.getsize(input_path)
    comp_size = os.path.getsize(compressed_path)
    ratio = (1 - comp_size/orig_size) * 100
    print(f"[{_ts()}] 📦 GLB compressed: {orig_size/1024/1024:.1f}MB → {comp_size/1024/1024:.1f}MB ({ratio:.1f}% reduction)")

    return compressed_path


async def run(page, hb_client, session_id: str, baza_id: str):
    """
    Загрузка GLB файла через input[type=file] с использованием Hyperbrowser upload API.
    Поддерживает файлы >50MB.

    Args:
        page: объект страницы Playwright
        hb_client: Hyperbrowser клиент (для upload_file API)
        session_id: ID сессии Hyperbrowser
        baza_id: идентификатор из Excel (для формирования имени файла)

    Raises:
        FileNotFoundError: если GLB файл не найден
        RuntimeError: если загрузка не удалась
    """
    # Путь к GLB файлу
    glb_path = os.path.join(UPLOAD_DIR, f"{baza_id}.glb")

    # Проверка существования файла
    if not os.path.exists(glb_path):
        raise FileNotFoundError(f"GLB файл не найден: {glb_path}")

    file_size_mb = os.path.getsize(glb_path) / (1024 * 1024)
    print(f"[{_ts()}] 📦 Загрузка файла {file_size_mb:.1f}MB: {glb_path}")

    try:
        # Ожидание input[type=file]
        await wait_for_element(page, input_upload, timeout=MAX_TIME)

        # ⭐ Upload файла в сессию через Hyperbrowser API (обход CDP лимита 50MB)
        print(f"[{_ts()}] → Загрузка в Hyperbrowser session storage...")
        upload_resp = await hb_client.sessions.upload_file(session_id, glb_path)
        remote_path = upload_resp.file_path
        print(f"[{_ts()}] ✓ Файл загружен в сессию: {remote_path}")

        # Установка input на remote файл (уже внутри сессии)
        await page.set_input_files(input_upload, remote_path)
        print(f"[{_ts()}] ✓ Input установлен, ожидание конвертации...")

        # Ожидание появления кнопок форматов (индикатор завершения загрузки)
        await wait_for_element(page, knopka_obj, timeout=MAX_TIME * 2)

        print(f"[{_ts()}] ✅ GLB успешно загружен и обработан")

    except Exception as e:
        print(f"[{_ts()}] ✗ Ошибка загрузки GLB: {type(e).__name__}: {e}")
        raise
