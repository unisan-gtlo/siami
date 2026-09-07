#!/bin/sh
set -e

wait_for_db() {
    echo "Menunggu database di ${DB_HOST:-db}:${DB_PORT:-5432}..."
    python - <<'PY'
import os, socket, time

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "5432"))
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit("Database tidak tersedia setelah 120 detik")
PY
    echo "Database siap."
}

case "$1" in
    web)
        wait_for_db
        python manage.py migrate --noinput
        python manage.py collectstatic --noinput
        exec gunicorn ami_project.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers "${GUNICORN_WORKERS:-3}" \
            --timeout "${GUNICORN_TIMEOUT:-60}" \
            --access-logfile - \
            --error-logfile -
        ;;
    *)
        exec "$@"
        ;;
esac
