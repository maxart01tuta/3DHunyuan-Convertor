#!/usr/bin/env bash
# github_download.sh — скачивает последние изменения с GitHub.
# Универсальный: использует настройки из .git текущего репозитория.
# Просто скопируй файл в нужный репозиторий и запусти: ./github_download.sh

set -euo pipefail

# Проверяем, что мы внутри git-репозитория
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Ошибка: текущая папка не является git-репозиторием."
    exit 1
fi

cd "$(git rev-parse --show-toplevel)"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
REMOTE="$(git config --get "branch.${BRANCH}.remote" || echo origin)"

echo "Скачиваю изменения из ${REMOTE}/${BRANCH}..."

# Если есть незакоммиченные изменения — предупреждаем и делаем stash
STASHED=0
if ! git diff-index --quiet HEAD -- || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo "Обнаружены локальные изменения — временно прячу их в stash..."
    git stash push -u -m "github_download autostash $(date +%s)" >/dev/null
    STASHED=1
fi

# Тянем изменения с rebase, чтоб не плодить merge-коммитов
git pull --rebase "${REMOTE}" "${BRANCH}"

# Возвращаем спрятанные изменения обратно
if [ "${STASHED}" -eq 1 ]; then
    echo "Возвращаю локальные изменения из stash..."
    if ! git stash pop; then
        echo "Внимание: возник конфликт при возврате изменений. Разрулите вручную (git status)."
        exit 1
    fi
fi

echo "Готово. Локальная ветка ${BRANCH} обновлена."
