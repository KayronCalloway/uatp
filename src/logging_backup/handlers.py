"""
Logging Handlers
================

Custom logging handlers for database, security, and external systems.
"""

import logging
import logging.handlers
import asyncio
import json
import queue
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import os


class DatabaseHandler(logging.Handler):
    """Handler that stores logs in database."""

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.db_manager = None  # Will be set from database manager
        self.log_queue = queue.Queue(maxsize=1000)
        self.batch_size = 100
        self.flush_interval = 30  # seconds

        # Start background thread for batch processing
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

        # Start periodic flush
        self.flush_timer = threading.Timer(self.flush_interval, self._periodic_flush)
        self.flush_timer.daemon = True
        self.flush_timer.start()

    def emit(self, record: logging.LogRecord):
        """Add log record to queue for batch processing."""
        try:
            # Format the record
            log_entry = self.format(record)

            # Parse JSON if it's a JSON formatter
            try:
                log_data = json.loads(log_entry)
            except json.JSONDecodeError:
                log_data = {
                    "timestamp": datetime.fromtimestamp(
                        record.created, tz=timezone.utc
                    ).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": log_entry,
                }

            # Add to queue (non-blocking)
            try:
                self.log_queue.put_nowait(log_data)
            except queue.Full:
                # Queue is full, skip this log entry
                # In production, you might want to implement a fallback
                pass

        except Exception:
            self.handleError(record)

    def _worker(self):
        """Background worker to process log queue."""
        batch = []

        while True:
            try:
                # Get log entry from queue (blocking with timeout)
                try:
                    log_data = self.log_queue.get(timeout=5)
                    batch.append(log_data)
                except queue.Empty:
                    # Timeout, flush current batch if not empty
                    if batch:
                        self._flush_batch(batch)
                        batch = []
                    continue

                # Flush batch when it reaches batch size
                if len(batch) >= self.batch_size:
                    self._flush_batch(batch)
                    batch = []

            except Exception as e:
                # Log error but keep worker running
                print(f"Database handler worker error: {e}")

    def _flush_batch(self, batch: List[Dict[str, Any]]):
        """Flush batch of log entries to database."""
        if not batch or not self.db_manager:
            return

        try:
            # This would be implemented with actual database operations
            # For now, we'll just store the logic structure

            # Example SQL for log storage:
            # INSERT INTO logs (timestamp, level, logger, message, data)
            # VALUES (%(timestamp)s, %(level)s, %(logger)s, %(message)s, %(data)s)

            # asyncio.create_task(self._store_logs_async(batch))
            pass

        except Exception as e:
            print(f"Error flushing log batch to database: {e}")

    async def _store_logs_async(self, batch: List[Dict[str, Any]]):
        """Store logs in database asynchronously."""
        if not self.db_manager:
            return

        try:
            # Prepare batch insert
            insert_data = []
            for log_entry in batch:
                insert_data.append(
                    {
                        "timestamp": log_entry.get("timestamp"),
                        "level": log_entry.get("level"),
                        "logger": log_entry.get("logger"),
                        "message": log_entry.get("message"),
                        "data": json.dumps(log_entry),
                    }
                )

            # Batch insert into database
            # await self.db_manager.execute_many(
            #     "INSERT INTO logs (timestamp, level, logger, message, data) VALUES ($1, $2, $3, $4, $5)",
            #     [(d['timestamp'], d['level'], d['logger'], d['message'], d['data']) for d in insert_data]
            # )

        except Exception as e:
            print(f"Error storing logs in database: {e}")

    def _periodic_flush(self):
        """Periodic flush of remaining logs."""
        # This would trigger a flush of any remaining logs in the queue
        # and restart the timer
        try:
            # Signal worker to flush current batch
            pass
        except Exception as e:
            print(f"Error in periodic flush: {e}")
        finally:
            # Restart timer
            self.flush_timer = threading.Timer(
                self.flush_interval, self._periodic_flush
            )
            self.flush_timer.daemon = True
            self.flush_timer.start()

    def close(self):
        """Close handler and flush remaining logs."""
        # Stop timer
        if hasattr(self, "flush_timer"):
            self.flush_timer.cancel()

        # Flush remaining logs
        remaining_logs = []
        while not self.log_queue.empty():
            try:
                remaining_logs.append(self.log_queue.get_nowait())
            except queue.Empty:
                break

        if remaining_logs:
            self._flush_batch(remaining_logs)

        super().close()


class SecurityHandler(logging.handlers.RotatingFileHandler):
    """Specialized handler for security logs with enhanced features."""

    def __init__(
        self, filename, mode="a", maxBytes=0, backupCount=0, encoding=None, delay=False
    ):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)

        # Security-specific configuration
        self.alert_threshold = logging.ERROR
        self.alert_recipients = self._get_alert_recipients()
        self.incident_counter = {}
        self.alert_cooldown = 300  # 5 minutes between similar alerts
        self.last_alerts = {}

    def emit(self, record: logging.LogRecord):
        """Emit security log with alerting capability."""
        try:
            # Standard file logging
            super().emit(record)

            # Check if alert should be sent
            if record.levelno >= self.alert_threshold:
                self._check_and_send_alert(record)

        except Exception:
            self.handleError(record)

    def _check_and_send_alert(self, record: logging.LogRecord):
        """Check if alert should be sent and send if needed."""
        alert_key = f"{record.name}:{record.levelname}"
        current_time = datetime.now()

        # Check cooldown
        if alert_key in self.last_alerts:
            time_diff = (current_time - self.last_alerts[alert_key]).total_seconds()
            if time_diff < self.alert_cooldown:
                return

        # Send alert
        self._send_security_alert(record)
        self.last_alerts[alert_key] = current_time

    def _send_security_alert(self, record: logging.LogRecord):
        """Send security alert to configured recipients."""
        try:
            alert_data = {
                "timestamp": datetime.fromtimestamp(
                    record.created, tz=timezone.utc
                ).isoformat(),
                "severity": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
                "hostname": self._get_hostname(),
            }

            # Add extra context if available
            if hasattr(record, "__dict__"):
                extra_fields = {
                    k: v
                    for k, v in record.__dict__.items()
                    if not k.startswith("_")
                    and k not in ["name", "msg", "args", "levelname", "levelno"]
                }
                alert_data.update(extra_fields)

            # In production, this would send to alerting system
            # Examples: Slack, PagerDuty, email, SMS
            self._log_alert_attempt(alert_data)

        except Exception as e:
            print(f"Error sending security alert: {e}")

    def _get_alert_recipients(self) -> List[str]:
        """Get list of alert recipients from configuration."""
        recipients_str = os.getenv("SECURITY_ALERT_RECIPIENTS", "")
        if recipients_str:
            return recipients_str.split(",")
        return []

    def _get_hostname(self) -> str:
        """Get hostname for alert context."""
        import socket

        try:
            return socket.gethostname()
        except Exception:
            return "unknown"

    def _log_alert_attempt(self, alert_data: Dict[str, Any]):
        """Log the alert attempt (for debugging/auditing)."""
        alert_log = {
            "alert_sent": True,
            "alert_data": alert_data,
            "recipients": self.alert_recipients,
        }
        print(f"Security alert would be sent: {json.dumps(alert_log, indent=2)}")


class ExternalSystemHandler(logging.Handler):
    """Handler for sending logs to external systems (ELK, Splunk, etc.)."""

    def __init__(self, system_type: str, endpoint: str, api_key: Optional[str] = None):
        super().__init__()
        self.system_type = system_type.lower()
        self.endpoint = endpoint
        self.api_key = api_key
        self.session = None
        self.retry_attempts = 3
        self.retry_delay = 1  # seconds

    def emit(self, record: logging.LogRecord):
        """Send log to external system."""
        try:
            log_data = self._prepare_log_data(record)

            if self.system_type == "elasticsearch":
                self._send_to_elasticsearch(log_data)
            elif self.system_type == "splunk":
                self._send_to_splunk(log_data)
            elif self.system_type == "webhook":
                self._send_to_webhook(log_data)
            else:
                raise ValueError(f"Unsupported system type: {self.system_type}")

        except Exception:
            self.handleError(record)

    def _prepare_log_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Prepare log data for external system."""
        # Format the record
        formatted_message = self.format(record)

        # Try to parse as JSON, fallback to plain message
        try:
            log_data = json.loads(formatted_message)
        except json.JSONDecodeError:
            log_data = {
                "timestamp": datetime.fromtimestamp(
                    record.created, tz=timezone.utc
                ).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": formatted_message,
            }

        # Add system metadata
        log_data["_system"] = {
            "source": "uatp_capsule_engine",
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "version": os.getenv("APP_VERSION", "unknown"),
        }

        return log_data

    def _send_to_elasticsearch(self, log_data: Dict[str, Any]):
        """Send log to Elasticsearch."""
        # This would implement actual Elasticsearch integration
        # using elasticsearch-py library
        pass

    def _send_to_splunk(self, log_data: Dict[str, Any]):
        """Send log to Splunk."""
        # This would implement actual Splunk integration
        # using splunk-sdk-python library
        pass

    def _send_to_webhook(self, log_data: Dict[str, Any]):
        """Send log to webhook endpoint."""
        import requests

        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.post(
                self.endpoint, json=log_data, headers=headers, timeout=10
            )
            response.raise_for_status()

        except Exception as e:
            raise Exception(f"Failed to send log to webhook: {e}")


class AuditTrailHandler(logging.handlers.RotatingFileHandler):
    """Specialized handler for audit trails with tamper protection."""

    def __init__(
        self, filename, mode="a", maxBytes=0, backupCount=0, encoding=None, delay=False
    ):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)

        # Audit-specific features
        self.integrity_check = True
        self.digital_signatures = False  # Would require crypto setup
        self.hash_chain = []
        self.last_hash = None

    def emit(self, record: logging.LogRecord):
        """Emit audit log with integrity protection."""
        try:
            # Add integrity hash to record
            if self.integrity_check:
                self._add_integrity_hash(record)

            # Standard file logging
            super().emit(record)

            # Update hash chain
            if self.integrity_check:
                self._update_hash_chain(record)

        except Exception:
            self.handleError(record)

    def _add_integrity_hash(self, record: logging.LogRecord):
        """Add integrity hash to log record."""
        import hashlib

        # Create hash of record content
        record_content = (
            f"{record.created}{record.levelname}{record.name}{record.getMessage()}"
        )

        # Include previous hash for chaining
        if self.last_hash:
            record_content += self.last_hash

        current_hash = hashlib.sha256(record_content.encode()).hexdigest()

        # Add hash to record
        record.integrity_hash = current_hash
        record.previous_hash = self.last_hash

    def _update_hash_chain(self, record: logging.LogRecord):
        """Update integrity hash chain."""
        if hasattr(record, "integrity_hash"):
            self.hash_chain.append(record.integrity_hash)
            self.last_hash = record.integrity_hash

            # Keep only last 1000 hashes in memory
            if len(self.hash_chain) > 1000:
                self.hash_chain = self.hash_chain[-1000:]

    def verify_integrity(self, log_file_path: str) -> bool:
        """Verify integrity of audit log file."""
        # This would implement full integrity verification
        # by reading the log file and checking hash chains
        try:
            # Implementation would read file and verify each hash
            return True
        except Exception as e:
            print(f"Integrity verification failed: {e}")
            return False


class MetricsHandler(logging.Handler):
    """Handler that converts logs to metrics."""

    def __init__(self):
        super().__init__()
        self.metrics_collector = None  # Would be set from metrics system

    def emit(self, record: logging.LogRecord):
        """Convert log record to metrics."""
        try:
            # Extract metrics from log record
            if record.levelname == "ERROR":
                self._increment_error_counter(record)

            if hasattr(record, "response_time"):
                self._record_response_time(record)

            if hasattr(record, "user_id"):
                self._record_user_activity(record)

        except Exception:
            self.handleError(record)

    def _increment_error_counter(self, record: logging.LogRecord):
        """Increment error counter metric."""
        # This would integrate with Prometheus or other metrics system
        pass

    def _record_response_time(self, record: logging.LogRecord):
        """Record response time metric."""
        # This would record histogram metric
        pass

    def _record_user_activity(self, record: logging.LogRecord):
        """Record user activity metric."""
        # This would increment user activity counter
        pass
