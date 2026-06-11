#!/usr/bin/env bash
# ============================================================
# Database Backup Script for Spoken Social
# ============================================================
# Usage:
#   ./backup_db.sh              # Backup local docker postgres
#   ./backup_db.sh --prod       # Backup production database
#
# Backups are saved to ./backups/ as timestamped .sql.gz files.
# Backups older than 30 days are automatically cleaned up.
# ============================================================

set -euo pipefail

# ── Configuration ──
BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)/backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
KEEP_DAYS=30

# ── Load .env if present ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# ── Defaults from .env or fallback ──
DB_NAME="${POSTGRES_DB:-spoken_social}"
DB_USER="${POSTGRES_USER:-spoken_user}"
DB_PASSWORD="${POSTGRES_PASSWORD:-}"

# ── Parse arguments ──
MODE="local"
if [ "${1:-}" = "--prod" ]; then
    MODE="prod"
fi

# ── Create backup directory ──
mkdir -p "$BACKUP_DIR"

echo "🗄️  Spoken Social Database Backup"
echo "   Mode:      $MODE"
echo "   Database:  $DB_NAME"
echo "   Timestamp: $TIMESTAMP"
echo ""

if [ "$MODE" = "local" ]; then
    # ── Local: dump via docker exec ──
    BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_local_${TIMESTAMP}.sql.gz"

    # Check if postgres container is running
    if ! docker compose ps postgres 2>/dev/null | grep -q "Up"; then
        echo "❌ Error: Postgres container is not running."
        echo "   Start it with: docker compose up -d postgres"
        exit 1
    fi

    echo "📦 Dumping local database via docker..."
    docker compose exec -T postgres pg_dump \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-privileges \
        --format=plain \
        | gzip > "$BACKUP_FILE"

elif [ "$MODE" = "prod" ]; then
    # ── Production: dump via DATABASE_URL or explicit host ──
    BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_prod_${TIMESTAMP}.sql.gz"

    # Production connection details (set these env vars or edit here)
    PROD_HOST="${PROD_DB_HOST:-}"
    PROD_PORT="${PROD_DB_PORT:-5432}"
    PROD_USER="${PROD_DB_USER:-$DB_USER}"
    PROD_PASSWORD="${PROD_DB_PASSWORD:-$DB_PASSWORD}"
    PROD_DB="${PROD_DB_NAME:-$DB_NAME}"

    if [ -z "$PROD_HOST" ]; then
        echo "❌ Error: PROD_DB_HOST is not set."
        echo "   Set it via environment variable or edit this script."
        echo ""
        echo "   Example:"
        echo "     PROD_DB_HOST=your-rds-endpoint.amazonaws.com ./backup_db.sh --prod"
        exit 1
    fi

    echo "📦 Dumping production database from $PROD_HOST..."
    PGPASSWORD="$PROD_PASSWORD" pg_dump \
        -h "$PROD_HOST" \
        -p "$PROD_PORT" \
        -U "$PROD_USER" \
        -d "$PROD_DB" \
        --no-owner \
        --no-privileges \
        --format=plain \
        | gzip > "$BACKUP_FILE"
fi

# ── Verify backup ──
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
    echo ""
    echo "✅ Backup complete!"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $SIZE"
else
    echo "❌ Backup failed — file not created."
    exit 1
fi

# ── Cleanup old backups ──
OLD_COUNT=$(find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS 2>/dev/null | wc -l | tr -d ' ')
if [ "$OLD_COUNT" -gt 0 ]; then
    echo ""
    echo "🧹 Cleaning up $OLD_COUNT backup(s) older than $KEEP_DAYS days..."
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS -delete
fi

echo ""
echo "📂 All backups in $BACKUP_DIR:"
ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "   (none)"
