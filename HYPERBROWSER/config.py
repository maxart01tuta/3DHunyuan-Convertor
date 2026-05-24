
import os

# Таймауты
MAX_TIME = 300  # секунд, максимальное ожидание элементов
WAIT_TIME = 3   # секунд, краткая пауза между действиями
GENERATE_TIME = 2000  # секунд, ожидание завершения генерации

# Режим продукта: 1 - Text-to-Foto, 2 - Text-to-Video, 3 - Image-to-Video, 4 - Video-to-Video, 
type_product = 1

# URL сайтов
site_registration = "https://www.mindvideo.ai/auth/signup/" # Страница для скрипта регистрации
site_vhod = "https://www.mindvideo.ai/auth/signin/" # Страница для скрипта автовхода
site_text_to_image = "https://www.mindvideo.ai/text-to-image/" # Страница для Генерации Фото
site_merepost = "https://tempmail.plus/ru/#!"

# Пароли (здесь оставить, не выосить в env)
mindvideo_password = "Kristina1988!"


# СЕЛЕКТОРЫ РЕГИСТРАЦИИ
input_mail_registration = "//input[@id='email']" # было, но при смене языка не находит : "//input[@placeholder='Email address']
input_nickname_registration = "//input[@id='nickname']" # было, но при смене языка не находит : "//input[@placeholder='Nickname']"
input_password_registration = "//input[@id='password']" # было, но при смене языка не находит : "//input[@placeholder='Password']"
knopka_continue_registration = "//button[@type='submit']" # было, но при смене языка не находит : "//*[contains(text(),'Continue')]"

input_code_verify = "//input[@id='verificationCode']"
knopka_verify_registration = "//button[@type='submit']" # было, но при смене языка не находит : "//*[contains(text(),'Verify')]"
text_account_mindvideo = "//img[@alt='avatar']" # Если отображается - мы авторизовались

# Селекторы Merepost
input_mail_merepost = "//input[@id='pre_button']"
knopka_dropdown_mails = "//button[@id='domain']" # Открывает выпадающее меню со списком доменов почт
option_merepost = "//button[contains(@class,'dropdown-item') and normalize-space(text())='merepost.com']" # Кнопка выбора домена merepost.com для почты
text_verify_mindvideo = "//*[contains(text(),'MindVideo.ai ')]" # Письмо от MindVideo
text_verify_code = "//span[@data-redactor-style-cache='color: rgb(0, 123, 255);']"

# СЕЛЕКТОРЫ АВТОВХОДА
input_mail_vhod = "//input[@placeholder='Email']"
input_password_vhod = "//input[@placeholder='Password']"
knopka_login_vhod = "//span[normalize-space()='Login']"


# СЕЛЕКТОРЫ СБОР КРЕДИТОВ
knopka_check_in_claim = "//*[contains(text(),'Check In & Claim ')]"
knopka_check_in = "//button[@class='ant-btn css-1cxyvzc ant-btn-default ant-btn-color-default ant-btn-variant-outlined ant-btn-lg w-[200px] rounded-3xl border-none font-medium']"
knopka_check_in_disabled = "//button[@type='button' and @disabled and .//span[normalize-space()='Check In']]"
text_tokens_count = "//span[@class='text-[#00C8FF]']" # Количество токенов


# СЕЛЕКТОРЫ ИНТЕРФЕЙСА
input_prompt = "//textarea[@maxlength='2000']"
knopka_interface_4k = "//div[contains(text(),'1K')]" # было 4K, теперь не нужно "//div[contains(text(),'4K')]" # Устанавливает рамер фото 4K
knopka_interface_ratio = "//span[contains(text(),'16:9')]" # Устанавливает соотношение сторон 16:9 по умолчанию
knopka_generate = "//span[normalize-space()='Create']"
text_generate_process = "//span[normalize-space()='Upgrade for faster generation']" # Процесс генерации
knopka_dropdown_download = "//div[@class='rounded-lg p-1 text-white cursor-pointer transition-colors hover:bg-white/[.12]']" # Пока не исспользуем
image_url = "//img[@class='relative h-full w-full object-contain']" # Из этого img должен брать src - это URL для скачивания

# Селекторы МОДЕЛИ
knopka_dropdown_models = "//div[@class='ant-select-selector']" # было "//div[@class='absolute bottom-2 right-0 z-0 h-[16px] w-[148px]']"  # было "//div[@class='h-full rounded-lg border border-white/[.08] bg-[#343434] py-[8px]']" # было не работало "//div[@aria-describedby='_r_m_']" # Открывает список моделей
mindvideo_model_foto = "//img[@alt='Nano Banana 2 (Beta)']" # Модель Nano Banana 2 (менять, если надо, на другую модель)
mindvideo_model_foto_test = "//img[@alt='GPT Image 2 Free']"# Модель тестовая Free ChatGPT 1k для скрипта func_model_test_free.py когда надо протестировать сам промт фото


# Селекторы Upscale
knopka_do_upscaler = "//div[@class='group relative h-full w-full cursor-pointer']" # Кнопка ... чтобы появилась потом кнопка Image Upscaler
knopka_image_upscaler = "//button[contains(@class, 'w-1/2') and .//span[contains(text(), 'Image Upscaler')]]" # было кнопка которая должна нажимать без открытия фото - "//span[contains(@class, 'whitespace-nowrap') and contains(text(), 'Image Upscaler')]" # Кнопка Image Upscaler может нажмется даже если ен видно. Если не нажмется, сначаа добавить нажатие до нее
knopka_upscale_4x = "//div[contains(@class, 'h-[32px]') and contains(@class, 'w-[55px]') and contains(., '4')]" # Upscale 4X
knopka_upscale_create = "//button[contains(@class, 'ant-btn') and contains(@class, 'h-[44px]') and contains(., 'Create')]" # Старт Upscale процесса


# MoreLogin API
MORELOGIN_BASE_URL = "http://127.0.0.1:40000"
API_MORELOGIN_LIST = [] # Отключил Авторизацию # Акк-01 API = 1546bede421c2c4f7d48b653afcbc811c7cb9f20e27ff3a2....
MORELOGIN_PROFILE_ID = "2048142019352137728" # Акк-01 = 2048142019352137728 | Акк-02 = 2048344914366369792 | Акк-03 = 2048366390985428992 | Акк-04 = 2048387642630410240 | Акк-05 = 2048437439886331904 | Акк-06 = 2048473708838326272 | Акк-07 = 2048482804773752832 | Акк-08 = 2048508282112905216 | Акк-09 = 2048698798645514240 | Акк-10 =  2048714090553610240

# Параметры ретраев/таймаутов MoreLogin
MAX_MORELOGIN_RETRIES = 5
MORELOGIN_RETRY_DELAY = 2.0
MORELOGIN_HTTP_TIMEOUT = 30
MORELOGIN_START_WAIT_TIMEOUT = 60
MORELOGIN_ENV_NAME_PREFIX = "mindvideo-autoreg"



# Пути
COOKIES_FOLDER = "D:\\MAX\\PYTHON\\VIDEO\\MindVideo-Cloud\\Cookies"
PROFILES_FOLDER = "D:\\MAX\\PYTHON\\VIDEO\\MindVideo-Cloud\\Profiles"
EXCEL_FILE = "D:\\MAX\\PYTHON\\VIDEO\\MindVideo-Cloud\\Baza-MindVideo.xlsx"
EXCEL_FILE_2 = "D:\\MAX\\PYTHON\\VIDEO\\MindVideo-Cloud\\Baza-MindVideo-2.xlsx" # База для Автосбора (строка 57 и 113 в скрипте) параллельно
DOWNLOAD_DIR = r"D:\MAX\PYTHON\VIDEO\MindVideo-Cloud\Download"
UPLOAD_DIR = r"D:\MAX\PYTHON\VIDEO\MindVideo-Cloud\Upload"

def get_cookie_path(profile_num: str) -> str:
    """
    Возвращает путь к файлу cookie для указанного номера профиля.
    profile_num — строка из BAZA_PROFILE (напр. "01"), файл: Cookies/Weave-cookies-01.json
    """
    profile_clean = str(profile_num).strip()
    return f"Cookies/Weave-cookies-{profile_clean}.json"

# Режим работы: True = обработать все и выйти, False = polling каждые 60 сек
POLLING_MODE = False
POLLING_INTERVAL = 60  # секунд



# ===== Storage State (новая авторизация) =====
AUTH_FILENAME = "mindvideo-auth.json"
SESSION_STORAGE_FILENAME = "mindvideo-session.json"
USE_HYPERBROWSER_PROFILES = True


def get_auth_path(profile_num: str) -> str:
    """
    Возвращает путь к файлу storage_state для указанного номера профиля.
    profile_num — строка из BAZA_PROFILE (напр. "01").
    Файл: Profiles/01/weavy-auth.json
    """
    profile_clean = str(profile_num).strip()
    return os.path.join(PROFILES_FOLDER, profile_clean, AUTH_FILENAME)


def get_session_storage_path(profile_num: str) -> str:
    """
    Возвращает путь к файлу session_storage для указанного номера профиля.
    """
    profile_clean = str(profile_num).strip()
    return os.path.join(PROFILES_FOLDER, profile_clean, SESSION_STORAGE_FILENAME)


# DEPRECATED: get_cookie_path() больше не используется для основной авторизации.
# Авторизация теперь работает через storage_state (get_auth_path).

# Системная папка загрузок Windows (куда Chrome сохраняет по умолчанию)
SYSTEM_DOWNLOAD_DIR = os.path.expanduser("~\\Downloads")





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

# Настройки переподключения
MAX_HYPERBROWSER_RETRIES = 10  # максимум попыток подключения
HYPERBROWSER_RETRY_DELAY = 5.0  # задержка между попытками в секундах

# --- СПИСОК ПРОКСИ (Работает только PROXIES массив, осталньые для примера) ---


PROXIES = [
    "http://BQrDDXuxtvT0xJQW:QGYClXqj5K6vwzF3@geo.floppydata.com:10080", # Акк-02
    "http://mCq0Pz5pBWYUexOY:9Un3lK1mvAqd3cfn@geo.floppydata.com:10080", # Акк-02
    "http://0RtfszRUV52xyLYR:X2lURTJoF5cIILpw@geo.floppydata.com:10080", # Акк-02
    "http://iupqkzIzJ84O9C4N:HuAtRxohaXVfVdSj@geo.floppydata.com:10080", # Акк-02
    "http://pUxCZ9gtrBufs88g:hkSHIuFUaL4WWZHs@geo.floppydata.com:10080", # Акк-02    
    "http://UwPm0ZcPa726J10m:Ysda782LsxUeRhz5@geo-dc.floppydata.com:10080", # Акк-03
    "http://oxxAslsfIwkak8pw:JisG4cHqztjBB0QR@geo-dc.floppydata.com:10080", # Акк-03
    "http://IVO3tk5ud5s0z3e1:XOImNpwIas4AI6cg@geo-dc.floppydata.com:10080", # Акк-03
    "http://VwG6rJ4rT0YulilZ:pGrpXfgEQqAvwUlV@geo-dc.floppydata.com:10080", # Акк-03
    "http://1rziwtTwXXCh9c3t:XAsEW09cYxEScviI@geo-dc.floppydata.com:10080", # Акк-03
    "http://Er7875L6XbqONnIC:3gAHegKG9cTrjSZi@geo-dc.floppydata.com:10080", # Акк-04
    "http://PfYCg12DDhD0tPsq:lZCxxJDdMqap4OKK@geo-dc.floppydata.com:10080", # Акк-04
    "http://3UJkwK3DsPGasZhE:mud1S4nuBSjlQJCK@geo-dc.floppydata.com:10080", # Акк-04
    "http://25NEtzODzLbHDSIu:LRf38uczCpNsompn@geo-dc.floppydata.com:10080", # Акк-04
    "http://xG0Dxs04SOuRJsXa:Mxs1RFy5RCHxxDWa@geo-dc.floppydata.com:10080", # Акк-04
    "http://Mgr4hRA3Cf2k1afA:O9Jcj0XV5hCyXydT@geo-dc.floppydata.com:10080", # Акк-05
    "http://VXpdDcDKGmSQPOMu:NqOFNH0KcmPXOPsC@geo-dc.floppydata.com:10080", # Акк-05
    "http://QTwOYEZzUecgHmRE:gIX5Y6e1Xcuu5Qgw@geo-dc.floppydata.com:10080", # Акк-05
    "http://ygDN7u77w33aodA6:ni3kTkEn3sYDtUhI@geo-dc.floppydata.com:10080", # Акк-05
    "http://iDIrssL4Pcx50eIa:sXl5yXo7QcbRC7BF@geo-dc.floppydata.com:10080", # Акк-05
    "http://al75WsiBTW7eOBtV:GuCtS0htBjb9mdWZ@geo.floppydata.com:10080", # Акк-06
    "http://6yV51weTIYCk7dm7:4crhmvhE6BYrFwfY@geo.floppydata.com:10080", # Акк-06
    "http://aCyi9uFCEtTJQfaZ:AyuXiSJDiZpsXzlV@geo.floppydata.com:10080", # Акк-06
    "http://8xBbR9lNdweKh4HK:H0yXl3pSUr0AT2Ny@geo.floppydata.com:10080", # Акк-06
    "http://plw2kUPAcv88LdiG:ZFrRbscHqaTtyPuE@geo.floppydata.com:10080", # Акк-06
    "http://FqjMeshyBtyT0Fpt:1PbuYuAVNEphyywF@geo.floppydata.com:10080", # Акк-07
    "http://flPQya8ANVJwW7hS:yR7C5BjZxgJjyVrb@geo.floppydata.com:10080", # Акк-07
    "http://CjRXkZzcNmoD9Zf3:YBeWVOGfAXA6623N@geo.floppydata.com:10080", # Акк-07
    "http://gG2rWJlh9N7lLVMC:N319IEDA7OumQPH3@geo.floppydata.com:10080", # Акк-07
    "http://b7ngfLQ2IqVt8IH2:eMsD8ysnDknclLHd@geo.floppydata.com:10080", # Акк-07
    "http://SKRL1egG4QotA88H:SUFc3Sv5meu0JnMQ@geo.floppydata.com:10080", # Акк-08
    "http://xzlsv7hzl4oJvhAg:ItS2ssTiU84F6GtE@geo.floppydata.com:10080", # Акк-08
    "http://L2KWOKWllsacsNe2:A29IPDWjgqPyI0fx@geo.floppydata.com:10080", # Акк-08
    "http://umLIdBezA1SNMjyI:3dW88q09bvd4Ygzk@geo.floppydata.com:10080", # Акк-08
    "http://kHMwvhE6XQztywDL:rYrqRtBZ69gJbWyX@geo.floppydata.com:10080", # Акк-08
    "http://5FNhqwfsaqiubMDX:qXMmc6JKpSq5ITjD@geo.floppydata.com:10080", # Акк-09
    "http://JZJAp7uSfI3HEz3U:GWiPs0QrX2pzXsW0@geo.floppydata.com:10080", # Акк-09
    "http://v4dujwygiBUiBcP8:zrV2I91dmebvf4kO@geo.floppydata.com:10080", # Акк-09
    "http://YoDsE7k84ga1PpB6:y81EJjf3lF675KzX@geo.floppydata.com:10080", # Акк-09
    "http://bYg1z6a3UauKHuTG:DLdkh3WPS5U0Z2BW@geo.floppydata.com:10080", # Акк-09
    "http://iXh8DNnz2je8i5NK:FXLwTUJoDpWFkwLw@geo.floppydata.com:10080", # Акк-10
    "http://rLWYULi0klJukkIw:S6nP8ebPYYvp1kWp@geo.floppydata.com:10080", # Акк-10
    "http://aLmBR5oSK4OVDK2n:HbhM98iMYhtOWxuN@geo.floppydata.com:10080", # Акк-10
    "http://KNWELIQheFPv3SNi:SgcOCfSMk9VHcF8F@geo.floppydata.com:10080", # Акк-10
    "http://sRaZCLYPdzSsNNRs:USgXswdCnJDbeeSN@geo.floppydata.com:10080"  # Акк-10
]

PROXIES_FREE = [
    "http://meuqisgd-rotate:sacw3z83rohz@p.webshare.io:80/",
    "http://fxjicgrp-rotate:8f0xm7zyz93m@p.webshare.io:80/",
    "http://jqgpxdcc-rotate:damrxfsdn4in@p.webshare.io:80/",
    "http://vfbjathr-rotate:ciimgkcdugq6@p.webshare.io:80/",
    "http://xookwczd-rotate:vvhvbm4f1luh@p.webshare.io:80/",
    "http://wphirntq-rotate:38ngyirnwbqk@p.webshare.io:80/",
    "http://hpakiybd-rotate:47rll7l9s756@p.webshare.io:80/",
    "http://utjwzmel-rotate:ya3a3zu4y5fy@p.webshare.io:80/",
    "http://jsoyabsz-rotate:hh0dy9jo3iev@p.webshare.io:80/",
    "http://edgcufpr-rotate:ajssd7b5i0k8@p.webshare.io:80/",
    "http://jqktjdtn-rotate:c4biefedfnrg@p.webshare.io:80/",
    "http://macoypfl-rotate:luo6y7axuqan@p.webshare.io:80/",
    "http://gcyesvjm-rotate:idku1auhnld2@p.webshare.io:80/",
    "http://wrihyuqq-rotate:amejt9f5m3v5@p.webshare.io:80/",
    "http://zxikssbx-rotate:3bo09re2v4rt@p.webshare.io:80/",
    "http://pnjfmzqx-rotate:jdlf4dzf7wn7@p.webshare.io:80/",
    "http://esbfptun-rotate:6gt0fw8x6lid@p.webshare.io:80/",
    "http://bmdywylt-rotate:lefh94hsdvrr@p.webshare.io:80/",
    "http://xrmxjmqb-rotate:kppuan4ysoa0@p.webshare.io:80/",
    "http://pdqqrfxq-rotate:8wa8adlcpkeb@p.webshare.io:80/",
    "http://zavsezcn-rotate:wz2putcheob6@p.webshare.io:80/",
    "http://sofzabcb-rotate:glv6w6nqlbvp@p.webshare.io:80/",
    "http://ivunngek-rotate:rasld5rov9rm@p.webshare.io:80/",
    "http://kemmbrvr-rotate:dehk60fsbof8@p.webshare.io:80/",
    "http://hpvyidpy-rotate:cnxux33pc82h@p.webshare.io:80/",
    "http://nkblpbca-rotate:gt3nuwdaewkr@p.webshare.io:80/",
    "http://xetmzjlv-rotate:e0tajq71ascs@p.webshare.io:80/",
    "http://uddyrkmp-rotate:um3zsc0dt4ib@p.webshare.io:80/",
    "http://qqtuhuyf-rotate:1xecakaxshf2@p.webshare.io:80/",
    "http://qnlnmyul-rotate:p72epv54r02k@p.webshare.io:80/",
    "http://txefhrmg-rotate:0atiay5uq6kh@p.webshare.io:80/",
    "http://nwnyyslr-rotate:mjuhgbm4eehg@p.webshare.io:80/",
    "http://ofpyckwz-rotate:31b9tncrxfsp@p.webshare.io:80/",
    "http://zxhdiscp-rotate:ru14eec4i8vd@p.webshare.io:80/",
    "http://kmftlgpk-rotate:lmzks4rhb2nz@p.webshare.io:80/",
    "http://yhwivdso-rotate:7lq7kfkabwf2@p.webshare.io:80/",
    "http://cyifpcyk-rotate:035bpezn0cl6@p.webshare.io:80/",
    "http://cvtrseuf-rotate:a6rmognfnkah@p.webshare.io:80/",
    "http://pnifrmmk-rotate:4a2fynovuhf7@p.webshare.io:80/",
    "http://vyzfbyew-rotate:ged0syp3efra@p.webshare.io:80/",
    "http://loxmvfsi-rotate:1o8a0qjk2cao@p.webshare.io:80/",
    "http://iucohrsb-rotate:7xpnbfplcdqv@p.webshare.io:80/",
    "http://ayegmhyl-rotate:yrg0u22b8fyp@p.webshare.io:80/",
    "http://zwshmyrf-rotate:bxb8c0enae8v@p.webshare.io:80/",
    "http://ebmtqwhz-rotate:la8iobq6e8ba@p.webshare.io:80/",
    "http://fpzrkbwx-rotate:rb4ww18ll5p6@p.webshare.io:80/",
    "http://opbqtgbu-rotate:gu9rxxci0br6@p.webshare.io:80/",
    "http://dfxsszyc-rotate:a39u82pgvu4u@p.webshare.io:80/",
    "http://ozigwwri-rotate:itei20ngpvgk@p.webshare.io:80/",
    "http://smqhzhgn-rotate:fuyrt9d8vysd@p.webshare.io:80/",
    "http://hivwoecz-rotate:otofekgqtnyo@p.webshare.io:80/",
    "http://kvwiidsf-rotate:r920hjc3oph9@p.webshare.io:80/",
    "http://uustvana-rotate:oxt876kgl571@p.webshare.io:80/",
    "http://zxuwcyzs-rotate:ug4vly6egs9p@p.webshare.io:80/",
    "http://sijilezi-rotate:5ppzlg38g7x1@p.webshare.io:80/",
    "http://kbefpadi-rotate:dnphzycs2tm1@p.webshare.io:80/",
    "http://pvzbafgl-rotate:rgwl2ivcrd5m@p.webshare.io:80/",
    "http://bmdcjznu-rotate:qb6hz7mr8mbk@p.webshare.io:80/",
    "http://qokpqzcz-rotate:p8heeou7fjmt@p.webshare.io:80/",
    "http://liaufqoq-rotate:k33bd83ozivd@p.webshare.io:80/",
    "http://yqxmyfsk-rotate:cuxdo7dzzyf3@p.webshare.io:80/",
    "http://avqbnawy-rotate:9qguri99h0hw@p.webshare.io:80/",
    "http://iyxmhunq-rotate:pu9siuad9otv@p.webshare.io:80/",
    "http://wuqanhpu-rotate:gjsj1vj7514a@p.webshare.io:80/",
    "http://qxstnkab-rotate:f5gv8gt2s2uq@p.webshare.io:80/",
    "http://wjmoflze-rotate:stnuynjw1da1@p.webshare.io:80/",
    "http://isyjloiv-rotate:73b92mfox3c2@p.webshare.io:80/",
    "http://grnywwnd-rotate:0wuuovi4stuk@p.webshare.io:80/",
    "http://vuusgbjw-rotate:xgakeibxi516@p.webshare.io:80/",
    "http://nzthgqgh-rotate:2ffa08u148og@p.webshare.io:80/",
    "http://lgeibgzh-rotate:avcoqti7svk5@p.webshare.io:80/"


    # Все 70 добавил
    # "http://proxy3:password@host:port/",
    # "http://proxy4:password@host:port/",
]

PROXIES_RESIDENTAL = [
    "http://BQrDDXuxtvT0xJQW:QGYClXqj5K6vwzF3@geo.floppydata.com:10080", # Акк-02
    "http://mCq0Pz5pBWYUexOY:9Un3lK1mvAqd3cfn@geo.floppydata.com:10080", # Акк-02
    "http://0RtfszRUV52xyLYR:X2lURTJoF5cIILpw@geo.floppydata.com:10080", # Акк-02
    "http://iupqkzIzJ84O9C4N:HuAtRxohaXVfVdSj@geo.floppydata.com:10080", # Акк-02
    "http://pUxCZ9gtrBufs88g:hkSHIuFUaL4WWZHs@geo.floppydata.com:10080", # Акк-02    
    "http://UwPm0ZcPa726J10m:Ysda782LsxUeRhz5@geo-dc.floppydata.com:10080", # Акк-03
    "http://oxxAslsfIwkak8pw:JisG4cHqztjBB0QR@geo-dc.floppydata.com:10080", # Акк-03
    "http://IVO3tk5ud5s0z3e1:XOImNpwIas4AI6cg@geo-dc.floppydata.com:10080", # Акк-03
    "http://VwG6rJ4rT0YulilZ:pGrpXfgEQqAvwUlV@geo-dc.floppydata.com:10080", # Акк-03
    "http://1rziwtTwXXCh9c3t:XAsEW09cYxEScviI@geo-dc.floppydata.com:10080", # Акк-03
    "http://Er7875L6XbqONnIC:3gAHegKG9cTrjSZi@geo-dc.floppydata.com:10080", # Акк-04
    "http://PfYCg12DDhD0tPsq:lZCxxJDdMqap4OKK@geo-dc.floppydata.com:10080", # Акк-04
    "http://3UJkwK3DsPGasZhE:mud1S4nuBSjlQJCK@geo-dc.floppydata.com:10080", # Акк-04
    "http://25NEtzODzLbHDSIu:LRf38uczCpNsompn@geo-dc.floppydata.com:10080", # Акк-04
    "http://xG0Dxs04SOuRJsXa:Mxs1RFy5RCHxxDWa@geo-dc.floppydata.com:10080", # Акк-04
    "http://Mgr4hRA3Cf2k1afA:O9Jcj0XV5hCyXydT@geo-dc.floppydata.com:10080", # Акк-05
    "http://VXpdDcDKGmSQPOMu:NqOFNH0KcmPXOPsC@geo-dc.floppydata.com:10080", # Акк-05
    "http://QTwOYEZzUecgHmRE:gIX5Y6e1Xcuu5Qgw@geo-dc.floppydata.com:10080", # Акк-05
    "http://ygDN7u77w33aodA6:ni3kTkEn3sYDtUhI@geo-dc.floppydata.com:10080", # Акк-05
    "http://iDIrssL4Pcx50eIa:sXl5yXo7QcbRC7BF@geo-dc.floppydata.com:10080", # Акк-05
    "http://al75WsiBTW7eOBtV:GuCtS0htBjb9mdWZ@geo.floppydata.com:10080", # Акк-06
    "http://6yV51weTIYCk7dm7:4crhmvhE6BYrFwfY@geo.floppydata.com:10080", # Акк-06
    "http://aCyi9uFCEtTJQfaZ:AyuXiSJDiZpsXzlV@geo.floppydata.com:10080", # Акк-06
    "http://8xBbR9lNdweKh4HK:H0yXl3pSUr0AT2Ny@geo.floppydata.com:10080", # Акк-06
    "http://plw2kUPAcv88LdiG:ZFrRbscHqaTtyPuE@geo.floppydata.com:10080", # Акк-06
    "http://FqjMeshyBtyT0Fpt:1PbuYuAVNEphyywF@geo.floppydata.com:10080", # Акк-07
    "http://flPQya8ANVJwW7hS:yR7C5BjZxgJjyVrb@geo.floppydata.com:10080", # Акк-07
    "http://CjRXkZzcNmoD9Zf3:YBeWVOGfAXA6623N@geo.floppydata.com:10080", # Акк-07
    "http://gG2rWJlh9N7lLVMC:N319IEDA7OumQPH3@geo.floppydata.com:10080", # Акк-07
    "http://b7ngfLQ2IqVt8IH2:eMsD8ysnDknclLHd@geo.floppydata.com:10080", # Акк-07
    "http://SKRL1egG4QotA88H:SUFc3Sv5meu0JnMQ@geo.floppydata.com:10080", # Акк-08
    "http://xzlsv7hzl4oJvhAg:ItS2ssTiU84F6GtE@geo.floppydata.com:10080", # Акк-08
    "http://L2KWOKWllsacsNe2:A29IPDWjgqPyI0fx@geo.floppydata.com:10080", # Акк-08
    "http://umLIdBezA1SNMjyI:3dW88q09bvd4Ygzk@geo.floppydata.com:10080", # Акк-08
    "http://kHMwvhE6XQztywDL:rYrqRtBZ69gJbWyX@geo.floppydata.com:10080", # Акк-08
    "http://5FNhqwfsaqiubMDX:qXMmc6JKpSq5ITjD@geo.floppydata.com:10080", # Акк-09
    "http://JZJAp7uSfI3HEz3U:GWiPs0QrX2pzXsW0@geo.floppydata.com:10080", # Акк-09
    "http://v4dujwygiBUiBcP8:zrV2I91dmebvf4kO@geo.floppydata.com:10080", # Акк-09
    "http://YoDsE7k84ga1PpB6:y81EJjf3lF675KzX@geo.floppydata.com:10080", # Акк-09
    "http://bYg1z6a3UauKHuTG:DLdkh3WPS5U0Z2BW@geo.floppydata.com:10080", # Акк-09
    "http://iXh8DNnz2je8i5NK:FXLwTUJoDpWFkwLw@geo.floppydata.com:10080", # Акк-10
    "http://rLWYULi0klJukkIw:S6nP8ebPYYvp1kWp@geo.floppydata.com:10080", # Акк-10
    "http://aLmBR5oSK4OVDK2n:HbhM98iMYhtOWxuN@geo.floppydata.com:10080", # Акк-10
    "http://KNWELIQheFPv3SNi:SgcOCfSMk9VHcF8F@geo.floppydata.com:10080", # Акк-10
    "http://sRaZCLYPdzSsNNRs:USgXswdCnJDbeeSN@geo.floppydata.com:10080"  # Акк-10
]