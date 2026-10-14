"""
Authentication and identity management service.
Handles registration, login, token issuance, refresh, and current user retrieval.
"""
from datetime import timedelta
from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.exceptions import BadRequestException, UnauthorizedException
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from ..models.entities import User
from ..schemas.auth import TokenResponse, UserRegister, UserResponse


class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserRegister) -> User:
        existing = db.query(User).filter(User.email == user_in.email).first()
        if existing:
            raise BadRequestException(f"User with email '{user_in.email}' already exists.")

        user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> TokenResponse:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedException("User account is inactive.")

        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    def refresh_token(db: Session, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid or expired refresh token.")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid refresh token payload.")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive.")

        new_access = create_access_token({"sub": str(user.id), "email": user.email})
        new_refresh = create_refresh_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            user=UserResponse.model_validate(user),
        )


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that extracts the authenticated user from the Bearer token, or returns default user for frictionless access."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user and user.is_active:
                    return user

    # Default user for frictionless access without login
    default_user = db.query(User).filter(User.email == "analyst@enterprise.internal").first()
    if not default_user:
        default_user = User(
            email="analyst@enterprise.internal",
            hashed_password="frictionless_default_hash",
            is_active=True,
            is_superuser=True,
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)

    return default_user
