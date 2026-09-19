from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User

def get_current_db_user(
    current_jwt_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts the user ID from the Supabase JWT.
    Auto-provisions the User record in the PostgreSQL database if it does not yet exist.
    """
    user_id = current_jwt_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity could not be retrieved from authorization payload"
        )
        
    import uuid
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except Exception:
            pass

    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        try:
            # Auto-provision user schema in local database
            email = current_jwt_user.get("email", "")
            user = User(
                id=user_id,
                email=email,
                auth_provider="supabase",
                name=email.split("@")[0] if email else "Authenticated User"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to auto-provision user account: {str(e)}"
            )
            
    return user
