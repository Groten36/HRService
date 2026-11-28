#!/usr/bin/env bash
# Uruchamia aplikację jedną komendą: ./run.sh [adres:port]
# Tworzy venv, instaluje zależności, wczytuje .env, migruje bazę,
# tworzy domyślne dane, konta przykładowe i (w razie braku) superużytkownika.
set -euo pipefail
cd "$(dirname "$0")"

VENV=.venv
PY="$VENV/bin/python"

if [ ! -x "$PY" ]; then
    echo "==> Tworzę środowisko wirtualne ($VENV)"
    python3 -m venv "$VENV"
fi

# Instaluj zależności tylko, gdy requirements.txt się zmienił.
STAMP="$VENV/.requirements.sha"
REQ_HASH=$(sha256sum requirements.txt | cut -d' ' -f1)
if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP")" != "$REQ_HASH" ]; then
    echo "==> Instaluję zależności"
    "$PY" -m pip install --quiet --upgrade pip
    "$PY" -m pip install --quiet -r requirements.txt
    echo "$REQ_HASH" > "$STAMP"
fi

if [ -f .env ]; then
    echo "==> Wczytuję .env"
    set -a; source .env; set +a
fi

echo "==> Migracje bazy danych"
"$PY" manage.py migrate --noinput

echo "==> Domyślne kategorie dokumentów"
"$PY" manage.py setup_documents

if [ "${DJANGO_DEMO_USERS:-True}" = "True" ] && [ "${DJANGO_DEBUG:-True}" = "True" ]; then
    echo "==> Konta przykładowe (patrz README.md)"
    "$PY" manage.py setup_demo_users
fi

HAS_SUPERUSER=$("$PY" manage.py shell -v 0 -c \
    "from django.contrib.auth import get_user_model; print(get_user_model().objects.filter(is_superuser=True).exists())")
if [ "$HAS_SUPERUSER" != "True" ]; then
    if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
        echo "==> Tworzę superużytkownika $DJANGO_SUPERUSER_USERNAME"
        "$PY" manage.py createsuperuser --noinput --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"
    elif [ -t 0 ]; then
        echo "==> Brak superużytkownika — utwórz go teraz"
        "$PY" manage.py createsuperuser
    else
        echo "!! Brak superużytkownika. Ustaw DJANGO_SUPERUSER_USERNAME/PASSWORD lub uruchom interaktywnie."
    fi
fi

echo "==> Start serwera: http://${1:-127.0.0.1:8000}/"
exec "$PY" manage.py runserver "${1:-127.0.0.1:8000}"
