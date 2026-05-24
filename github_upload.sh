#!/usr/bin/env bash
# github_upload.sh — закачивает локальные изменения на GitHub.
# Для каждого изменённого файла создаёт отдельный короткий коммит (<= 500 символов),
# в котором описывает: какие функции/классы тронуты, что добавлено и что удалено.
# Универсальный: использует репозиторий из .git текущей папки.
#
# Использование: ./github_upload.sh

set -euo pipefail

# --- Проверки окружения ----------------------------------------------------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Ошибка: текущая папка не является git-репозиторием."
    exit 1
fi

cd "$(git rev-parse --show-toplevel)"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
REMOTE="$(git config --get "branch.${BRANCH}.remote" || echo origin)"

# Сначала подтянем удалённые изменения, чтобы избежать non-fast-forward
echo "Получаю последнюю информацию о ${REMOTE}/${BRANCH}..."
git fetch "${REMOTE}" "${BRANCH}" >/dev/null 2>&1 || true

# --- Хелпер: сгенерировать короткое сообщение коммита для одного файла -----
# Аргументы: $1 = файл (относительный путь), $2 = двухсимвольный статус git
generate_message() {
    local file="$1"
    local status="$2"
    local short_status="${status// /}"
    local msg=""
    local diff plus minus funcs added_defs removed_defs lines

    case "${short_status}" in
        "??"|"A"|"AM"|"MA")
            if [ -f "${file}" ]; then
                lines=$(wc -l < "${file}" 2>/dev/null | tr -d ' ' || echo 0)
                msg="новый файл (${lines} строк)"
            else
                msg="новый файл"
            fi
            ;;
        "D"|"AD")
            msg="файл удалён"
            ;;
        "R"|"RM")
            msg="файл переименован"
            ;;
        *)
            # Изменённый файл — анализируем diff.
            # Берём diff с рабочей копией относительно HEAD (включает и stage, и working).
            diff=$(git diff HEAD -- "${file}" 2>/dev/null || true)
            if [ -z "${diff}" ]; then
                diff=$(git diff -- "${file}" 2>/dev/null || true)
            fi

            plus=$(printf '%s\n' "${diff}" | grep -c '^+[^+]' || true)
            minus=$(printf '%s\n' "${diff}" | grep -c '^-[^-]' || true)
            plus=${plus:-0}
            minus=${minus:-0}

            # Контекст функций из заголовков ханков:  "@@ ... @@ def foo():"
            funcs=$(printf '%s\n' "${diff}" \
                | grep '^@@' \
                | sed -E 's/^@@[^@]*@@[[:space:]]*//' \
                | sed -E 's/[ \t]*[({:=].*$//' \
                | sed -E 's/^(def|class|function|fn|func|async def|public|private|static)[[:space:]]+//' \
                | awk 'NF' \
                | sort -u \
                | head -5 \
                | paste -sd ',' - \
                | sed 's/,/, /g')

            # Новые определения функций/классов в добавленных строках
            added_defs=$(printf '%s\n' "${diff}" \
                | grep -E '^\+[[:space:]]*(def |class |async def |function |fn |func |public |private |static )' \
                | sed -E 's/^\+[[:space:]]*//' \
                | sed -E 's/^(async def|def|class|function|fn|func|public|private|static)[[:space:]]+//' \
                | sed -E 's/[ \t]*[({=:].*$//' \
                | awk 'NF' \
                | sort -u \
                | head -5 \
                | paste -sd ',' - \
                | sed 's/,/, /g')

            # Удалённые определения
            removed_defs=$(printf '%s\n' "${diff}" \
                | grep -E '^-[[:space:]]*(def |class |async def |function |fn |func )' \
                | sed -E 's/^-[[:space:]]*//' \
                | sed -E 's/^(async def|def|class|function|fn|func)[[:space:]]+//' \
                | sed -E 's/[ \t]*[({=:].*$//' \
                | awk 'NF' \
                | sort -u \
                | head -5 \
                | paste -sd ',' - \
                | sed 's/,/, /g')

            msg="изменения (+${plus}/-${minus})"
            [ -n "${funcs}" ]        && msg="${msg}; затронуты: ${funcs}"
            [ -n "${added_defs}" ]   && msg="${msg}; добавлено: ${added_defs}"
            [ -n "${removed_defs}" ] && msg="${msg}; удалено: ${removed_defs}"
            ;;
    esac

    printf '%s' "${msg}"
}

# --- Хелпер: обрезать строку до N символов (с учётом utf-8) ----------------
truncate_msg() {
    local s="$1"
    local max="$2"
    # awk считает байты, поэтому используем python если есть, иначе cut по символам через perl/awk
    if [ "$(printf '%s' "${s}" | wc -m)" -le "${max}" ]; then
        printf '%s' "${s}"
        return
    fi
    # Обрезаем по символам, добавляем …
    local cut
    cut=$((max - 1))
    printf '%s' "${s}" | awk -v n="${cut}" '{ printf "%s", substr($0, 1, n) }'
    printf '…'
}

# --- Собираем список изменений ---------------------------------------------
# Используем -z, чтобы корректно обработать имена с пробелами/спецсимволами.
mapfile -d '' -t entries < <(git status --porcelain=v1 -z)

if [ "${#entries[@]}" -eq 0 ]; then
    echo "Нет изменений для отправки."
    exit 0
fi

echo "Найдено записей: ${#entries[@]}"

i=0
commits_made=0
while [ "${i}" -lt "${#entries[@]}" ]; do
    entry="${entries[$i]}"
    i=$((i + 1))
    # Формат записи (без -z): "XY filename".  С -z: "XY filename" без кавычек.
    status="${entry:0:2}"
    file="${entry:3}"

    # Для R/C (rename/copy) следующий элемент — это старое имя.
    first_char="${status:0:1}"
    if [ "${first_char}" = "R" ] || [ "${first_char}" = "C" ]; then
        # Пропустим старое имя из следующей записи.
        old_name="${entries[$i]:-}"
        i=$((i + 1))
        # Файл, который нужно закоммитить — новое имя (file).
    fi

    if [ -z "${file}" ]; then
        continue
    fi

    msg_body=$(generate_message "${file}" "${status}")
    full_msg="${file}: ${msg_body}"
    full_msg=$(truncate_msg "${full_msg}" 500)

    echo "----"
    echo "Файл: ${file}"
    echo "Коммит: ${full_msg}"

    # Стейджим именно этот файл (-A учитывает удаления и переименования).
    if [ "${first_char}" = "R" ] && [ -n "${old_name:-}" ]; then
        git add -A -- "${old_name}" "${file}"
    else
        git add -A -- "${file}"
    fi

    # Если после add нечего коммитить (например, файл уже идентичен) — пропустим.
    if git diff --cached --quiet -- "${file}" 2>/dev/null; then
        # Возможно — это переименование без модификации, тогда коммит всё равно нужен.
        if [ "${first_char}" != "R" ]; then
            echo "  (нет staged-изменений, пропускаю)"
            continue
        fi
    fi

    git commit -m "${full_msg}" >/dev/null
    commits_made=$((commits_made + 1))
done

if [ "${commits_made}" -eq 0 ]; then
    echo "Коммитов не создано."
    exit 0
fi

echo "Создано коммитов: ${commits_made}. Отправляю на ${REMOTE}/${BRANCH}..."
git push "${REMOTE}" "${BRANCH}"
echo "Готово."
