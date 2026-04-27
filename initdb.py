import os
import sys
import time

from sqlalchemy import text

import models  # noqa: F401
from database import Base, engine


MAX_ATTEMPTS = int(os.getenv("DB_INIT_MAX_ATTEMPTS", "30"))
RETRY_DELAY_SECONDS = float(os.getenv("DB_INIT_RETRY_DELAY", "5"))


def wait_for_database() -> None:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Database connection established on attempt {attempt}.")
            return
        except Exception as exc:
            print(f"Database not ready yet (attempt {attempt}/{MAX_ATTEMPTS}): {exc}")
            if attempt == MAX_ATTEMPTS:
                raise
            time.sleep(RETRY_DELAY_SECONDS)


def initialize_schema() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE invoices "
                "ADD COLUMN IF NOT EXISTS user_id VARCHAR(50) DEFAULT '1'"
            )
        )
    print("Invoice service database schema initialized successfully.")


if __name__ == "__main__":
    try:
        wait_for_database()
        initialize_schema()
    except Exception as exc:
        print(f"Invoice service DB initialization failed: {exc}")
        sys.exit(1)
