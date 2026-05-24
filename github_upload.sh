#!/usr/bin/env bash
# Универсальный скрипт загрузки изменений на GitHub.
# Создаёт отдельный коммит по каждому изменённому файлу с коротким описанием
# (до 500 символов), сгенерированным из git diff.
# Аккаунт и репозиторий берутся из .git/config (origin).

set -euo pipefail

MAX_MSG_LEN=500

# --- проверки окружения ---------------------------------------------------
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

# --- синхронизация с origin -----------------------------------------------
echo "Получаем изменения с origin..."
git fetch origin --prune

# Если на origin есть новые коммиты — подтягиваем их через rebase,
# чтобы не было конфликтов при push.
if git rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1; then
    BEHIND="$(git rev-list --count "HEAD..origin/$BRANCH")"
    if [[ "$BEHIND" -gt 0 ]]; then
        echo "Локальная ветка отстаёт на $BEHIND коммит(ов). Выполняю rebase..."
        # Если есть незакоммиченные изменения — временно их прячем
        STASHED=0
        if ! git diff --quiet || ! git diff --cached --quiet \
                || [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
            git stash push -u -m "github_upload pre-rebase $(date +%s)" >/dev/null
            STASHED=1
        fi
        git pull --rebase origin "$BRANCH"
        if [[ "$STASHED" -eq 1 ]]; then
            git stash pop || {
                echo "Конфликт при восстановлении stash. Разрешите вручную." >&2
                exit 1
            }
        fi
    fi
fi

# --- сбор списка изменённых файлов ----------------------------------------
# Формат строк porcelain: "XY path" или для переименований "XY old -> new".
mapfile -t RAW_STATUS < <(git status --porcelain)

if [[ "${#RAW_STATUS[@]}" -eq 0 ]]; then
    echo "Нет локальных изменений — нечего загружать."
    exit 0
fi

# --- генерация короткого сообщения коммита --------------------------------
generate_message() {
    local code="$1"   # 2 символа из porcelain (XY)
    local path="$2"

    local X="${code:0:1}"
    local Y="${code:1:1}"

    # Удалённый файл
    if [[ "$X" == "D" || "$Y" == "D" ]]; then
        printf "Удалён файл %s" "$path"
        return
    fi

    # Переименование
    if [[ "$X" == "R" || "$Y" == "R" ]]; then
        printf "Переименован файл %s" "$path"
        return
    fi

    # Новый (untracked или добавленный) файл
    if [[ "$code" == "??" || "$X" == "A" ]]; then
        local lines=0
        if [[ -f "$path" ]]; then
            lines="$(wc -l <"$path" 2>/dev/null || echo 0)"
        fi
        printf "Добавлен новый файл %s (%s строк)" "$path" "$lines"
        return
    fi

    # Модифицированный файл — анализируем diff
    local diff_text
    diff_text="$(git diff --no-color -- "$path" 2>/dev/null)"
    if [[ -z "$diff_text" ]]; then
        diff_text="$(git diff --no-color --cached -- "$path" 2>/dev/null)"
    fi

    local added removed
    added="$(grep -cE '^\+[^+]' <<<"$diff_text" || true)"
    removed="$(grep -cE '^-[^-]' <<<"$diff_text" || true)"

    # Контекст функций/секций из заголовков @@ ... @@
    local hunks
    hunks="$(grep -E '^@@' <<<"$diff_text" \
        | sed -E 's/^@@[^@]*@@[[:space:]]*//' \
        | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' \
        | grep -v '^$' \
        | awk '!seen[$0]++' \
        | head -3 \
        | paste -sd '; ' - || true)"

    # Примеры реально изменённых строк (без +++/--- заголовков)
    local added_sample removed_sample
    added_sample="$(grep -E '^\+[^+]' <<<"$diff_text" \
        | sed -E 's/^\+//' \
        | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' \
        | grep -v '^$' \
        | head -3 \
        | paste -sd ' | ' - || true)"
    removed_sample="$(grep -E '^-[^-]' <<<"$diff_text" \
        | sed -E 's/^-//' \
        | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' \
        | grep -v '^$' \
        | head -2 \
        | paste -sd ' | ' - || true)"

    local msg="Изменён ${path}: +${added}/-${removed} строк"
    [[ -n "$hunks" ]]          && msg="${msg}. Контекст: ${hunks}"
    [[ -n "$added_sample" ]]   && msg="${msg}. Добавлено: ${added_sample}"
    [[ -n "$removed_sample" ]] && msg="${msg}. Удалено: ${removed_sample}"

    printf "%s" "$msg"
}

# --- коммиты по одному файлу ----------------------------------------------
COMMITS_MADE=0

for line in "${RAW_STATUS[@]}"; do
    code="${line:0:2}"
    rest="${line:3}"

    # Случай переименования: "old -> new" — берём новое имя
    if [[ "$rest" == *' -> '* ]]; then
        path="${rest##* -> }"
    else
        path="$rest"
    fi

    # Снимаем возможные кавычки вокруг пути
    path="${path%\"}"
    path="${path#\"}"

    msg="$(generate_message "$code" "$path")"

    # Обрезаем до MAX_MSG_LEN символов (по байтам, для bash достаточно)
    if (( ${#msg} > MAX_MSG_LEN )); then
        msg="${msg:0:MAX_MSG_LEN}"
    fi

    echo "----"
    echo "Файл:    $path"
    echo "Коммит:  $msg"

    # Готовим индекс ТОЛЬКО под этот файл:
    # сначала убираем всё лишнее, потом добавляем нужный путь.
    git reset -q
    git add -A -- "$path"

    # Если после add нечего коммитить (например, файл исчез) — пропускаем
    if git diff --cached --quiet; then
        echo "Нечего коммитить для $path, пропуск."
        continue
    fi

    git commit -q -m "$msg"
    COMMITS_MADE=$((COMMITS_MADE + 1))
done

if (( COMMITS_MADE == 0 )); then
    echo "Коммиты не создавались, push пропущен."
    exit 0
fi

echo "----"
echo "Создано коммитов: $COMMITS_MADE. Push в origin/$BRANCH..."
git push origin "$BRANCH"
echo "Готово."
