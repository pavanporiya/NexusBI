#!/usr/bin/env bash
# NexusBI Database Restore Script
# Usage: ./scripts/restore.sh <backup_file> [container_name]
set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Usage: $0 <backup_file.sql.gz> [container_name]"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/nexusbi_*.sql.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"
CONTAINER="${2:-nbi-postgres}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite the current database!"
echo "   Container: $CONTAINER"
echo "   Backup: $BACKUP_FILE"
echo ""
read -p "Are you sure? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo "🔄 Restoring database..."

# Decompress and restore
gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER" psql -U postgres nexusbi_metadata

echo "✅ Restore complete!"
echo "   Run 'docker compose restart backend' to reload."
