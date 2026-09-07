#!/bin/bash
# Backup harian database SIAMI (Postgres di container docker-compose).
# Pasang lewat crontab, contoh jam 02:00 setiap hari:
#   0 2 * * * /home/amiruddin/siami/deploy/backup.sh >> /home/amiruddin/siami-backup/backup.log 2>&1
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$HOME/siami-backup"
RETENTION_DAYS=14
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_DIR"

cd "$PROJECT_DIR"
DB_USER="$(grep -m1 '^DB_USER=' .env | cut -d= -f2-)"
DB_NAME="$(grep -m1 '^DB_NAME=' .env | cut -d= -f2-)"

docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" \
    | gzip > "$BACKUP_DIR/siami-$TIMESTAMP.sql.gz"

echo "[$TIMESTAMP] Backup selesai: siami-$TIMESTAMP.sql.gz"

# Buang backup yang lebih tua dari RETENTION_DAYS
find "$BACKUP_DIR" -name 'siami-*.sql.gz' -mtime "+$RETENTION_DAYS" -delete
