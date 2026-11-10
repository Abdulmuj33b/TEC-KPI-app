
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from database import get_connection
from security import CurrentUser

router = APIRouter(prefix="/api/production", tags=["Production Management"])


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


@router.get("")
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


@router.get("/{record_id}")
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
        raise HTTPException(
            status_code=404,
            detail="Production record not found",
        )

    return row


@router.post("", status_code=201)
def create_production_record(
    record: ProductionCreate,
    user: CurrentUser,
):
    if user["role"] not in ("administrator", "head_of_unit"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to create production records",
        )

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
