#!/bin/bash

# UATP Comprehensive Backup System
# Performs automated backups of PostgreSQL database, Redis, and application state

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
LOG_DIR="${LOG_DIR:-/logs}"
CONFIG_DIR="${CONFIG_DIR:-/config}"

# Database configuration
POSTGRES_HOST="${POSTGRES_HOST:-postgres-primary}"
POSTGRES_DB="${POSTGRES_DB:-uatp_production}"
POSTGRES_USER="${POSTGRES_USER:-uatp_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

# Redis configuration
REDIS_HOST="${REDIS_HOST:-redis-primary}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

# AWS/S3 configuration
S3_BUCKET="${S3_BUCKET:-}"
AWS_REGION="${AWS_REGION:-us-west-2}"

# Backup configuration
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_TYPE="${BACKUP_TYPE:-full}"  # full, incremental, differential
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-9}"
ENCRYPTION_ENABLED="${BACKUP_ENCRYPTION:-true}"
VERIFICATION_ENABLED="${BACKUP_VERIFICATION:-true}"

# Notification configuration
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL_RECIPIENTS="${EMAIL_RECIPIENTS:-}"

# Initialize logging
LOG_FILE="$LOG_DIR/backup-$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$LOG_DIR" "$BACKUP_DIR"

# Logging function
log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

# Error handling
trap 'log ERROR "Backup failed at line $LINENO. Exit code: $?"' ERR

# Check prerequisites
check_prerequisites() {
    log INFO "Checking prerequisites..."

    local missing_tools=()

    for tool in pg_dump redis-cli aws gzip openssl; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done

    if [ ${#missing_tools[@]} -gt 0 ]; then
        log ERROR "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi

    # Check environment variables
    if [ -z "$POSTGRES_PASSWORD" ]; then
        log ERROR "POSTGRES_PASSWORD not set"
        exit 1
    fi

    log INFO "Prerequisites check passed"
}

# Generate backup metadata
generate_metadata() {
    local backup_file="$1"
    local metadata_file="${backup_file}.metadata"

    cat > "$metadata_file" << EOF
{
    "backup_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "backup_type": "$BACKUP_TYPE",
    "database_host": "$POSTGRES_HOST",
    "database_name": "$POSTGRES_DB",
    "backup_size": "$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file")",
    "compression_level": "$COMPRESSION_LEVEL",
    "encrypted": "$ENCRYPTION_ENABLED",
    "checksum": "$(sha256sum "$backup_file" | cut -d' ' -f1)",
    "version": "$(psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT version();" | xargs)"
}
EOF
}

# Database backup
backup_database() {
    log INFO "Starting database backup..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/postgres_backup_${timestamp}.sql"
    local compressed_file="${backup_file}.gz"

    # Set password for pg_dump
    export PGPASSWORD="$POSTGRES_PASSWORD"

    # Perform backup based on type
    case "$BACKUP_TYPE" in
        "full")
            log INFO "Performing full database backup"
            pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
                --verbose --format=custom --no-password \
                --file="$backup_file"
            ;;
        "schema-only")
            log INFO "Performing schema-only backup"
            pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
                --verbose --schema-only --no-password \
                --file="$backup_file"
            ;;
        "data-only")
            log INFO "Performing data-only backup"
            pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
                --verbose --data-only --no-password \
                --file="$backup_file"
            ;;
    esac

    # Compress backup
    log INFO "Compressing backup file..."
    gzip -"$COMPRESSION_LEVEL" "$backup_file"

    # Encrypt if enabled
    if [ "$ENCRYPTION_ENABLED" = "true" ]; then
        log INFO "Encrypting backup file..."
        local encrypted_file="${compressed_file}.enc"
        openssl enc -aes-256-cbc -salt -in "$compressed_file" -out "$encrypted_file" -k "$BACKUP_ENCRYPTION_KEY"
        rm "$compressed_file"
        compressed_file="$encrypted_file"
    fi

    # Generate metadata
    generate_metadata "$compressed_file"

    # Verify backup if enabled
    if [ "$VERIFICATION_ENABLED" = "true" ]; then
        verify_backup "$compressed_file"
    fi

    log INFO "Database backup completed: $compressed_file"
    echo "$compressed_file"
}

# Redis backup
backup_redis() {
    log INFO "Starting Redis backup..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/redis_backup_${timestamp}.rdb"

    # Get Redis authentication
    local redis_auth=""
    if [ -n "$REDIS_PASSWORD" ]; then
        redis_auth="-a $REDIS_PASSWORD"
    fi

    # Trigger Redis save
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $redis_auth BGSAVE

    # Wait for background save to complete
    while [ "$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $redis_auth LASTSAVE)" = "$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $redis_auth LASTSAVE)" ]; do
        sleep 1
    done

    # Copy RDB file
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $redis_auth --rdb "$backup_file"

    # Compress
    gzip -"$COMPRESSION_LEVEL" "$backup_file"
    local compressed_file="${backup_file}.gz"

    log INFO "Redis backup completed: $compressed_file"
    echo "$compressed_file"
}

# Application state backup
backup_application_state() {
    log INFO "Starting application state backup..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/app_state_${timestamp}.tar.gz"

    # Backup configuration files, logs, and other important data
    tar -czf "$backup_file" \
        -C / \
        app/logs \
        app/config \
        app/data \
        2>/dev/null || true

    log INFO "Application state backup completed: $backup_file"
    echo "$backup_file"
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    log INFO "Verifying backup integrity: $backup_file"

    # Check if file exists and is not empty
    if [ ! -s "$backup_file" ]; then
        log ERROR "Backup file is empty or does not exist"
        return 1
    fi

    # Verify compression integrity
    if [[ "$backup_file" == *.gz ]]; then
        if ! gzip -t "$backup_file"; then
            log ERROR "Backup file is corrupted (gzip test failed)"
            return 1
        fi
    fi

    # Verify encryption if applicable
    if [[ "$backup_file" == *.enc ]]; then
        # Test decryption without extracting
        if ! openssl enc -aes-256-cbc -d -in "$backup_file" -k "$BACKUP_ENCRYPTION_KEY" | head -c 1 > /dev/null; then
            log ERROR "Backup file encryption verification failed"
            return 1
        fi
    fi

    log INFO "Backup integrity verification passed"
    return 0
}

# Upload to cloud storage
upload_to_cloud() {
    local backup_file="$1"

    if [ -z "$S3_BUCKET" ]; then
        log WARN "S3_BUCKET not configured, skipping cloud upload"
        return 0
    fi

    log INFO "Uploading backup to S3: $S3_BUCKET"

    local s3_key="uatp-backups/$(date +%Y/%m/%d)/$(basename "$backup_file")"

    if aws s3 cp "$backup_file" "s3://$S3_BUCKET/$s3_key" \
        --region "$AWS_REGION" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256; then
        log INFO "Backup uploaded successfully to s3://$S3_BUCKET/$s3_key"

        # Upload metadata as well
        local metadata_file="${backup_file}.metadata"
        if [ -f "$metadata_file" ]; then
            aws s3 cp "$metadata_file" "s3://$S3_BUCKET/${s3_key}.metadata" \
                --region "$AWS_REGION"
        fi
    else
        log ERROR "Failed to upload backup to S3"
        return 1
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log INFO "Cleaning up backups older than $RETENTION_DAYS days..."

    # Local cleanup
    find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.rdb.gz" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.metadata" -type f -mtime +$RETENTION_DAYS -delete

    # S3 cleanup (if configured)
    if [ -n "$S3_BUCKET" ]; then
        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
        log INFO "Cleaning up S3 backups older than $cutoff_date"

        # This would require a more complex script to list and delete old S3 objects
        # For now, we'll rely on S3 lifecycle policies
    fi

    log INFO "Cleanup completed"
}

# Send notifications
send_notification() {
    local status="$1"
    local message="$2"

    # Slack notification
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"UATP Backup $status: $message\"}" \
            "$SLACK_WEBHOOK" || true
    fi

    # Email notification (if configured)
    if [ -n "$EMAIL_RECIPIENTS" ]; then
        echo "$message" | mail -s "UATP Backup $status" "$EMAIL_RECIPIENTS" || true
    fi
}

# Main backup function
main() {
    log INFO "Starting UATP backup process..."
    local start_time=$(date +%s)

    check_prerequisites

    local backup_files=()
    local failed_backups=()

    # Perform database backup
    if db_backup_file=$(backup_database); then
        backup_files+=("$db_backup_file")
        upload_to_cloud "$db_backup_file" || failed_backups+=("database upload")
    else
        failed_backups+=("database")
    fi

    # Perform Redis backup
    if redis_backup_file=$(backup_redis); then
        backup_files+=("$redis_backup_file")
        upload_to_cloud "$redis_backup_file" || failed_backups+=("redis upload")
    else
        failed_backups+=("redis")
    fi

    # Perform application state backup
    if app_backup_file=$(backup_application_state); then
        backup_files+=("$app_backup_file")
        upload_to_cloud "$app_backup_file" || failed_backups+=("application upload")
    else
        failed_backups+=("application state")
    fi

    # Cleanup old backups
    cleanup_old_backups

    # Calculate execution time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Generate summary
    local summary="Backup completed in ${duration}s. Files created: ${#backup_files[@]}"
    if [ ${#failed_backups[@]} -gt 0 ]; then
        summary="$summary. Failed: ${failed_backups[*]}"
        log ERROR "$summary"
        send_notification "FAILED" "$summary"
        exit 1
    else
        log INFO "$summary"
        send_notification "SUCCESS" "$summary"
    fi

    log INFO "Backup process completed successfully"
}

# Run main function
main "$@"
