#!/bin/bash
# Daily Postgres backup. Keeps last 14 daily dumps.
set -e
BACKUP_DIR=/root/backups/postgres
mkdir -p $BACKUP_DIR
STAMP=$(date +%Y%m%d_%H%M%S)
FILE=$BACKUP_DIR/meepo_$STAMP.sql.gz

docker exec meeposite-db-1 pg_dump -U meepo -d meepo --no-owner --clean --if-exists \
  | gzip -9 > $FILE

# Rotate: keep last 14 daily dumps
ls -t $BACKUP_DIR/meepo_*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm -f

echo "[$(date -Iseconds)] Backup OK: $FILE ($(du -h $FILE | cut -f1))"
