import uuid
from sqlalchemy import create_engine, Uuid
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator
from app.core.config import settings

# Ensure Uuid type processor gracefully handles string UUIDs under SQLite
_orig_uuid_bind_processor = Uuid.bind_processor
def _safe_uuid_bind_processor(self, dialect):
    proc = _orig_uuid_bind_processor(self, dialect)
    if proc is None:
        return None
    def process(value):
        if isinstance(value, str):
            try:
                value = uuid.UUID(value)
            except Exception:
                pass
        return proc(value)
    return process
Uuid.bind_processor = _safe_uuid_bind_processor

is_sqlite = "sqlite" in settings.DATABASE_URL.lower() if settings.DATABASE_URL else False

engine_kwargs = {"pool_pre_ping": True}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

# Create SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for models
Base = declarative_base()

# DB dependency generator
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
