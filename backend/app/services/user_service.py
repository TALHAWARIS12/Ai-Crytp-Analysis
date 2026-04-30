from sqlalchemy.orm import Session
from app.db.models import User
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def get_or_create_user(db: Session, telegram_id: str, username: Optional[str] = None) -> User:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if not user:
            user = User(
                telegram_id=str(telegram_id),
                username=username,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {telegram_id} (@{username})")
        else:
            if username and user.username != username:
                user.username = username
                db.commit()
                db.refresh(user)
        return user

    @staticmethod
    def toggle_alerts(db: Session, telegram_id: str, enabled: bool) -> bool:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if user:
            user.alerts_enabled = enabled
            db.commit()
            return True
        return False

    @staticmethod
    def get_alert_recipients(db: Session) -> list[User]:
        return db.query(User).filter(User.alerts_enabled == True, User.telegram_id != None).all()

    @staticmethod
    def update_last_alert_time(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_alert_at = datetime.utcnow()
            db.commit()

user_service = UserService()
