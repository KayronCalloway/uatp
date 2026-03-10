#!/bin/bash

# UATP Capsule Engine Database Backup Script
# Performs automated backups of PostgreSQL database with rotation

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-uatp_capsule_engine}"
POSTGRES_USER="${POSTGRES_USER:-uatp_user}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/uatp_backup_$TIMESTAMP.sql"
COMPRESSED_BACKUP="$BACKUP_FILE.gz"

echo "Starting database backup at $(date)"

# Perform database dump
if pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
   --no-password --verbose --format=custom --compress=9 \
   --file="$BACKUP_FILE"; then

   echo "Database dump completed successfully"

   # Compress the backup
   gzip "$BACKUP_FILE"
   echo "Backup compressed: $COMPRESSED_BACKUP"

   # Verify backup integrity
   if gunzip -t "$COMPRESSED_BACKUP"; then
       echo "Backup integrity verified"
   else
       echo "ERROR: Backup integrity check failed!"
       exit 1
   fi

   # Calculate backup size
   BACKUP_SIZE=$(du -h "$COMPRESSED_BACKUP" | cut -f1)
   echo "Backup size: $BACKUP_SIZE"

   # Clean up old backups
   echo "Cleaning up backups older than $RETENTION_DAYS days..."
   find "$BACKUP_DIR" -name "uatp_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

   # List remaining backups
   echo "Current backups:"
   ls -lah "$BACKUP_DIR"/uatp_backup_*.sql.gz || echo "No backups found"

   echo "Backup completed successfully at $(date)"

else
   echo "ERROR: Database backup failed!"
   exit 1
fi

# Optional: Upload to cloud storage (uncomment and configure as needed)
# aws s3 cp "$COMPRESSED_BACKUP" "s3://your-backup-bucket/uatp-backups/"
# gsutil cp "$COMPRESSED_BACKUP" "gs://your-backup-bucket/uatp-backups/"

# Optional: Send notification (uncomment and configure as needed)
# curl -X POST -H 'Content-type: application/json' \
#      --data '{"text":"UATP backup completed successfully"}' \
#      "$SLACK_WEBHOOK_URL"

echo "Backup script completed at $(date)"
