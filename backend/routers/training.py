
from datetime import date
import csv
import io
from typing import Literal

import psycopg
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from database import get_connection
from security import CurrentUser, require_roles

router = APIRouter(
    prefix="/api/training",
    tags=["Training Management"],
)


# --------------------------------------------------
# SCHEMAS
# --------------------------------------------------

class ProgrammeCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=200)
    description: str | None = None


class SkillCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    programme_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None


class FacilitatorCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=3, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)


class TrainingActivityCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    programme_id: int = Field(gt=0)
    skill_id: int = Field(gt=0)
    unit_id: int | None = Field(default=None, gt=0)

    start_date: date
    end_date: date

    level: str = Field(min_length=2, max_length=150)
    course_name: str = Field(min_length=2, max_length=200)

    enrolled: int = Field(default=0, ge=0)
    trained: int = Field(default=0, ge=0)
    completed: int = Field(default=0, ge=0)

    status: Literal[
        "draft", "ongoing", "completed", "cancelled"
    ] = "draft"

    facilitator_ids: list[int] = Field(default_factory=list)

    notes: str | None = None


# --------------------------------------------------
# TRAINING PROGRAMMES
# --------------------------------------------------

@router.get("/programmes")
def list_programmes(user: CurrentUser):

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, name, description, created_at
            FROM training_programmes
            ORDER BY name
            """
        ).fetchall()


@router.post("/programmes", status_code=201)
def create_programme(
    programme: ProgrammeCreate,
    admin: dict = Depends(require_roles("administrator")),
):

    try:
        with get_connection() as conn:
            return conn.execute(
                """
                INSERT INTO training_programmes (name, description)
                VALUES (%s, %s)
                RETURNING id, name, description, created_at
                """,
                (programme.name, programme.description),
            ).fetchone()

    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="This training programme already exists",
        )


# --------------------------------------------------
# TRAINING SKILLS
# --------------------------------------------------

@router.get("/skills")
def list_skills(
    user: CurrentUser,
    programme_id: int | None = Query(default=None, gt=0),
):

    with get_connection() as conn:
        if programme_id is None:
            rows = conn.execute(
                """
                SELECT
                    s.id, s.programme_id,
                    p.name AS programme_name,
                    s.name, s.description
                FROM training_skills s
                JOIN training_programmes p
                    ON p.id = s.programme_id
                ORDER BY p.name, s.name
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    s.id, s.programme_id,
                    p.name AS programme_name,
                    s.name, s.description
                FROM training_skills s
                JOIN training_programmes p
                    ON p.id = s.programme_id
                WHERE s.programme_id = %s
                ORDER BY s.name
                """,
                (programme_id,),
            ).fetchall()

    return rows


@router.post("/skills", status_code=201)
def create_skill(
    skill: SkillCreate,
    admin: dict = Depends(require_roles("administrator")),
):

    try:
        with get_connection() as conn:
            programme = conn.execute(
                "SELECT id FROM training_programmes WHERE id = %s",
                (skill.programme_id,),
            ).fetchone()

            if programme is None:
                raise HTTPException(
                    status_code=404,
                    detail="Training programme not found",
                )

            return conn.execute(
                """
                INSERT INTO training_skills (
                    programme_id, name, description
                )
                VALUES (%s, %s, %s)
                RETURNING id, programme_id, name, description
                """,
                (
                    skill.programme_id,
                    skill.name,
                    skill.description,
                ),
            ).fetchone()

    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="This skill already exists under the programme",
        )


# --------------------------------------------------
# FACILITATORS
# --------------------------------------------------

@router.get("/facilitators")
def list_facilitators(
    user: CurrentUser,
    active_only: bool = True,
):

    with get_connection() as conn:
        if active_only:
            rows = conn.execute(
                """
                SELECT id, full_name, email, phone, is_active
                FROM facilitators
                WHERE is_active = TRUE
                ORDER BY full_name
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, full_name, email, phone, is_active
                FROM facilitators
                ORDER BY full_name
                """
            ).fetchall()

    return rows


@router.post("/facilitators", status_code=201)
def create_facilitator(
    facilitator: FacilitatorCreate,
    admin: dict = Depends(require_roles("administrator")),
):

    try:
        with get_connection() as conn:
            return conn.execute(
                """
                INSERT INTO facilitators (
                    full_name, email, phone
                )
                VALUES (%s, %s, %s)
                RETURNING id, full_name, email, phone, is_active
                """,
                (
                    facilitator.full_name,
                    facilitator.email,
                    facilitator.phone,
                ),
            ).fetchone()

    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="A facilitator with this email already exists",
        )


# --------------------------------------------------
# TRAINING ACTIVITIES
# --------------------------------------------------

@router.get("/activities")
def list_training_activities(
    user: CurrentUser,
    unit_id: int | None = Query(default=None, gt=0),
    programme_id: int | None = Query(default=None, gt=0),
    start_date: date | None = None,
    end_date: date | None = None,
    activity_status: Literal[
        "draft", "ongoing", "completed", "cancelled"
    ] | None = None,
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
        conditions.append("a.unit_id = %s")
        params.append(user["unit_id"])

        if unit_id is not None and unit_id != user["unit_id"]:
            raise HTTPException(
                status_code=403,
                detail="You cannot access another unit's training records",
            )

    elif unit_id is not None:
        conditions.append("a.unit_id = %s")
        params.append(unit_id)

    if programme_id is not None:
        conditions.append("a.programme_id = %s")
        params.append(programme_id)

    if start_date is not None:
        conditions.append("a.start_date >= %s")
        params.append(start_date)

    if end_date is not None:
        conditions.append("a.end_date <= %s")
        params.append(end_date)

    if activity_status is not None:
        conditions.append("a.status = %s")
        params.append(activity_status)

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    query = f"""
        SELECT
            a.id,
            a.programme_id,
            p.name AS programme_name,
            a.skill_id,
            s.name AS skill_name,
            a.unit_id,
            u.name AS unit_name,
            a.start_date,
            a.end_date,
            a.level,
            a.course_name,
            a.enrolled,
            a.trained,
            a.completed,
            a.status,
            a.notes,
            a.created_at,
            COALESCE(
                json_agg(
                    json_build_object(
                        'id', f.id,
                        'full_name', f.full_name
                    )
                ) FILTER (WHERE f.id IS NOT NULL),
                '[]'
            ) AS facilitators
        FROM training_activities a
        JOIN training_programmes p
            ON p.id = a.programme_id
        JOIN training_skills s
            ON s.id = a.skill_id
        LEFT JOIN units u
            ON u.id = a.unit_id
        LEFT JOIN training_activity_facilitators af
            ON af.activity_id = a.id
        LEFT JOIN facilitators f
            ON f.id = af.facilitator_id
        {where_clause}
        GROUP BY
            a.id, p.name, s.name, u.name
        ORDER BY a.start_date DESC, a.id DESC
        LIMIT %s OFFSET %s
    """

    params.extend([limit, offset])

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


@router.post("/activities", status_code=201)
def create_training_activity(
    activity: TrainingActivityCreate,
    user: CurrentUser,
):

    if user["role"] not in ("administrator", "head_of_unit"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to create training activities",
        )

    if activity.start_date > activity.end_date:
        raise HTTPException(
            status_code=422,
            detail="End date cannot be before start date",
        )

    if activity.trained > activity.enrolled:
        raise HTTPException(
            status_code=422,
            detail="Trained cannot exceed enrolled",
        )

    if activity.completed > activity.trained:
        raise HTTPException(
            status_code=422,
            detail="Completed cannot exceed trained",
        )

    if user["role"] == "head_of_unit":
        if activity.unit_id != user["unit_id"]:
            raise HTTPException(
                status_code=403,
                detail="You can only manage training in your assigned unit",
            )

    try:
        with get_connection() as conn:

            skill = conn.execute(
                """
                SELECT id
                FROM training_skills
                WHERE id = %s AND programme_id = %s
                """,
                (activity.skill_id, activity.programme_id),
            ).fetchone()

            if skill is None:
                raise HTTPException(
                    status_code=422,
                    detail="The selected skill does not belong to the selected programme",
                )

            if activity.unit_id is not None:
                unit = conn.execute(
                    "SELECT id FROM units WHERE id = %s",
                    (activity.unit_id,),
                ).fetchone()

                if unit is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Training unit not found",
                    )

            facilitator_ids = list(dict.fromkeys(activity.facilitator_ids))

            if facilitator_ids:
                facilitators = conn.execute(
                    """
                    SELECT id
                    FROM facilitators
                    WHERE id = ANY(%s) AND is_active = TRUE
                    """,
                    (facilitator_ids,),
                ).fetchall()

                if len(facilitators) != len(facilitator_ids):
                    raise HTTPException(
                        status_code=422,
                        detail="One or more facilitators are invalid or inactive",
                    )

            row = conn.execute(
                """
                INSERT INTO training_activities (
                    programme_id, skill_id, unit_id,
                    start_date, end_date, level, course_name,
                    enrolled, trained, completed, status,
                    notes, created_by
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                RETURNING *
                """,
                (
                    activity.programme_id,
                    activity.skill_id,
                    activity.unit_id,
                    activity.start_date,
                    activity.end_date,
                    activity.level,
                    activity.course_name,
                    activity.enrolled,
                    activity.trained,
                    activity.completed,
                    activity.status,
                    activity.notes,
                    user["id"],
                ),
            ).fetchone()

            for facilitator_id in facilitator_ids:
                conn.execute(
                    """
                    INSERT INTO training_activity_facilitators (
                        activity_id, facilitator_id
                    )
                    VALUES (%s, %s)
                    """,
                    (row["id"], facilitator_id),
                )

        return {
            **row,
            "facilitator_ids": facilitator_ids,
        }

    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=422,
            detail="One of the referenced training records does not exist",
        )


# --------------------------------------------------
# CSV BULK IMPORT
# --------------------------------------------------

@router.post("/activities/import", status_code=200)
def import_training_activities(
    file: UploadFile = File(...),
    user: dict = Depends(require_roles("administrator")),
):
    """Import training activities from CSV; valid rows commit independently."""

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Upload a .csv file")

    raw = file.file.read()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV file exceeds the 5 MB limit")

    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=422,
            detail="CSV must be UTF-8 encoded. Re-save it as CSV UTF-8 from Excel or LibreOffice.",
        )

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise HTTPException(status_code=422, detail="CSV is empty or has no header row")

    headers = {h.strip().lower() for h in reader.fieldnames if h}
    required = {
        "start_date", "end_date", "course", "level", "skill",
        "enrolled", "trained", "completed",
    }
    missing = sorted(required - headers)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required columns: {', '.join(missing)}",
        )
    if not ({"programme", "programme_name"} & headers) and "level" not in headers:
        raise HTTPException(
            status_code=422,
            detail="CSV requires a programme column (or legacy level column containing the programme name)",
        )
    if not ({"facilitator_names", "facilitators"} & headers):
        raise HTTPException(
            status_code=422,
            detail="CSV requires facilitator_names or facilitators column",
        )

    def cell(row, *names):
        for name in names:
            value = row.get(name)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    def whole_number(row, name, line):
        value = cell(row, name)
        if not value.isdigit():
            raise ValueError(f"{name} must be a non-negative whole number")
        return int(value)

    imported, skipped, rejected = 0, 0, 0
    results = []

    with get_connection() as conn:
        for line, source_row in enumerate(reader, start=2):
            row = {
                (key or "").strip().lower(): (value or "").strip()
                for key, value in source_row.items()
            }
            if not any(row.values()):
                continue

            try:
                programme_name = cell(row, "programme", "programme_name")
                legacy_level = cell(row, "level")
                if not programme_name:
                    programme_name = legacy_level
                skill_name = cell(row, "skill")
                course_name = cell(row, "course", "course_name")
                level = cell(row, "student_level") or legacy_level or programme_name
                start = date.fromisoformat(cell(row, "start_date"))
                end = date.fromisoformat(cell(row, "end_date"))
                enrolled = whole_number(row, "enrolled", line)
                trained = whole_number(row, "trained", line)
                completed = whole_number(row, "completed", line)

                if not programme_name or not skill_name or not course_name or not level:
                    raise ValueError("programme, skill, course and level are required")
                if end < start:
                    raise ValueError("end_date cannot be earlier than start_date")
                if trained > enrolled:
                    raise ValueError("trained cannot exceed enrolled")
                if completed > trained:
                    raise ValueError("completed cannot exceed trained")

                status_text = (cell(row, "status") or "draft").lower()
                status_map = {
                    "draft": "draft",
                    "ongoing": "ongoing",
                    "in progress": "ongoing",
                    "completed": "completed",
                    "cancelled": "cancelled",
                    "submitted": "draft",
                }
                if status_text not in status_map:
                    raise ValueError("status must be draft, ongoing, completed or cancelled")
                status = status_map[status_text]

                programme = conn.execute(
                    "SELECT id FROM training_programmes WHERE LOWER(name) = LOWER(%s)",
                    (programme_name,),
                ).fetchone()
                if not programme:
                    raise ValueError(f"programme not found: {programme_name}")

                skill = conn.execute(
                    """
                    SELECT id FROM training_skills
                    WHERE programme_id = %s AND LOWER(name) = LOWER(%s)
                    """,
                    (programme["id"], skill_name),
                ).fetchone()
                if not skill:
                    raise ValueError(
                        f"skill '{skill_name}' not found under programme '{programme_name}'"
                    )

                unit_name = cell(row, "unit", "unit_name")
                unit_id = None
                if unit_name:
                    unit = conn.execute(
                        "SELECT id FROM units WHERE LOWER(name) = LOWER(%s)",
                        (unit_name,),
                    ).fetchone()
                    if not unit:
                        raise ValueError(f"unit not found: {unit_name}")
                    unit_id = unit["id"]

                raw_facilitators = cell(row, "facilitator_names", "facilitators")
                facilitator_names = [
                    name.strip() for name in raw_facilitators.split(";") if name.strip()
                ]
                # Legacy template used a numeric facilitator count. Preserve compatibility,
                # but only names can create actual facilitator assignments.
                if raw_facilitators.isdigit():
                    facilitator_names = []
                    legacy_facilitator_count = int(raw_facilitators)
                else:
                    legacy_facilitator_count = None

                facilitator_ids = []
                for name in facilitator_names:
                    facilitator = conn.execute(
                        """
                        SELECT id FROM facilitators
                        WHERE is_active = TRUE AND LOWER(full_name) = LOWER(%s)
                        """,
                        (name,),
                    ).fetchone()
                    if not facilitator:
                        raise ValueError(f"active facilitator not found: {name}")
                    facilitator_ids.append(facilitator["id"])

                facilitator_ids = list(dict.fromkeys(facilitator_ids))
                notes = cell(row, "notes")

                duplicate = conn.execute(
                    """
                    SELECT id FROM training_activities
                    WHERE programme_id = %s AND skill_id = %s
                      AND unit_id IS NOT DISTINCT FROM %s
                      AND start_date = %s AND end_date = %s
                      AND LOWER(course_name) = LOWER(%s)
                    LIMIT 1
                    """,
                    (
                        programme["id"], skill["id"], unit_id,
                        start, end, course_name,
                    ),
                ).fetchone()
                if duplicate:
                    skipped += 1
                    results.append({
                        "row": line, "status": "skipped",
                        "reason": f"Duplicate of existing activity ID {duplicate['id']}",
                    })
                    continue

                with conn.transaction():
                    activity = conn.execute(
                        """
                        INSERT INTO training_activities (
                            programme_id, skill_id, unit_id, start_date, end_date,
                            level, course_name, enrolled, trained, completed,
                            status, notes, created_by
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            programme["id"], skill["id"], unit_id, start, end,
                            level, course_name, enrolled, trained, completed,
                            status, notes or None, user["id"],
                        ),
                    ).fetchone()

                    for facilitator_id in facilitator_ids:
                        conn.execute(
                            """
                            INSERT INTO training_activity_facilitators
                                (activity_id, facilitator_id)
                            VALUES (%s, %s)
                            """,
                            (activity["id"], facilitator_id),
                        )

                imported += 1
                message = "Imported"
                if legacy_facilitator_count is not None and legacy_facilitator_count:
                    message += (
                        f"; legacy facilitator count {legacy_facilitator_count} recorded "
                        "as a count only, no named facilitator assignments"
                    )
                results.append({
                    "row": line, "status": "imported",
                    "activity_id": activity["id"], "reason": message,
                })

            except (ValueError, TypeError) as exc:
                rejected += 1
                results.append({
                    "row": line, "status": "rejected", "reason": str(exc),
                })

    return {
        "filename": file.filename,
        "total_rows": imported + skipped + rejected,
        "imported": imported,
        "skipped": skipped,
        "rejected": rejected,
        "results": results,
    }
