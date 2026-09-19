import uuid
from sqlalchemy import Column, String, DateTime, func, Uuid
from sqlalchemy.orm import relationship
from app.core.db import Base

class User(Base):
    """
    SQLAlchemy model representing the 'users' table,
    synchronized with Supabase identities.
    """
    __tablename__ = "users"
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    auth_provider = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
