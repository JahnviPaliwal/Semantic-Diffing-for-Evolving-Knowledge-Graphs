"""Authentication API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.entities import User
from ..schemas.auth import RefreshRequest, TokenResponse, UserLogin, UserRegister, UserResponse
from ..services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account and receive authentication tokens."""
    AuthService.register_user(db, user_in)
    return AuthService.authenticate_user(db, user_in.email, user_in.password)


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email and password to receive JWT tokens."""
    return AuthService.authenticate_user(db, credentials.email, credentials.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_in: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a fresh access token."""
    return AuthService.refresh_token(db, refresh_in.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Retrieve profile of the currently authenticated user."""
    return current_user
