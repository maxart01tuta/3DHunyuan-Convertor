
# Инициализация
cd D:\MAX\PYTHON\VIDEO\MindVideo-Cloud
git init

# Добавить файлы
git add .

# Коммит
git commit -m "Initial commit"

# Remote через HTTPS
git remote add origin https://github.com/maxart01tuta/mindvideo-cloud.git

# Пуш
git branch -M main
git push -u origin main




# ЧЕРЕЗ SSH НЕ НУЖНО, НУ ПУСТЬ БУДЕТ!!



Понял, вот пошаговая инструкция:

## 1. Настройка SSH-ключа для аккаунта maxart01tuta

Поскольку у тебя несколько аккаунтов GitHub, нужно настроить отдельный SSH-ключ:

```powershell
# Генерация нового ключа для этого аккаунта
# Сначала создать папку
mkdir D:\MAX\PYTHON\VIDEO\MindVideo-Cloud\.ssh

# Потом генерация ключа
ssh-keygen -t ed25519 -C "maxart01tuta@github" -f D:\MAX\PYTHON\VIDEO\MindVideo-Cloud\.ssh\id_ed25519_maxart01tuta```

## 2. Добавить ключ в ssh-agent

```powershell
# Запустить ssh-agent
# Запустить от имени администратора (открыть PowerShell как Admin)
Get-Service ssh-agent | Set-Service -StartupType Automatic
Или: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force;
Start-Service ssh-agent



# Добавить ключ
ssh-add $HOME\.ssh\id_ed25519_maxart01tuta
```

## 3. Настроить SSH config для нескольких аккаунтов

Создать/отредактировать файл `~/.ssh/config`, добавить:

```
Host github-maxart01tuta
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_maxart01tuta
    IdentitiesOnly yes
```

## 4. Добавить публичный ключ на GitHub

```powershell
# Вывести публичный ключ
cat ~/.ssh/id_ed25519_maxart01tuta.pub
```

Скопировать вывод → зайти на GitHub в аккаунт **maxart01tuta** → **Settings → SSH and GPG keys → New SSH key** → вставить.

## 5. Инициализация и пуш проекта

```powershell
# Перейти в папку проекта
cd D:\MAX\PYTHON\VIDEO\MindVideo-Cloud

# Инициализировать git (если ещё не инициализирован)
git init

# Добавить все файлы
git add .

# Первый коммит
git commit -m "Initial commit"

# Добавить remote (обрати внимание на Host из ssh config)
git remote add origin git@github-maxart01tuta:maxart01tuta/mindvideo-cloud.git

# Запушить
git branch -M main
git push -u origin main
```

**Ключевой момент** — в `git remote add origin` используется `github-maxart01tuta` (алиас из SSH config), а не просто `github.com`. Это гарантирует, что будет использован нужный SSH-ключ для нужного аккаунта.

Если хочешь, могу создать `.gitignore` перед пушем, чтобы не заливать лишнее (например, `__pycache__`, `.env` и т.д.)?