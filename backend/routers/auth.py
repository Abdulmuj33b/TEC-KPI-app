
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from config import settings
from database import get_connection
from security import CurrentUser, create_access_token, password_hash

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login")
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    # OAuth2 field "username" contains the user's email address.
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id, full_name, email, password_hash,
                   role, unit_id, is_active
            FROM users
            WHERE lower(email) = lower(%s)
            """,
            (form.username.strip(),),
        ).fetchone()

    if (
        user is None
        or not user["is_active"]
        or not password_hash.verify(
            form.password, user["password_hash"]
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_minutes * 60,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "unit_id": user["unit_id"],
        },
    }


@router.get("/me")
def get_my_account(user: CurrentUser):
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
        "unit_id": user["unit_id"],
    }
