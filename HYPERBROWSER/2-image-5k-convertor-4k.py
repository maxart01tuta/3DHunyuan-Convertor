"""
Задача 005 — Cropper 5K → 4K
Обрезает JPG фото 5504×3072 → 4907×2760 (строго 16:9)
Обрезка: справа и сверху. Лево и низ остаются нетронутыми.
Использует FFmpeg crop filter с максимальным качеством JPEG.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from config import UPLOAD_DIR, DOWNLOAD_DIR

# ─── Параметры обрезки ───
# crop = out_w : out_h : x : y
# x = 0   → не трогаем левый край
# y = 312 → обрезаем 312 пикселей сверху
# out_w = 4907 → обрезаем 597 пикселей справа (5504 - 4907)
# out_h = 2760 → итоговая высота (3072 - 312)
# Итог: 4907 / 2760 = 1.7779... ≈ 16/9 (1.7777...) ✅
CROP_WIDTH  = 4907
CROP_HEIGHT = 2760
CROP_X      = 0
CROP_Y      = 312

# Исходное разрешение (для логирования)
SRC_W = 5504
SRC_H = 3072


def collect_images(folder: str) -> list:
    """Собрать все JPG файлы из папки, отсортировать по имени."""
    p = Path(folder)
    extensions = {".jpg", ".jpeg", ".JPG", ".JPEG"}
    files = sorted([
        f for f in p.iterdir()
        if f.is_file() and f.suffix in extensions
    ])
    return files


def crop_image(input_path: str, output_path: str) -> bool:
    """
    Обрезать фото через FFmpeg crop filter.
    crop=4907:2760:0:312 → оставить лево+низ, обрезать право+верх.
    -q:v 2 → максимальное JPEG качество (шкала 1-31, меньше = лучше).
    """
    cmd = [
        "ffmpeg",
        "-y",                                        # Перезаписать если файл существует
        "-i", input_path,                            # Входной файл
        "-vf",
        f"crop={CROP_WIDTH}:{CROP_HEIGHT}:{CROP_X}:{CROP_Y}",
        "-q:v", "2",                                 # Максимальное JPEG качество
        output_path                                  # Выходной файл
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print(f"\n    ❌ Ошибка FFmpeg:\n    {result.stderr[:300]}")
            return False
        return True
    except FileNotFoundError:
        print("\n❌ FFmpeg не найден! Убедитесь, что ffmpeg установлен и добавлен в PATH.")
        sys.exit(1)


def main():
    # 1. Создать выходную папку если не существует
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # 2. Собрать список фото
    images = collect_images(UPLOAD_DIR)

    if not images:
        print(f"📂 Папка {UPLOAD_DIR} пуста — JPG файлов не найдено.")
        return

    total = len(images)

    # 3. Вывести заголовок
    print()
    print("=" * 60)
    print(f"✂️  CROPPER 5K → 4K  |  Найдено файлов: {total}")
    print(f"   {SRC_W}×{SRC_H}  →  {CROP_WIDTH}×{CROP_HEIGHT}  (16:9)")
    print(f"   Обрезка: справа {SRC_W - CROP_WIDTH} px, сверху {CROP_Y} px")
    print(f"   Вход:   {UPLOAD_DIR}")
    print(f"   Выход:  {DOWNLOAD_DIR}")
    print("=" * 60)

    success = 0
    errors  = 0

    # 4. Обработка каждого файла
    for i, img_path in enumerate(images, 1):
        out_path = os.path.join(DOWNLOAD_DIR, img_path.name)
        t0 = time.time()

        print(f"  [{i}/{total}] {img_path.name} ... ", end="", flush=True)

        if crop_image(str(img_path), out_path):
            elapsed = time.time() - t0
            print(f"✅ OK ({elapsed:.1f}s)")
            success += 1
        else:
            print(f"  ❌ НЕУДАЧА: {img_path.name}")
            errors += 1

    # 5. Итоговый отчёт
    print()
    print("=" * 60)
    print(f"🎉 Готово!  ✅ Успешно: {success}  |  ❌ Ошибки: {errors}  |  Всего: {total}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
