"""
Single, module-level SQLAlchemy engine for Neon.
Import `engine` wherever you need a DB connection — never call create_engine()
more than once, and never open a raw connection per-request.
"""
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

neon_pooled_url = os.getenv("DATABASE_URL")

engine = create_engine(
    neon_pooled_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)