# Конфигурация системы автоматизации Convertor GLB

import os

# Таймауты
MAX_TIME = 600  # секунд, максимальное ожидание элементов
WAIT_TIME = 7   # секунд, краткая пауза между действиями


# Настройки переподключения
MAX_STEEL_RETRIES = 10  # максимум попыток подключения
STEEL_RETRY_DELAY = 5.0  # задержка между попытками в секундах


# URL сайта
site = "https://fabconvert.com/convert/3d-model"


# Селекторы для FabConvertor
input_upload = "//input[@id='gb']" # Upload GLB на сайт. старое: //input[@id='fb']
input_upload_css = "input#gb"  # CSS селектор для CDP DOM.querySelector | Старое: "input#fb"
knopka_vibor_type = "//span[@class='tc']" # Pop-up выпадающий список выбора Типа файла
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
# Steel.dev НАСТРОЙКИ
# ============================================

# API ключи Steel.dev (каждый раз для новой сессии выбирается рандомно)
API_STEEL_LIST = [
    "ste-3TgYu4PCPt3d9I4HwacV1zhDcMG8qnV344sNG6fDsHOMhXqJI5jPHwo80Ld0HTOPQ7ON2ebrX5B117ts2s8LBddpLIwGs9buBJV",  # Акк-1
    ]

API_STEEL_LIST_TEST = [
    "ste-3TgYu4PCPt3d9I4HwacV1zhDcMG8qnV344sNG6fDsHOMhXqJI5jPHwo80Ld0HTOPQ7ON2ebrX5B117ts2s8LBddpLIwGs9buBJV",  # Акк-1
    "ste-GfD9mhcwt4d3EQFyIoAkdmTQaI3m2B9vp6IvfVHrdc3e0th1Mq28Xm15qviQh8gxcJJXsBbjugBVFqakBfPE98VM3t7oIwiiAHE",  # Акк-2
    "ste-laL9yUSnj0HeACWTiITyaa445FhyLY72hSsBslxO25oRMT1GwVaFOarMGNYjJi319xXsD3h8t6ukFlZXH2AM5kSbaKxMIBDeRnb",  # Акк-3
    "ste-aw2UYibBcT9N9cm0picFI6LD2ZL9AoRrHQ4Nq4aEb5Fuhe0AAqf0LPgoXbn79hBqXciPV7G2MUv3sF0LHa9hPNANhTpPBnd2GVi",  # Акк-4
    "ste-SABmzjzD1Jx8BACer4XT4RVeQDAPMygdZQDGr7gPtH1mTuJqejGIm5vaDkGznQxe4toDg9W7mWjf0wq4tbcII6YnPR0Ccr4Z3Eq",  # Акк-5
    "ste-9qojVfWBSZR0xc4WJk3oNysSt3tUHPZaxdMxPvJQ7uv0yDIWaEHSvHB3enkPcQxORMxAkyXAaINE8QkXMsu0jOVF1Dh0VfAYJ4C",  # Акк-6
    "ste-7sH2zZgfmmbgCXt3CVivsen7I8mPRl00DeA59WTM1022AefgLpGnMj3c2kgsyAiw0KTv4VRbgT8Ny7KUByJxqBDJfIehY9mF8Y6",  # Акк-7
    "ste-Y7LkmyDrZTAJR0uGM1CpNahjG4VEGMHw3NSzRWobCYYxsQ1WFtNwhnKmcqfZpEf9E5zOPbsL482IkyGxJriyDL0pzWFwMPWdjN6",  # Акк-8
    "ste-CUCWq4r3cIi2rHB8IMASmIsVLmfYlVUVpb8PMffLLqkVPp1j2deMHOzP6xX6QrozFhVTKLUnt1I3k7X29iO6Hn6VPtesUSFMkCo",  # Акк-9
    "ste-M78kTMpbD7Ja2GTYnabVDwQlzSL7lCewH2mtxr3gmG1YBfO16TPO1zYC2ZaVCSWlts13ZUwDuTkjKylSDaA5CrgwtFNv38Z91FI",  # Акк-10
    "ste-Pt0fjPJxtFSi56DsCiQvHOoFQHj5i6t3LyzwwpuqsXClF8BfBtcEhlvT32m7TtJM0MjMiSmECQ5ElgiruCxUCAqejKepJSYx9yM",  # Акк-11
    "ste-xH096wqYBgxel1ujm0R1xkninrbaRAnbcqJd9qoSu5MeamQuctNjNGfGdluJYRH1WaS0d0aLw0JBRta9F8EdaNWw8fS1jt7tdSf",  # Акк-12
    "ste-TtsPEfwf7p5JYqShB4CnMnrIDlCodZnjW4o2oQPNjXRfyGFpYwI0vGY4hCT4JP2f5t2QDkoAAElfDalYbphWNx0aS2sp51iK9bx",  # Акк-13
    "ste-hiuyI7Qb2uz2FrjJETU40x4ZG1MuedKpZvIocEIVrWsdjhbWyjpJboXMz9eB21VLN3h0OdAnaxXdkC93WsuM4tM5lEAASxVUamc",  # Акк-14
    "ste-JdIF2XR7bFXNQYvngoMd4jHIuoI4C2bIMZ5vOxkPV8OLZsT8QpMRiaqHxt5iImIWq9TgwQczyAsb8UQwDOnGlmu3gd7navNvbEi",  # Акк-15
    "ste-ReZ5QYFet7r9FDvrlcBnT7i4EQ5vIPVRO3bfPEh6NGm64xvKJ0AMPEgbThjhL7wV1YVxFnOAkKSub75eNYoct5NOKInJm2epzL5",  # Акк-16
    "ste-13hTKa4otCy05oilpimXDWwrXNO4rkBe1ybqzBj5w9FTq8e50nZXnKgOw2ScoAAIye1yh6TL0536WhABrdjYTahM24aBXXpzbLz",  # Акк-17
    "ste-cCLvopBSOZQVx6JjUpTPyaTCxiKGzXhu51Ho0T3P5AhJHjphEBBi092RHipGw9Z1sTTOSXyb8w1sa6eZDZ35QKcwZJoeeMFiQ7p",  # Акк-18
    "ste-RLprnLAv7qICleDRupvBXliwvtTiupKtHW3ILzYTrpr3YcmPdW3wK79AzjUpt7SVs3g2ym5892wwu34CRijC4atSE4Zp1yN2Ve7",  # Акк-19
    "ste-VARcMeEiubU84fFyGnRuBASppqQDeNwLXqsFeZOOrvJDIOqqRcQIuVTAFBPw57lAMZCMdkqNpsoO7EhApIhqSJk5XzT0RiWrFbP",  # Акк-20
    "ste-kfWbH2yQ3UCcqAo9Zf48UkE5nINSWdU7yMIjbntOrMcU28mZU2WCyhZcKh5fXoME63lqTz0aAwi4frSD7QbTAygEKMd5VNm6bmd",  # Акк-21
    "ste-XCEDro5SVocquQw2b4AZ7qWnZcbizgXdU6KMqL9gLxHcPGkEONTwiC0UKYBhlzWdwjD3OQgNFyvkEv9hFzw8y8OITeVyTKmKBVW",  # Акк-22
    "ste-DQYFtcXry3vUiF5rY7ptaoGfOBlCQuKl33mWwUcgBkO0CjZHxjHsQFW6Yud8CxcNnbFZDoWBLFXTzCh0JLfBb0AOmlAMyBhOgv5",  # Акк-23
    "ste-qWd1ZeTqy4hBQo9LfAbxpQ4sqaBbcfvM6nCliB1qjABU4myUQ2js1mlhGneT9quDFFptc4ZE28Vcca81yEZClApC8vzaV2ovqyi",  # Акк-24
    "ste-Qaw9hRs08EC2cWFHXecs3DWRjly47Z2lU8oh5tLqPRk9HTv3awYZNCZ7FqGZFUBqyXnaw4rCd3QggnUpKyq7tkaIEiYMNBcg417",  # Акк-25
    "ste-NPft9IbF5jarLoREsS2ZUoPWilFnIYFXgGzlA3pNl6exO77AzLOgQTm9x5X9vydv3HSwsdCdVOA8L1T8uTdakh4rjJIM89Bg1yw",  # Акк-26
    "ste-Hrl75ag5vKlBldukKG0PM9j9g0aahZkNIEuymLSqhh2gknEHtuKOPi9A8SMuvo8dZnpxRZ5wTy2H6kSRaeDyLTEGULazmr1CpTX",  # Акк-27
    "ste-rG8JJNX0zwuUSA4oTDm6BCapyBgfX4UF0qFO2GAm8NtJLlbIUniz0O9H6xe9Zy1Mdc0StPMmBheSdj5Ad9a1q63VYVcWIIklHiQ",  # Акк-28
    "ste-YqX6JDv3TgxoHsh5EYjH916aGMSSauOd2vn0ZfKqdD7kZhcoV36WLG6WgVNrhGHdmacaD0YXpZg4QrCM2G66IQhKZgI3ZUlWI5O",  # Акк-29
    "ste-0aO01WOGo3db25LvsyX9KmLkm39ltWvsoxjAgceUN8mjSLXUY3n34phPaqiZT3XcgvWzCD1lsSXGtToGdU583sSY2r5k6d7NRh2"   # Акк-30   
]

