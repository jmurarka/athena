from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

reusable_oauth2 = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
) -> dict:
    """
    Decodes the Supabase JWT bearer token using the configured secret key.
    Enforces authorization rules at the endpoint layer.
    """
    token = credentials.credentials
    if not settings.SUPABASE_JWT_SECRET:
        # Fallback or alert for missing local settings
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase JWT secret is not configured in backend settings"
        )
    
    try:
        # Supabase default signature scheme is HS256 for user tokens
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        
        # Verify user ID exists in payload sub field
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing subject ID ('sub')"
            )
            
        return {
            "id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated")
        }
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate authorization credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
