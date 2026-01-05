from sqlalchemy.orm import Session
from database import SessionLocal
from models import Store, Service, User, Role, Permission, StoreType, StoreStatus
from auth import hash_password
from init_db import init_roles_and_permissions

def seed_test_stores(db: Session, count: int = 20):
    """Seed test stores for testing."""
    stores = []
    base_lat, base_lon = 42.3601, -71.0589  # Boston coordinates
    
    for i in range(1, count + 1):
        store = Store(
            store_id=f"S{i:04d}",
            name=f"Test Store {i}",
            store_type=StoreType.regular if i % 2 == 0 else StoreType.flagship,
            status=StoreStatus.active if i % 10 != 0 else StoreStatus.inactive,
            latitude=base_lat + (i * 0.01),
            longitude=base_lon + (i * 0.01),
            address_street=f"{i * 100} Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code=f"0210{i % 10}",
            address_country="USA",
            phone=f"617-555-{i:04d}",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="09:00-21:00",
            hours_sun="10:00-20:00"
        )
        
        # Add some services
        if i % 3 == 0:
            service = db.query(Service).filter(Service.name == "pharmacy").first()
            if service:
                store.services.append(service)
        
        stores.append(store)
        db.add(store)
    
    db.commit()
    print(f"Created {count} test stores")
    return stores

def seed_test_users(db: Session):
    """Seed test users with different roles."""
    # Ensure roles exist
    init_roles_and_permissions(db)
    
    # Get roles
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    marketer_role = db.query(Role).filter(Role.name == "marketer").first()
    viewer_role = db.query(Role).filter(Role.name == "viewer").first()
    
    # Create test users
    users = [
        User(
            user_id="U001",
            email="admin@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id=admin_role.role_id,
            status="active"
        ),
        User(
            user_id="U002",
            email="marketer@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id=marketer_role.role_id,
            status="active"
        ),
        User(
            user_id="U003",
            email="viewer@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id=viewer_role.role_id,
            status="active"
        )
    ]
    
    for user in users:
        existing = db.query(User).filter(User.email == user.email).first()
        if not existing:
            db.add(user)
    
    db.commit()
    print("Created test users:")
    print("  Admin: admin@test.com / TestPassword123!")
    print("  Marketer: marketer@test.com / TestPassword123!")
    print("  Viewer: viewer@test.com / TestPassword123!")

def seed_test_services(db: Session):
    """Seed test services."""
    services_data = [
        {"service_id": "SVC_pharmacy", "name": "pharmacy"},
        {"service_id": "SVC_pickup", "name": "pickup"},
        {"service_id": "SVC_returns", "name": "returns"},
        {"service_id": "SVC_optical", "name": "optical"},
        {"service_id": "SVC_photo_printing", "name": "photo_printing"},
        {"service_id": "SVC_gift_wrapping", "name": "gift_wrapping"},
        {"service_id": "SVC_automotive", "name": "automotive"},
        {"service_id": "SVC_garden_center", "name": "garden_center"}
    ]
    
    for service_data in services_data:
        service = db.query(Service).filter(Service.service_id == service_data["service_id"]).first()
        if not service:
            service = Service(**service_data)
            db.add(service)
    
    db.commit()
    print("Created test services")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        print("Seeding test data...")
        seed_test_services(db)
        seed_test_users(db)
        seed_test_stores(db, count=20)
        print("Test data seeding completed!")
    finally:
        db.close()

