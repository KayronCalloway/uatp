"""
Setup Honey Tokens for Intrusion Detection

This script initializes honey tokens and canary traps throughout the system.
Run this once during deployment to plant deception-based security measures.

Usage:
    python scripts/setup_honey_tokens.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from src.security.honey_tokens import HoneyTokenManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_honey_tokens():
    """Initialize honey tokens in the system"""

    manager = HoneyTokenManager()

    logger.info(" Setting up honey tokens for intrusion detection...")

    # 1. Generate fake API keys
    logger.info("\n Creating honey API keys...")

    honey_keys = []
    for i in range(5):
        key = manager.generate_honey_api_key(
            owner="security_team",
            description=f"Fake API key #{i + 1} for intrusion detection",
        )
        honey_keys.append(key)
        logger.info(f"   Created: {key[:30]}...")

    # 2. Generate canary database records
    logger.info("\n Creating canary database records...")

    # Fake user record
    manager.generate_canary_database_record(
        table_name="users",
        record_data={
            "user_id": "canary_user_admin",
            "username": "admin",
            "email": "admin@internal.uatp.local",
            "is_admin": True,
            "api_key": "sk_canary_admin_key_do_not_use",
        },
        owner="security_team",
    )
    logger.info("   Created: Canary admin user record")

    # Fake sensitive configuration
    manager.generate_canary_database_record(
        table_name="configurations",
        record_data={
            "config_id": "canary_config_secrets",
            "config_key": "master_encryption_key",
            "config_value": "canary_fake_encryption_key_12345",
            "is_sensitive": True,
        },
        owner="security_team",
    )
    logger.info("   Created: Canary encryption key config")

    # Fake payment information
    manager.generate_canary_database_record(
        table_name="payment_methods",
        record_data={
            "payment_id": "canary_payment_001",
            "card_number": "4111111111111111",  # Test card number
            "cvv": "123",
            "owner": "canary_user",
        },
        owner="security_team",
    )
    logger.info("   Created: Canary payment record")

    # 3. Generate honey file paths
    logger.info("\n Creating honey file paths...")

    sensitive_files = [
        "/app/.env",
        "/app/config/secrets.json",
        "/app/credentials.txt",
        "/app/database_backup.sql",
        "/app/private_keys/master.pem",
    ]

    for file_path in sensitive_files:
        manager.generate_honey_file_path(file_path=file_path, owner="security_team")
        logger.info(f"   Created: {file_path}")

    # Summary
    logger.info("\n[OK] Honey token setup complete!")
    logger.info("\n Summary:")
    logger.info(f"   - Fake API keys: {len(honey_keys)}")
    logger.info("   - Canary database records: 3")
    logger.info(f"   - Honey file paths: {len(sensitive_files)}")

    logger.info("\n[WARN]  IMPORTANT:")
    logger.info(
        "   - These honey tokens will trigger CRITICAL security alerts if accessed"
    )
    logger.info("   - Never use these credentials or access these files/records")
    logger.info(
        "   - Alerts are logged to: security/honey_tokens/honey_token_alerts.jsonl"
    )

    logger.info("\n To check for intrusions:")
    logger.info("   - Monitor: security/honey_tokens/honey_token_alerts.jsonl")
    logger.info("   - Check audit logs for 'honey_token_triggered' events")
    logger.info("   - Run: python scripts/check_honey_token_alerts.py")


if __name__ == "__main__":
    setup_honey_tokens()
