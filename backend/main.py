from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated

import jwt
import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings
from psycopg.rows import dict_row


class Settings(BaseSettings):
    database_url: str = (
        "postgresql://tec_kpi:development_only@db:5432/tec_kpi"
    )
    jwt_secret_key: str
    access_token_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_connection():
    return psycopg.connect(
        settings.database_url,
        connect_timeout=5,
        row_factory=dict_row,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        app.state.database_ready = True
    except Exception as exc:
        app.state.database_ready = False
        print(f"Database connection failed: {exc}")
    yield


app = FastAPI(
    title="TEC KPI API",
    description="Institutional performance tracking API",
    version="0.3.0",
    lifespan=lifespan,
)


class ProductionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    unit_id: int = Field(gt=0)
    record_date: date
    product_name: str = Field(min_length=1, max_length=200)
    quantity: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    unit_of_measure: str = Field(min_length=1, max_length=40)
    unit_cost: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=14, decimal_places=2
    )
    total_cost: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    revenue: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=14, decimal_places=2
    )
    notes: str | None = None


def create_access_token(user: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "role": user["role"],
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm="HS256",
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired login token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "iat"]},
        )
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise unauthorized

    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id, full_name, email, role, unit_id, is_active
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        ).fetchone()

    if user is None or not user["is_active"]:
        raise unauthorized

    return user


CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_roles(*allowed_roles: str):
    def check_role(user: CurrentUser) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user

    return check_role


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "tec-kpi-api"}


@app.get("/api/health/database")
def database_health():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        )


@app.post("/api/auth/login")
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    # OAuth2 form field "username" contains the user's email address.
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
        or not password_hash.verify(form.password, user["password_hash"])
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


@app.get("/api/auth/me")
def get_my_account(user: CurrentUser):
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
        "unit_id": user["unit_id"],
    }


@app.get("/api/units")
def list_units(user: CurrentUser):
    with get_connection() as conn:
        if user["role"] == "head_of_unit":
            rows = conn.execute(
                "SELECT id, name, unit_type FROM units WHERE id = %s",
                (user["unit_id"],),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, unit_type FROM units ORDER BY name"
            ).fetchall()
    return rows


@app.get("/api/production")
def list_production(
    user: CurrentUser,
    unit_id: int | None = Query(default=None, gt=0),
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=422,
            detail="end_date must be on or after start_date",
        )

    conditions = []
    params = []

    if user["role"] == "head_of_unit":
        # Never trust the requested unit ID for authorization.
        conditions.append("p.unit_id = %s")
        params.append(user["unit_id"])

        if unit_id is not None and unit_id != user["unit_id"]:
            raise HTTPException(
                status_code=403,
                detail="You cannot access another unit's records",
            )
    elif unit_id is not None:
        conditions.append("p.unit_id = %s")
        params.append(unit_id)

    if start_date is not None:
        conditions.append("p.record_date >= %s")
        params.append(start_date)

    if end_date is not None:
        conditions.append("p.record_date <= %s")
        params.append(end_date)

    where_clause = (
        "WHERE " + " AND ".join(conditions) if conditions else ""
    )

    query = f"""
        SELECT
            p.id, p.unit_id, u.name AS unit_name,
            p.record_date, p.product_name, p.quantity,
            p.unit_of_measure, p.unit_cost, p.total_cost,
            p.revenue, p.notes, p.created_at, p.updated_at
        FROM production_records AS p
        JOIN units AS u ON u.id = p.unit_id
        {where_clause}
        ORDER BY p.record_date DESC, p.id DESC
        LIMIT %s OFFSET %s
    """

    params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return rows


@app.get("/api/production/{record_id}")
def get_production_record(record_id: int, user: CurrentUser):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                p.id, p.unit_id, u.name AS unit_name,
                p.record_date, p.product_name, p.quantity,
                p.unit_of_measure, p.unit_cost, p.total_cost,
                p.revenue, p.notes, p.created_at, p.updated_at
            FROM production_records AS p
            JOIN units AS u ON u.id = p.unit_id
            WHERE p.id = %s
            """,
            (record_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Production record not found",
        )

    if (
        user["role"] == "head_of_unit"
        and row["unit_id"] != user["unit_id"]
    ):
        # Return 404 rather than disclose that another unit's record exists.
        raise HTTPException(
            status_code=404,
            detail="Production record not found",
        )

    return row


@app.post("/api/production", status_code=201)
def create_production_record(
    record: ProductionCreate,
    user: CurrentUser,
):
    if (
        user["role"] == "head_of_unit"
        and record.unit_id != user["unit_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only create records for your assigned unit",
        )

    with get_connection() as conn:
        unit = conn.execute(
            "SELECT id FROM units WHERE id = %s",
            (record.unit_id,),
        ).fetchone()

        if unit is None:
            raise HTTPException(
                status_code=404,
                detail="Production unit not found",
            )

        total_cost = record.total_cost
        if total_cost is None:
            total_cost = (
                record.quantity * record.unit_cost
            ).quantize(Decimal("0.01"))

        row = conn.execute(
            """
            INSERT INTO production_records (
                unit_id, record_date, product_name,
                quantity, unit_of_measure, unit_cost,
                total_cost, revenue, notes, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING
                id, unit_id, record_date, product_name,
                quantity, unit_of_measure, unit_cost,
                total_cost, revenue, notes, created_at
            """,
            (
                record.unit_id,
                record.record_date,
                record.product_name,
                record.quantity,
                record.unit_of_measure,
                record.unit_cost,
                total_cost,
                record.revenue,
                record.notes,
                user["id"],
            ),
        ).fetchone()

    return row
