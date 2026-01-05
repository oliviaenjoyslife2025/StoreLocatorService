from sqlalchemy.orm import Session
from database import SessionLocal
from models import Role, Permission, User
from auth import hash_password

def init_roles_and_permissions(db: Session):
    """Initialize roles and permissions in the database."""
    
    # Create roles
    roles_data = [
        {"role_id": "R001", "name": "admin", "description": "Full access to all endpoints"},
        {"role_id": "R002", "name": "marketer", "description": "Can manage stores and perform imports"},
        {"role_id": "R003", "name": "viewer", "description": "Read-only access to stores"},
    ]
    
    for role_data in roles_data:
        role = db.query(Role).filter(Role.role_id == role_data["role_id"]).first()
        if not role:
            role = Role(**role_data)
            db.add(role)
    
    db.commit()
    
    # Create permissions
    permissions_data = [
        {"permission_id": "P001", "name": "stores:create", "resource": "stores", "action": "create"},
        {"permission_id": "P002", "name": "stores:read", "resource": "stores", "action": "read"},
        {"permission_id": "P003", "name": "stores:update", "resource": "stores", "action": "update"},
        {"permission_id": "P004", "name": "stores:delete", "resource": "stores", "action": "delete"},
        {"permission_id": "P005", "name": "stores:import", "resource": "stores", "action": "import"},
        {"permission_id": "P006", "name": "users:create", "resource": "users", "action": "create"},
        {"permission_id": "P007", "name": "users:read", "resource": "users", "action": "read"},
        {"permission_id": "P008", "name": "users:update", "resource": "users", "action": "update"},
        {"permission_id": "P009", "name": "users:delete", "resource": "users", "action": "delete"},
    ]
    
    for perm_data in permissions_data:
        permission = db.query(Permission).filter(Permission.permission_id == perm_data["permission_id"]).first()
        if not permission:
            permission = Permission(**perm_data)
            db.add(permission)
    
    db.commit()
    
    # Assign permissions to roles
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    marketer_role = db.query(Role).filter(Role.name == "marketer").first()
    viewer_role = db.query(Role).filter(Role.name == "viewer").first()
    
    all_permissions = db.query(Permission).all()
    store_permissions = [p for p in all_permissions if p.resource == "stores"]
    user_permissions = [p for p in all_permissions if p.resource == "users"]
    
    # Admin: all permissions
    for perm in all_permissions:
        if perm not in admin_role.permissions:
            admin_role.permissions.append(perm)
    
    # Marketer: store permissions only
    for perm in store_permissions:
        if perm not in marketer_role.permissions:
            marketer_role.permissions.append(perm)
    
    # Viewer: read-only store permissions
    read_permission = next((p for p in store_permissions if p.action == "read"), None)
    if read_permission and read_permission not in viewer_role.permissions:
        viewer_role.permissions.append(read_permission)
    
    db.commit()
    print("Roles and permissions initialized successfully!")

def create_default_admin(db: Session):
    """Create a default admin user if it doesn't exist."""
    admin = db.query(User).filter(User.email == "admin@company.com").first()
    if not admin:
        admin = User(
            user_id="Admin",
            email="admin@company.com",
            password_hash=hash_password("TestPassword123!"),
            role_id="R001",
            status="active"
        )
        db.add(admin)
        db.commit()
        print("Default admin user created: admin@company.com / admin123")
    else:
        print("Default admin user already exists")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_roles_and_permissions(db)
        create_default_admin(db)
    finally:
        db.close()

