import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ALEMBIC_URL = os.getenv("ALEMBIC_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required.")

if not ALEMBIC_URL:
    raise RuntimeError("ALEMBIC_URL environment variable is required.")
