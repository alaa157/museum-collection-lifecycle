from sqlalchemy import select
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.role import Permission, Role
from app.models.user import User
from app.security.passwords import hash_password


settings = get_settings()

ROLE_DEFINITIONS = {
    "ADMIN": "Full system administration",
    "CURATOR": "Collection and exhibition management",
    "CONSERVATOR": "Condition and conservation management",
    "REGISTRAR": "Registration, acquisition, movement and loan management",
    "RESEARCHER": "Research and controlled collection access",
    "VIEWER": "Read-only collection access",
}

PERMISSIONS = {
    "users:read": "View users",
    "users:create": "Create users",
    "users:update": "Update users",
    "users:delete": "Delete users",
    "roles:read": "View roles",
    "roles:update": "Update role assignments",
    "collection:read": "View collection",
    "collection:create": "Create collection items",
    "collection:update": "Update collection items",
    "collection:delete": "Delete collection items",
    "collection:move": "Move collection items",
    "conservation:read": "View conservation records",
    "conservation:write": "Manage conservation records",
    "loans:read": "View loans",
    "loans:write": "Manage loans",
    "audit:read": "View audit records",
    "settings:manage": "Manage system settings",
}

ROLE_PERMISSIONS = {
    "ADMIN": list(PERMISSIONS),
    "CURATOR": [
        "collection:read",
        "collection:create",
        "collection:update",
        "collection:move",
        "conservation:read",
        "loans:read",
    ],
    "CONSERVATOR": [
        "collection:read",
        "conservation:read",
        "conservation:write",
    ],
    "REGISTRAR": [
        "collection:read",
        "collection:create",
        "collection:update",
        "collection:move",
        "loans:read",
        "loans:write",
    ],
    "RESEARCHER": [
        "collection:read",
        "conservation:read",
        "loans:read",
    ],
    "VIEWER": [
        "collection:read",
    ],
}


def seed():
    db = SessionLocal()
    try:
        permission_objects: dict[str, Permission] = {}

        for code, description in PERMISSIONS.items():
            permission = db.scalar(
                select(Permission).where(Permission.code == code)
            )
            if not permission:
                permission = Permission(code=code, description=description)
                db.add(permission)
                db.flush()
            permission_objects[code] = permission

        role_objects: dict[str, Role] = {}

        for name, description in ROLE_DEFINITIONS.items():
            role = db.scalar(select(Role).where(Role.name == name))
            if not role:
                role = Role(name=name, description=description, is_system_role=True)
                db.add(role)
                db.flush()

            role.permissions = [
                permission_objects[code]
                for code in ROLE_PERMISSIONS[name]
            ]
            role_objects[name] = role

        admin = db.scalar(
            select(User).where(User.email == settings.seed_admin_email.lower())
        )

        if not admin:
            admin = User(
                email=settings.seed_admin_email.lower(),
                password_hash=hash_password(settings.seed_admin_password),
                first_name=settings.seed_admin_first_name,
                last_name=settings.seed_admin_last_name,
                is_active=True,
                is_verified=True,
                roles=[role_objects["ADMIN"]],
            )
            db.add(admin)
        else:
            admin.roles = [role_objects["ADMIN"]]
            admin.is_active = True

        db.commit()
        print(f"Seed completed. Admin: {settings.seed_admin_email}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
