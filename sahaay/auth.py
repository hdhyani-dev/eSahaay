"""Authentication, password security and session management."""
import datetime
import bcrypt
from typing import Optional
from sqlalchemy.orm import Session
from sahaay.models import User
from sahaay.config import settings

def hash_password(password: str) -> str:
    """Hash a password securely using bcrypt."""
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def authenticate_user(db: Session, employee_id: str, password: str) -> Optional[User]:
    """Authenticate employee credentials against database."""
    user = db.query(User).filter(User.employee_id == employee_id, User.is_active == True).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    # Update last login non-blockingly
    try:
        user.last_login = datetime.datetime.utcnow()
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
    return user

def create_user(db: Session, employee_id: str, full_name: str, email: str, password: str, role: str, assigned_service: Optional[str] = None) -> User:
    """Create a new user with hashed password."""
    hashed = hash_password(password)
    user = User(
        employee_id=employee_id,
        full_name=full_name,
        email=email,
        hashed_password=hashed,
        role=role,
        assigned_service=assigned_service,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
