# Конфигурация системы автоматизации Convertor GLB

import os

# Таймауты
MAX_TIME = 500  # секунд, максимальное ожидание элементов
WAIT_TIME = 5   # секунд, краткая пауза между действиями


# Настройки переподключения
MAX_STEEL_RETRIES = 10  # максимум попыток подключения
STEEL_RETRY_DELAY = 5.0  # задержка между попытками в секундах


# URL сайта
site = "https://fabconvert.com/convert/3d-model"


# Селекторы для iLove3DM
input_upload = "//input[@id='fb']" # Upload GLB на сайт
knopka_vibor_type = "//div[@class='og']" # Pop-up выпадающий список выбора Типа файла
knopka_obj = "//span[contains(text(), 'OBJ')][1]" # Выбор OBJ тип
knopka_fbx = "//span[contains(text(), 'FBX')][1]" # Выбор FBX тип
knopka_blend = "//span[contains(text(), 'BLEND')][1]" # Выбор FBX тип
knopka_convert = "//a[@class='k x pb jf']" # Старт Convet to OBJ
knopka_download = "//a[@id='yj']" # Кнопка Download

knopka_close_reklama = "//div[@class='continue-prompt-text']" # Закрыть рекламу


# Пути

EXCEL_FILE = r"D:\MAX\PYTHON\STOCK-PYTHON\3DHunyuan-Convertor\Baza-3dhunyuan.xlsx"
DOWNLOAD_DIR = r"D:\MAX\PYTHON\STOCK-PYTHON\3DHunyuan-Convertor\Download"
SCREENSHOTS_FOLDER = r"D:\MAX\PYTHON\STOCK-PYTHON\3DHunyuan-Convertor\Download"
UPLOAD_DIR = r"D:\MAX\PYTHON\STOCK-PYTHON\3DHunyuan-Convertor\Upload"


# ============================================
# HYPERBROWSER.AI НАСТРОЙКИ
# ============================================

# API ключи Hyperbrowser (каждый раз для новой сессии выбирается рандомно)

# API ключи Hyperbrowser (DEPRECATED)
API_HYPERBROWSER_LIST_TEST = [
    "hb_643782e2d26cb973abd1818c8a42",  # Акк-6 
]
API_HYPERBROWSER_LIST = [
    "hb_b3676877594912cc510afd9330de",  # Акк-1  Atomic 
    "hb_643782e2d26cb973abd1818c8a42",  # Акк-6 - Забанили через 1 день
    "hb_16f13ac0b6015b6b78c035902e0c",  # Акк-7
    "hb_5bdc868dc6d569a70141ee15f3e8",  # Акк-8 - Забанили через 1 день
    "hb_a1854b87d17c0c31391ed81f2f43",  # Акк-9 gmail     
    "hb_5ea4d4b5c44d0c32a5a90b6dd932",  # Акк-32
    "hb_9bc8cc8b868658047a712ecdc9df",  # Акк-33
    "hb_0bd0990e06da784d5b5da05fd14d",  # Акк-34
    "hb_f2f821baa810ce6e634d885332dd",  # Акк-35    
    "hb_d3b0b31bb4c56a545a6c2485cebb",  # Акк-37
    "hb_b95d124bb02c41bd64e2406a2e67",  # Акк-38
    "hb_c1eb69c98c0593d904418e7f73f0",  # Акк-39
    "hb_c848c443620987ef58743ce179c4",  # Акк-40
    "hb_650af0964eaa0cd9fe57f4f2b082",  # Акк-41
    
]

