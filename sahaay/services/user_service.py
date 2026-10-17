"""User management and profile queries service."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sahaay.models import User
from sahaay.auth import hash_password

def list_users(db: Session) -> List[User]:
    """List all registered system users."""
    return db.query(User).order_by(User.id.asc()).all()

def get_user_by_employee_id(db: Session, employee_id: str) -> Optional[User]:
    """Find user by unique employee ID."""
    return db.query(User).filter(User.employee_id == employee_id).first()

def update_user_password(db: Session, employee_id: str, new_password: str) -> bool:
    """Update employee password with secure hash."""
    user = get_user_by_employee_id(db, employee_id)
    if not user:
        return False
    user.hashed_password = hash_password(new_password)
    db.commit()
    return True
