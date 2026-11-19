from datetime import date
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from database import get_connection
from security import CurrentUser

router = APIRouter(prefix="/api/research", tags=["Research and Development"])


class ProjectCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    unit_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=2, max_length=250)
    description: str | None = None
    lead_name: str | None = Field(default=None, max_length=150)
    start_date: date | None = None
    end_date: date | None = None
    status: Literal["proposed", "ongoing", "completed", "suspended", "cancelled"] = "proposed"
    budget: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    notes: str | None = None


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    unit_id: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, min_length=2, max_length=250)
    description: str | None = None
    lead_name: str | None = Field(default=None, max_length=150)
    start_date: date | None = None
    end_date: date | None = None
    status: Literal["proposed", "ongoing", "completed", "suspended", "cancelled"] | None = None
    budget: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    notes: str | None = None


class ActivityCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    activity_date: date
    title: str = Field(min_length=2, max_length=250)
    description: str | None = None
    status: Literal["planned", "ongoing", "completed", "cancelled"] = "planned"
    percent_complete: int = Field(default=0, ge=0, le=100)


class ActivityUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    activity_date: date | None = None
    title: str | None = Field(default=None, min_length=2, max_length=250)
    description: str | None = None
    status: Literal["planned", "ongoing", "completed", "cancelled"] | None = None
    percent_complete: int | None = Field(default=None, ge=0, le=100)


class OutputCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    output_type: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=250)
    output_date: date | None = None
    description: str | None = None


class ExpenditureCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    expenditure_date: date
    category: str = Field(min_length=2, max_length=100)
    description: str | None = None
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    reference: str | None = Field(default=None, max_length=120)


def _require_project_edit(user: dict, project: dict):
    """Enforce project-level R&D permissions."""
    role = user["role"]
    if role == "administrator":
        return
    if role == "research_officer" and project["unit_id"] is None:
        return
    if (
        role == "head_of_unit"
        and project["unit_id"] is not None
        and project["unit_id"] == user["unit_id"]
    ):
        return
    raise HTTPException(
        status_code=403,
        detail="You do not have permission to modify this research project",
    )


def _require_project_creation(user: dict, unit_id: int | None):
    role = user["role"]
    if role == "administrator":
        return
    if role == "research_officer" and unit_id is None:
        return
    if role == "head_of_unit" and unit_id == user["unit_id"]:
        return
    raise HTTPException(
        status_code=403,
        detail="You cannot create a research project with this unit assignment",
    )


def _project(conn, project_id: int, user: dict):
    row = conn.execute(
        """
        SELECT p.*, u.name AS unit_name
        FROM research_projects p
        LEFT JOIN units u ON u.id = p.unit_id
        WHERE p.id = %s
        """,
        (project_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Research project not found")
    if user["role"] == "head_of_unit" and row["unit_id"] != user["unit_id"]:
        raise HTTPException(status_code=404, detail="Research project not found")
    return row


def _validate_unit(conn, unit_id):
    if unit_id is None:
        return
    if conn.execute("SELECT id FROM units WHERE id = %s", (unit_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Unit not found")


@router.get("/projects")
def list_projects(
    user: CurrentUser,
    unit_id: int | None = Query(default=None, gt=0),
    status: Literal["proposed", "ongoing", "completed", "suspended", "cancelled"] | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    conditions, params = [], []
    if user["role"] == "head_of_unit":
        if unit_id is not None and unit_id != user["unit_id"]:
            raise HTTPException(status_code=403, detail="You cannot access another unit's research")
        conditions.append("p.unit_id = %s")
        params.append(user["unit_id"])
    elif unit_id is not None:
        conditions.append("p.unit_id = %s")
        params.append(unit_id)
    if status:
        conditions.append("p.status = %s")
        params.append(status)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params.extend([limit, offset])
    with get_connection() as conn:
        return conn.execute(
            f"""
            SELECT p.id, p.unit_id, u.name AS unit_name, p.title, p.description,
                   p.lead_name, p.start_date, p.end_date, p.status, p.budget,
                   p.expenditure, p.notes, p.created_at, p.updated_at
            FROM research_projects p
            LEFT JOIN units u ON u.id = p.unit_id
            {where}
            ORDER BY p.created_at DESC, p.id DESC
            LIMIT %s OFFSET %s
            """,
            params,
        ).fetchall()


@router.post("/projects", status_code=201)
def create_project(project: ProjectCreate, user: CurrentUser):
    _require_project_creation(user, project.unit_id)
    if project.start_date and project.end_date and project.end_date < project.start_date:
        raise HTTPException(status_code=422, detail="end_date cannot be earlier than start_date")
    with get_connection() as conn:
        _validate_unit(conn, project.unit_id)
        return conn.execute(
            """
            INSERT INTO research_projects
                (unit_id, title, description, lead_name, start_date, end_date,
                 status, budget, notes, created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
            """,
            (project.unit_id, project.title, project.description, project.lead_name,
             project.start_date, project.end_date, project.status, project.budget,
             project.notes, user["id"]),
        ).fetchone()


@router.get("/projects/{project_id}")
def get_project(project_id: int, user: CurrentUser):
    with get_connection() as conn:
        return _project(conn, project_id, user)


@router.patch("/projects/{project_id}")
def update_project(project_id: int, changes: ProjectUpdate, user: CurrentUser):
    data = changes.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=422, detail="No project fields supplied")
    with get_connection() as conn:
        existing = _project(conn, project_id, user)
        _require_project_edit(user, existing)
        if "unit_id" in data:
            if user["role"] == "research_officer" and data["unit_id"] is not None:
                raise HTTPException(status_code=403, detail="R&D Officers can manage central projects only")
            if user["role"] == "head_of_unit" and data["unit_id"] != user["unit_id"]:
                raise HTTPException(status_code=403, detail="You cannot move a project outside your assigned unit")
            _validate_unit(conn, data["unit_id"])
        start = data.get("start_date", existing["start_date"])
        end = data.get("end_date", existing["end_date"])
        if start and end and end < start:
            raise HTTPException(status_code=422, detail="end_date cannot be earlier than start_date")
        allowed = {"unit_id", "title", "description", "lead_name", "start_date",
                   "end_date", "status", "budget", "notes"}
        assignments = ", ".join(f"{key} = %s" for key in data if key in allowed)
        values = [data[key] for key in data if key in allowed]
        values.append(project_id)
        return conn.execute(
            f"UPDATE research_projects SET {assignments}, updated_at = NOW() WHERE id = %s RETURNING *",
            values,
        ).fetchone()


@router.get("/projects/{project_id}/activities")
def list_activities(project_id: int, user: CurrentUser):
    with get_connection() as conn:
        _project(conn, project_id, user)
        return conn.execute(
            """SELECT id, project_id, activity_date, title, description, status,
                      percent_complete, created_by, created_at, updated_at
               FROM research_activities WHERE project_id = %s
               ORDER BY activity_date DESC, id DESC""",
            (project_id,),
        ).fetchall()


@router.post("/projects/{project_id}/activities", status_code=201)
def create_activity(project_id: int, activity: ActivityCreate, user: CurrentUser):
    with get_connection() as conn:
        project = _project(conn, project_id, user)
        _require_project_edit(user, project)
        return conn.execute(
            """INSERT INTO research_activities
                   (project_id, activity_date, title, description, status, percent_complete, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (project_id, activity.activity_date, activity.title, activity.description,
             activity.status, activity.percent_complete, user["id"]),
        ).fetchone()


@router.patch("/activities/{activity_id}")
def update_activity(activity_id: int, changes: ActivityUpdate, user: CurrentUser):
    data = changes.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=422, detail="No activity fields supplied")
    with get_connection() as conn:
        row = conn.execute(
            """SELECT a.id, a.project_id FROM research_activities a
               JOIN research_projects p ON p.id = a.project_id WHERE a.id = %s""",
            (activity_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Research activity not found")
        project = _project(conn, row["project_id"], user)
        _require_project_edit(user, project)
        assignments = ", ".join(f"{key} = %s" for key in data)
        values = list(data.values()) + [activity_id]
        return conn.execute(
            f"UPDATE research_activities SET {assignments}, updated_at = NOW() WHERE id = %s RETURNING *",
            values,
        ).fetchone()


@router.get("/projects/{project_id}/outputs")
def list_outputs(project_id: int, user: CurrentUser):
    with get_connection() as conn:
        _project(conn, project_id, user)
        return conn.execute(
            """SELECT id, project_id, output_type, title, output_date, description, created_at
               FROM research_outputs WHERE project_id = %s ORDER BY output_date DESC NULLS LAST, id DESC""",
            (project_id,),
        ).fetchall()


@router.post("/projects/{project_id}/outputs", status_code=201)
def create_output(project_id: int, output: OutputCreate, user: CurrentUser):
    with get_connection() as conn:
        project = _project(conn, project_id, user)
        _require_project_edit(user, project)
        return conn.execute(
            """INSERT INTO research_outputs (project_id, output_type, title, output_date, description)
               VALUES (%s,%s,%s,%s,%s) RETURNING *""",
            (project_id, output.output_type, output.title, output.output_date, output.description),
        ).fetchone()


@router.get("/projects/{project_id}/expenditures")
def list_expenditures(project_id: int, user: CurrentUser):
    with get_connection() as conn:
        _project(conn, project_id, user)
        return conn.execute(
            """SELECT id, project_id, expenditure_date, category, description,
                      amount, reference, recorded_by, created_at
               FROM research_expenditures WHERE project_id = %s
               ORDER BY expenditure_date DESC, id DESC""",
            (project_id,),
        ).fetchall()


@router.post("/projects/{project_id}/expenditures", status_code=201)
def create_expenditure(project_id: int, item: ExpenditureCreate, user: CurrentUser):
    with get_connection() as conn:
        project = _project(conn, project_id, user)
        _require_project_edit(user, project)
        new_total = Decimal(project["expenditure"]) + item.amount
        conn.execute(
            """INSERT INTO research_expenditures
                   (project_id, expenditure_date, category, description, amount, reference, recorded_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (project_id, item.expenditure_date, item.category, item.description,
             item.amount, item.reference, user["id"]),
        )
        conn.execute(
            "UPDATE research_projects SET expenditure = %s, updated_at = NOW() WHERE id = %s",
            (new_total, project_id),
        )
        return conn.execute(
            """SELECT id, project_id, expenditure_date, category, description,
                      amount, reference, recorded_by, created_at
               FROM research_expenditures WHERE project_id = %s
               ORDER BY id DESC LIMIT 1""",
            (project_id,),
        ).fetchone()
