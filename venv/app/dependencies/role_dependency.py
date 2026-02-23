from fastapi import Depends, HTTPException, status
from app.dependencies.auth_dependency import get_current_user
from app.models.user import User


def admin_only(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
