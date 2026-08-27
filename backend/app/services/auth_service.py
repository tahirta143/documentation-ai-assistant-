import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    def register(self, db: Session, user_in: UserCreate) -> Token:
        existing = user_repository.get_by_email(db, user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        hashed = hash_password(user_in.password)
        user = user_repository.create(db, user_in.email, hashed)
        logger.info("Registered new user id=%d email=%s", user.id, user.email)

        token_str = create_access_token(subject=user.id)
        return Token(
            access_token=token_str,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    def login(self, db: Session, user_in: UserLogin) -> Token:
        user = user_repository.get_by_email(db, user_in.email)
        if not user or not verify_password(user_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )

        token_str = create_access_token(subject=user.id)
        return Token(
            access_token=token_str,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )


auth_service = AuthService()
