
# TEC KPI API

from contextlib import asynccontextmanager
from routers.training import router as training_router
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import get_connection
from security import CurrentUser

from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.production import router as production_router


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(production_router)
app.include_router(training_router)

# --------------------------------------------------
# HEALTH CHECK ENDPOINTS
# --------------------------------------------------

@app.get("/api/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "service": "tec-kpi-api",
    }


@app.get("/api/health/database", tags=["Health"])
def database_health():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        )


# --------------------------------------------------
# UNIT MANAGEMENT
# --------------------------------------------------

@app.get("/api/units", tags=["Units"])
def list_units(user: CurrentUser):

    with get_connection() as conn:

        if user["role"] == "head_of_unit":

            rows = conn.execute(
                """
                SELECT id, name, unit_type
                FROM units
                WHERE id = %s
                """,
                (user["unit_id"],),
            ).fetchall()

        else:

            rows = conn.execute(
                """
                SELECT id, name, unit_type
                FROM units
                ORDER BY name
                """
            ).fetchall()

    return rows
