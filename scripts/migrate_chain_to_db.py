import json
import logging
import os
import sys

from sqlalchemy.orm import Session

# Add project root to Python path to allow imports from src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import our application modules
# Now we can import our application modules
from crud import capsule as capsule_crud

from capsule_schema import Capsule as CapsuleSchema
from core.database import Base, SessionLocal, engine
from crypto_utils import hash_capsule_dict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define the path to the old chain file, relative to the project root
CHAIN_FILE_PATH = os.path.join(
    project_root, os.environ.get("UATP_CHAIN_PATH", "capsule_chain.jsonl")
)


def migrate_data(db: Session):
    """
    Reads capsules from the JSONL file and migrates them to the database.
    """
    if not os.path.exists(CHAIN_FILE_PATH):
        logging.warning(
            f"Chain file not found at {CHAIN_FILE_PATH}. No data to migrate."
        )
        return

    migrated_count = 0
    skipped_count = 0

    logging.info(f"Starting migration from {CHAIN_FILE_PATH}...")

    with open(CHAIN_FILE_PATH) as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                data = json.loads(line)
                # The chain file might have aliases like 'type', so we use pydantic to validate and load
                capsule_schema = CapsuleSchema.model_validate(data)

                # If hash is missing, generate it. This is crucial for data integrity.
                if not capsule_schema.hash:
                    logging.warning(
                        f"Capsule {capsule_schema.capsule_id} is missing a hash. Generating one now."
                    )
                    capsule_dict_for_hashing = capsule_schema.model_dump(
                        exclude={"hash", "signature"}, by_alias=True, exclude_none=True
                    )
                    capsule_schema.hash = hash_capsule_dict(capsule_dict_for_hashing)

                # Check if capsule already exists
                existing = capsule_crud.get_capsule(
                    db, capsule_id=capsule_schema.capsule_id
                )
                if existing:
                    logging.info(
                        f"Skipping duplicate capsule ID: {capsule_schema.capsule_id}"
                    )
                    skipped_count += 1
                    continue

                # Create capsule in DB
                capsule_crud.create_capsule(db, capsule=capsule_schema)
                logging.info(f"Migrated capsule ID: {capsule_schema.capsule_id}")
                migrated_count += 1

            except json.JSONDecodeError:
                logging.error(f"Skipping corrupted line {i} in chain file.")
            except Exception as e:
                logging.error(f"Error processing line {i}: {e}", exc_info=True)
                db.rollback()  # Rollback the session to continue with the next line

    logging.info("Migration complete.")
    logging.info(f"Successfully migrated: {migrated_count} capsules.")
    logging.info(f"Skipped (duplicates): {skipped_count} capsules.")


if __name__ == "__main__":
    logging.info("Recreating database schema to ensure it's up to date...")
    # This will drop all tables and recreate them, ensuring a clean slate.
    # Make sure all models are imported so Base knows about them.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logging.info("Database schema successfully recreated.")

    db = SessionLocal()
    try:
        migrate_data(db)
    finally:
        db.close()
