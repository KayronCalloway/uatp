# UATP Database Backup and Recovery System

## Overview

The UATP Database Backup and Recovery System provides comprehensive backup and recovery capabilities for the UATP capsule database. It supports automated scheduled backups, manual backup creation, backup verification, and database recovery.

## Features

### ✅ Core Features
- **Automated Backups**: Scheduled backups with configurable intervals
- **Manual Backups**: On-demand backup creation
- **Backup Verification**: Integrity checking of backup files
- **Database Recovery**: Restore from backup files
- **Retention Management**: Automatic cleanup of old backups
- **Multiple Formats**: SQLite database + SQL dump + JSONL fallback
- **Compression**: ZIP compression for efficient storage
- **Metadata Tracking**: Detailed backup metadata and statistics

### 🔧 Technical Features
- **Atomic Operations**: Backup creation is atomic and safe
- **Error Handling**: Comprehensive error handling and retry logic
- **Hash Verification**: SHA256 checksums for file integrity
- **Concurrent Safety**: Safe to run alongside live database operations
- **Logging**: Detailed logging for monitoring and debugging

## Components

### 1. Database Backup Manager (`scripts/database_backup.py`)
Core backup functionality for creating, verifying, and managing backups.

**Key Functions:**
- `create_sqlite_backup()`: Creates a complete database backup
- `restore_from_backup()`: Restores database from backup file
- `verify_backup()`: Verifies backup integrity
- `cleanup_old_backups()`: Removes old backups based on retention policy
- `list_backups()`: Lists all available backups

### 2. Backup Scheduler (`scripts/scheduled_backup.py`)
Automated backup scheduling with configurable intervals.

**Features:**
- 24-hour default backup interval
- Configurable retry logic
- Automatic backup verification
- Startup and cleanup routines
- Continuous operation with proper error handling

### 3. Backup CLI (`scripts/backup_recovery_cli.py`)
Command-line interface for backup operations.

**Commands:**
- `backup`: Create a new backup
- `restore`: Restore from backup
- `list`: List available backups
- `verify`: Verify backup integrity
- `cleanup`: Clean up old backups

### 4. Configuration (`backup_config.json`)
JSON configuration file for backup settings.

## Usage

### Automated Backups

Start the backup scheduler:
```bash
./start_backup_scheduler.sh
```

Or manually:
```bash
python3 scripts/scheduled_backup.py
```

### Manual Backups

**Create a backup:**
```bash
python3 scripts/backup_recovery_cli.py backup
```

**Create and verify a backup:**
```bash
python3 scripts/backup_recovery_cli.py backup --verify
```

**List available backups:**
```bash
python3 scripts/backup_recovery_cli.py list
```

**Verify a backup:**
```bash
python3 scripts/backup_recovery_cli.py verify backups/uatp_backup_sqlite_20250715_180649.zip
```

**Restore from backup:**
```bash
python3 scripts/backup_recovery_cli.py restore backups/uatp_backup_sqlite_20250715_180649.zip
```

**Clean up old backups:**
```bash
python3 scripts/backup_recovery_cli.py cleanup
```

### Direct Usage

```python
from scripts.database_backup import DatabaseBackupManager

# Create backup manager
backup_manager = DatabaseBackupManager("./backups")

# Create backup
backup_result = await backup_manager.create_sqlite_backup()

# Verify backup
verification_result = await backup_manager.verify_backup(backup_result['backup_file'])

# Restore from backup
restore_result = await backup_manager.restore_from_backup(backup_result['backup_file'])
```

## Configuration

### Backup Configuration (`backup_config.json`)

```json
{
  "backup_interval_hours": 24,
  "retention_days": 30,
  "backup_dir": "./backups",
  "max_backup_attempts": 3,
  "backup_on_startup": true,
  "verify_backups": true,
  "cleanup_on_startup": true
}
```

**Configuration Options:**
- `backup_interval_hours`: Hours between automated backups (default: 24)
- `retention_days`: Days to keep backups (default: 30)
- `backup_dir`: Directory for backup storage (default: "./backups")
- `max_backup_attempts`: Maximum retry attempts for failed backups (default: 3)
- `backup_on_startup`: Create backup when scheduler starts (default: true)
- `verify_backups`: Verify backups after creation (default: true)
- `cleanup_on_startup`: Clean up old backups on startup (default: true)

## Backup Contents

Each backup contains:

### 📁 Files
- **`uatp_database.db`**: Complete SQLite database file
- **`database_dump.sql`**: SQL dump for portability
- **`capsule_chain.jsonl`**: JSONL fallback file (if exists)
- **`backup_metadata.json`**: Backup metadata and statistics

### 📊 Metadata
- Backup timestamp and status
- File checksums (SHA256)
- Database statistics (capsule counts, platforms, date ranges)
- Backup verification results

## Recovery Procedures

### 1. Standard Recovery
```bash
# List available backups
python3 scripts/backup_recovery_cli.py list

# Restore from specific backup
python3 scripts/backup_recovery_cli.py restore backups/uatp_backup_sqlite_20250715_180649.zip
```

### 2. Emergency Recovery
If the main database is corrupted:

```bash
# Stop the UATP system
# Restore from most recent backup
python3 scripts/backup_recovery_cli.py restore backups/uatp_backup_sqlite_20250715_180649.zip --force

# Restart the UATP system
```

### 3. Partial Recovery
If only specific data is needed:

```bash
# Extract backup manually
unzip backups/uatp_backup_sqlite_20250715_180649.zip -d temp_restore/

# Use SQL dump for selective recovery
sqlite3 uatp_dev.db < temp_restore/database_dump.sql
```

## Monitoring

### Backup Status
- Check backup scheduler logs: `backup_scheduler.log`
- Monitor backup directory: `./backups/`
- Verify backup integrity regularly

### Alerts
Set up monitoring for:
- Backup failures
- Disk space issues
- Old backup accumulation
- Database corruption

## Best Practices

### 🔒 Security
- Store backups in secure location
- Encrypt sensitive backups
- Restrict access to backup files
- Regular backup verification

### 📈 Performance
- Schedule backups during low-traffic periods
- Monitor backup size and duration
- Clean up old backups regularly
- Use compression for large databases

### 🛡️ Reliability
- Test restore procedures regularly
- Keep multiple backup copies
- Verify backup integrity
- Document recovery procedures

## Troubleshooting

### Common Issues

**Backup Creation Fails:**
- Check disk space
- Verify database file permissions
- Review error logs
- Try manual backup creation

**Restore Fails:**
- Verify backup file integrity
- Check target directory permissions
- Ensure database is not in use
- Try extracting backup manually

**Scheduler Stops:**
- Check system resources
- Review scheduler logs
- Verify configuration file
- Restart scheduler service

### Error Codes
- `Status: completed` - Backup successful
- `Status: failed` - Backup failed (check error message)
- `Status: warning` - Backup completed with warnings

## Integration

### With UATP System
The backup system integrates seamlessly with:
- SQLite database storage
- Real-time capsule generation
- Attribution tracking
- Visualization system

### With External Systems
- CI/CD pipelines
- Monitoring systems
- Cloud storage providers
- Disaster recovery systems

## Future Enhancements

### Planned Features
- PostgreSQL support
- Cloud storage integration
- Incremental backups
- Backup encryption
- Multi-region replication

### API Integration
- REST API for backup operations
- Webhook notifications
- Backup status monitoring
- Remote backup management

---

## Quick Reference

### Essential Commands
```bash
# Start automated backups
./start_backup_scheduler.sh

# Create manual backup
python3 scripts/backup_recovery_cli.py backup --verify

# List backups
python3 scripts/backup_recovery_cli.py list

# Restore from backup
python3 scripts/backup_recovery_cli.py restore <backup_file>

# Clean up old backups
python3 scripts/backup_recovery_cli.py cleanup
```

### Configuration Files
- `backup_config.json` - Backup settings
- `backup_scheduler.log` - Scheduler logs
- `./backups/` - Backup storage directory

### Support
For backup system issues:
1. Check logs in `backup_scheduler.log`
2. Verify configuration in `backup_config.json`
3. Test manual backup creation
4. Review database permissions and disk space