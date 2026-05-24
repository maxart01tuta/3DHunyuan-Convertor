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

API_STEEL_LIST = [  
    "hb_06f9b31559530ab700899333e47a",  # Акк-4        
]
API_STEEL_LIST_ORIGINAL = [
    "hb_e7649890522ec7f7302cc5a7cae7",  # Акк-1
    "hb_978ba0671f2a0cd57baf82604f90",  # Акк-2
    "hb_385fd63a9d48d7b053eb34c280de",  # Акк-3
    "hb_06f9b31559530ab700899333e47a",  # Акк-4
    "hb_4c02c75403141a02032e790cfb28",  # Акк-5
    "hb_643782e2d26cb973abd1818c8a42",  # Акк-6
    "hb_16f13ac0b6015b6b78c035902e0c",  # Акк-7
    "hb_5bdc868dc6d569a70141ee15f3e8",  # Акк-8
    "hb_997257a83f1257c424342e5b22e6",  # Акк-9
    "hb_f4f9e2fa3d9c005221bb2ce63f36",  # Акк-10
    "hb_cee93b6eb2f4a7fa4d9fbe24d6bd",  # Акк-11
    "hb_716f022d6df7f1af4ad9dcb4b780",  # Акк-12
    "hb_32a25bf4fd68e80cfdf886c1852d",  # Акк-13
    "hb_3d039576bc9d034c22bb2a8280a9",  # Акк-14
    "hb_9a681f8e035847185ce51c9b76cc",  # Акк-15
    "hb_caa6d71c9b02dae91b9adc969975",  # Акк-16
    "hb_a56f2bd0721f867722d1a77060fc",  # Акк-17
    "hb_b40bb971f69900a64c14b7cfac3e",  # Акк-18
    "hb_77cbaebf0b8d29cd2b86b9da77fd",  # Акк-19
    "hb_367b90783331264fe159a539ec6e",  # Акк-20
    "hb_238dd7184e02a26ba99a9d57b6b6",  # Акк-21
    "hb_56083c6354f31dbd34034c4a852f",  # Акк-22
    "hb_d491402dc55aae9a81cac4c5ec84",  # Акк-23
    "hb_d491402dc55aae9a81cac4c5ec84",  # Акк-24
    "hb_bf2dfafa917b9b21953546612947",  # Акк-25
    "hb_7f791b995ab17499359b075df3a5",  # Акк-26
    "hb_9a23bc1cd3fda893f12c590d7616",  # Акк-27
    "hb_a38bbd4717a467e06e6a6b52071b",  # Акк-28
    "hb_6e1127e8fa83d86a5ff218f8273c",  # Акк-29
    "hb_7b7abc340971f715601639f9129e",  # Акк-30
    "hb_d00a64370a93b1a08913e2c13019",  # Акк-31
    "hb_5ea4d4b5c44d0c32a5a90b6dd932",  # Акк-32
    "hb_9bc8cc8b868658047a712ecdc9df",  # Акк-33
    "hb_0bd0990e06da784d5b5da05fd14d",  # Акк-34
    "hb_f2f821baa810ce6e634d885332dd",  # Акк-35
    "hb_ade57b86a86b47bc6ca2b28864fa",  # Акк-36
    "hb_d3b0b31bb4c56a545a6c2485cebb",  # Акк-37
    "hb_b95d124bb02c41bd64e2406a2e67",  # Акк-38
    "hb_c1eb69c98c0593d904418e7f73f0",  # Акк-39
    "hb_c848c443620987ef58743ce179c4",  # Акк-40
    "hb_650af0964eaa0cd9fe57f4f2b082",  # Акк-41
    "hb_f8885cd65777e2d612897eee5601",  # Акк-42
    "hb_9d01e71a8d68e9c88c64ca59c26e",  # Акк-43
    "hb_d6f7dbe6bcc8aa0eb3c1992e5d1b",  # Акк-44
    "hb_c2d84b1c7cd1ce73e2fceca1877b",  # Акк-45
    "hb_3aaf76ad08e69e02efa27c380cb0",  # Акк-46
    "hb_f2c15626f50634bb21aa139dcab3",  # Акк-47
    "hb_300224a263d6dcb8e82fa4e02172",  # Акк-48
    "hb_dc02d1495113002fb7f6791e0099",  # Акк-49
    "hb_1dad67dcfd2fa4182bd30e5f84b6",  # Акк-50
    "hb_b3676877594912cc510afd9330de",  # Акк-51
    "hb_12de620025dfeacddff746859284",  # Акк-52
    "hb_7da19fcdbfc0164ef1f4fa465a89",  # Акк-53
    "hb_e1a0af716c0c39f0bea6dae96832",  # Акк-54
    "hb_1e15dd535eb404450ef7fa904323",  # Акк-55
    "hb_98efb891ef0e05150dae285dd6ac",  # Акк-56
    "hb_6c911dc6407c19fcf1ed5867084f",  # Акк-57
    "hb_a508c765ade25f588a8b7fd4a344",  # Акк-58
    "hb_2493357a1cfbb44cef8db02ea991",  # Акк-59
    "hb_6c79b53bb6f7a9f03b10bbdf0282",  # Акк-60
    "hb_9340ddcb641b33c550be575a4c08",  # Акк-61
    "hb_ef1e3f522b21b4f0ba72c1b2d00a",  # Акк-62
    "hb_01c6ab2e3e2c9b28a262a80225a5",  # Акк-63
    "hb_5293d6c2e3eff4db4571ccbcb674",  # Акк-64
    "hb_5f515519b96d1271f84f8877da69",  # Акк-65
    "hb_d8a2b985aa678ae420165586b0ee",  # Акк-66
    "hb_3930fc44ef6cbb8cbee100a4cf92",  # Акк-67
    "hb_3b77535780606c66fe436d5cad33",  # Акк-68
    "hb_b27abf6fe29db50abe135c811761",  # Акк-69
    "hb_57c720d6dbfd8e3706dd548afd0f"   # Акк-70    
]

