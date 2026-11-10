
import psycopg
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from database import get_connection
from security import require_roles

router = APIRouter(prefix="/api/users", tags=["User Management"])


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: Literal["director", "administrator", "head_of_unit"]
    unit_id: int | None = Field(default=None, gt=0)


@router.post("", status_code=201)
def create_user(
    new_user: UserCreate,
    admin: dict = Depends(require_roles("administrator")),
):
    if new_user.role == "head_of_unit" and new_user.unit_id is None:
        raise HTTPException(
            status_code=422,
            detail="A Head of Unit must be assigned to a unit",
        )

    if (
        new_user.role in ("director", "administrator")
        and new_user.unit_id is not None
    ):
        raise HTTPException(
            status_code=422,
            detail="Director and Administrator accounts cannot be assigned to a unit",
        )

    from security import password_hash

    hashed_password = password_hash.hash(new_user.password)

    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                INSERT INTO users (
                    full_name, email, password_hash, role, unit_id
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, full_name, email, role, unit_id, is_active
                """,
                (
                    new_user.full_name,
                    new_user.email.lower(),
                    hashed_password,
                    new_user.role,
                    new_user.unit_id,
                ),
            ).fetchone()

        return row

    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        )
