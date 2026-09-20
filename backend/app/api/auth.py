import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
)
from backend.app.services.user import (
    create_user,
    authenticate_user,
)
from backend.app.utils.security import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# Basic login rate limiting
_login_attempts = {}

MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300


@router.post(
    "/register",
    response_model=UserResponse,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    return create_user(db, user)


@router.post(
    "/login",
    response_model=Token,
)
def login(
    request: Request,
    user: UserLogin,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"{client_ip}:{user.email.lower().strip()}"

    current_time = time.time()

    attempts = _login_attempts.get(rate_limit_key, [])

    attempts = [
        attempt
        for attempt in attempts
        if current_time - attempt < LOGIN_WINDOW_SECONDS
    ]

    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
        )

    db_user = authenticate_user(
        db,
        user.email,
        user.password,
    )

    if not db_user:
        attempts.append(current_time)
        _login_attempts[rate_limit_key] = attempts

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    _login_attempts.pop(rate_limit_key, None)

    token = create_access_token(
        {
            "sub": db_user.email,
            "user_id": db_user.id,
            "role": db_user.role,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }