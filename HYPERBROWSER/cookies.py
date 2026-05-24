import os
import config

def get_storage_state(profile_num: str) -> str:
    """
    Формирует и возвращает путь к файлу storage_state (auth) для указанного профиля.
    Профиль берется из BAZA_PROFILE (например, "01").
    Путь строится как: Profiles/{profile_num}/mindvideo-auth.json
    """
    # Очистка номера профиля от лишних пробелов
    profile_clean = str(profile_num).strip()
    
    # Формируем путь через функцию из конфига (она уже настроена на mindvideo-auth.json)
    auth_path = config.get_auth_path(profile_clean)
    
    if not os.path.exists(auth_path):
        raise FileNotFoundError(f"Файл авторизации не найден по пути: {auth_path}")
        
    return auth_path
