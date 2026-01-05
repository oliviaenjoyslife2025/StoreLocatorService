from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from auth import get_current_user
from models import User, Role, Permission
from database import get_db

# Permission definitions
PERMISSIONS = {
    "stores:create": ("stores", "create"),
    "stores:read": ("stores", "read"),
    "stores:update": ("stores", "update"),
    "stores:delete": ("stores", "delete"),
    "stores:import": ("stores", "import"),
    "users:create": ("users", "create"),
    "users:read": ("users", "read"),
    "users:update": ("users", "update"),
    "users:delete": ("users", "delete"),
}

def check_permission(permission_name: str):
    """Decorator to check if user has required permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs (injected by Depends)
            current_user: User = kwargs.get("current_user")
            db: Session = kwargs.get("db")
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check if user's role has the required permission
            role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User role not found"
                )
            
            # Get permission details
            resource, action = PERMISSIONS.get(permission_name, (None, None))
            if not resource or not action:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Invalid permission: {permission_name}"
                )
            
            # Check if role has the permission
            has_permission = any(
                p.resource == resource and p.action == action
                for p in role.permissions
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission_name}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(allowed_roles: list):
    """Dependency to check if user has one of the allowed roles."""
    def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
        if not role or role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# Convenience dependencies for common role checks
def require_admin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """Require admin role."""
    role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
    if not role or role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_admin_or_marketer(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """Require admin or marketer role."""
    role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
    if not role or role.name not in ["admin", "marketer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Marketer access required"
        )
    return current_user

