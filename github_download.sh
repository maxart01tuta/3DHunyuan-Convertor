#!/usr/bin/env bash
# Универсальный скрипт получения последних изменений с GitHub.
# Аккаунт и репозиторий берутся из .git/config (origin).
# Локальные незакоммиченные изменения временно прячутся через git stash,
# чтобы избежать конфликтов, и возвращаются обратно после pull.

set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Ошибка: текущая папка не git-репозиторий" >&2
    exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
    echo "Ошибка: не найден remote 'origin' в .git/config" >&2
    exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "Ветка: $BRANCH"
echo "Origin: $(git remote get-url origin)"

echo "Получаем актуальные данные с origin..."
git fetch --all --prune

# Прячем локальные изменения, если они есть
STASHED=0
if ! git diff --quiet \
        || ! git diff --cached --quiet \
        || [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
    echo "Обнаружены локальные изменения — временно сохраняю их в stash..."
    git stash push -u -m "github_download auto-stash $(date +%s)" >/dev/null
    STASHED=1
fi

echo "Тяну изменения (rebase) из origin/$BRANCH..."
if ! git pull --rebase origin "$BRANCH"; then
    echo "Ошибка при rebase. Разрешите конфликты вручную." >&2
    if [[ "$STASHED" -eq 1 ]]; then
        echo "Ваши локальные изменения находятся в stash (см. 'git stash list')." >&2
    fi
    exit 1
fi

if [[ "$STASHED" -eq 1 ]]; then
    echo "Восстанавливаю локальные изменения из stash..."
    if ! git stash pop; then
        echo "Конфликт при восстановлении stash. Разрешите вручную." >&2
        echo "Изменения остались в 'git stash list'." >&2
        exit 1
    fi
fi

echo "Готово. Локальная ветка $BRANCH синхронизирована с origin."
