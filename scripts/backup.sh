#!/usr/bin/env bash
# NexusBI Database Backup Script
# Usage: ./scripts/backup.sh [container_name] [backup_dir]
set -euo pipefail

CONTAINER="${1:-nbi-postgres}"
BACKUP_DIR="${2:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/nexusbi_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "🔄 Backing up NexusBI database from container: $CONTAINER"
echo "   Output: $BACKUP_FILE"

docker exec "$CONTAINER" pg_dump -U postgres nexusbi_metadata | gzip > "$BACKUP_FILE"

FILESIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup complete: $BACKUP_FILE ($FILESIZE)"

# Keep only last 30 backups
echo "🧹 Cleaning old backups (keeping last 30)..."
ls -t "$BACKUP_DIR"/nexusbi_*.sql.gz 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

echo "📋 Current backups:"
ls -lh "$BACKUP_DIR"/nexusbi_*.sql.gz 2>/dev/null | tail -5
