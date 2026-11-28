#!/usr/bin/env bash
# ==============================================================================
# Spoken Social — Production Deployment Script
# ==============================================================================
# Safe, idempotent deployment runner.
# Can be run manually on the server or automatically by GitHub Actions CD.
#
# Usage:
#   ./scripts/deploy.sh                 # Normal deploy (backup + pull + build + migrate + verify)
#   ./scripts/deploy.sh --skip-backup   # Fast deploy without pre-flight backup
#   ./scripts/deploy.sh --no-pull       # Deploy current local files without git pull
# ==============================================================================

set -euo pipefail

# ── Paths & Setup ──
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
git config --global --add safe.directory "$ROOT_DIR" 2>/dev/null || true
git config --global --add safe.directory "*" 2>/dev/null || true

SKIP_BACKUP=false
SKIP_PULL=false

for arg in "$@"; do
    case "$arg" in
        --skip-backup) SKIP_BACKUP=true ;;
        --no-pull)     SKIP_PULL=true ;;
        *)
            echo "Unknown argument: $arg"
            echo "Usage: ./scripts/deploy.sh [--skip-backup] [--no-pull]"
            exit 1
            ;;
    esac
done

echo "=========================================================="
echo "🚀 Starting Spoken Social Deployment"
echo "   Directory: $ROOT_DIR"
echo "   Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "=========================================================="

# ── 1. Pre-flight Checks ──
echo "📋 [1/6] Running pre-flight checks..."

if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Error: Docker is not installed or not in PATH."
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "❌ Error: Docker Compose is not installed."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "❌ Error: Production .env file not found in $ROOT_DIR."
    echo "   Ensure .env is configured before deploying."
    exit 1
fi

echo "   Docker and .env are ready."

# ── 2. Pre-deploy Database Backup ──
# Production Postgres runs in this compose project, so backup_db.sh's default
# (docker exec) mode is the production backup. Its --prod mode is for a remote
# database host and would fail here. A failed backup stops the deploy before
# any migration runs; pass --skip-backup to override deliberately.
echo "💾 [2/6] Backing up the database..."
BACKUP_NOTE="skipped (--skip-backup)"
if [ "$SKIP_BACKUP" = false ]; then
    if docker compose ps --services --filter "status=running" | grep -q "^postgres$"; then
        if ! ./backup_db.sh; then
            echo "❌ Database backup failed — aborting before migrations."
            echo "   Fix the backup, or re-run with --skip-backup to deploy without one."
            exit 1
        fi
        LATEST_BACKUP=$(ls -t backups/*.sql.gz)
        LATEST_BACKUP=${LATEST_BACKUP%%$'\n'*}
        BACKUP_NOTE="$LATEST_BACKUP ($(du -h "$LATEST_BACKUP" | cut -f1))"
    else
        BACKUP_NOTE="none (postgres was not running, nothing to back up)"
        echo "   Postgres is not running yet; nothing to back up."
    fi
else
    echo "   Backup skipped (--skip-backup)."
fi
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    echo "- **Database backup:** \`$BACKUP_NOTE\`" >> "$GITHUB_STEP_SUMMARY"
fi

# ── 3. Pull Latest Code ──
if [ "$SKIP_PULL" = false ]; then
    echo "📥 [3/6] Pulling latest code from origin/master..."
    git fetch origin master
    git checkout master
    git pull --ff-only origin master
else
    echo "⏭️  [3/6] Skipping git pull (--no-pull specified)."
fi

# ── 4. Build Images ──
# CRITICAL: Rebuilding before migrating is load-bearing;
# running alembic inside a stale image silently no-ops.
echo "🏗️  [4/6] Building production Docker images..."
docker compose build --pull

# ── 5. Up Containers & Run Migrations ──
echo "🔄 [5/6] Updating containers & running migrations..."
docker compose up -d --remove-orphans

echo "   Applying Alembic database migrations..."
docker compose exec -T backend alembic upgrade head

# ── 6. Health & Smoke Checks ──
echo "🩺 [6/6] Running post-deployment health verification..."
sleep 4

# Check container statuses
RUNNING_SERVICES=$(docker compose ps --services --filter "status=running")
echo "   Running services:"
echo "$RUNNING_SERVICES" | sed 's/^/     - /'

for req_svc in backend postgres redis frontend; do
    if ! echo "$RUNNING_SERVICES" | grep -q "^$req_svc$"; then
        echo "❌ Health check failed: '$req_svc' is not running!"
        docker compose logs --tail=50 "$req_svc"
        exit 1
    fi
done

# Backend HTTP health check inside docker network
echo "   Verifying backend API health..."
BACKEND_HEALTH=$(docker compose exec -T backend python -c "
import urllib.request, json
try:
    resp = urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=5)
    data = json.loads(resp.read().decode('utf-8'))
    print(data.get('status', 'unknown'))
except Exception as e:
    print(f'error: {e}')
")

if [ "$BACKEND_HEALTH" != "healthy" ]; then
    echo "❌ Backend health check failed with status: '$BACKEND_HEALTH'"
    docker compose logs --tail=50 backend
    exit 1
fi

echo "=========================================================="
echo "✅ Spoken Social successfully deployed and healthy!"
echo "   Backend:  Healthy (200 OK on /api/health)"
echo "   Database: Migrations up to date (alembic head)"
echo "   Finished: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "=========================================================="
