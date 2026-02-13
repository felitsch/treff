"""Student CRUD routes."""

from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.student import Student
from app.models.asset import Asset

router = APIRouter()


# --- Pydantic Schemas ---

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    country: str = Field(..., min_length=1, max_length=100)
    city: Optional[str] = None
    school_name: Optional[str] = None
    host_family_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    profile_image_id: Optional[int] = None
    bio: Optional[str] = None
    fun_facts: Optional[str] = None  # JSON array as string
    status: str = Field(default="active", pattern="^(active|completed|upcoming)$")


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    country: Optional[str] = Field(None, min_length=1, max_length=100)
    city: Optional[str] = None
    school_name: Optional[str] = None
    host_family_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    profile_image_id: Optional[int] = None
    bio: Optional[str] = None
    fun_facts: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|upcoming)$")


# --- Helper ---

def student_to_dict(student: Student, profile_image_url: Optional[str] = None) -> dict:
    """Convert Student model to plain dict."""
    return {
        "id": student.id,
        "user_id": student.user_id,
        "name": student.name,
        "country": student.country,
        "city": student.city,
        "school_name": student.school_name,
        "host_family_name": student.host_family_name,
        "start_date": student.start_date.isoformat() if student.start_date else None,
        "end_date": student.end_date.isoformat() if student.end_date else None,
        "profile_image_id": student.profile_image_id,
        "profile_image_url": profile_image_url,
        "bio": student.bio,
        "fun_facts": student.fun_facts,
        "status": student.status,
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "updated_at": student.updated_at.isoformat() if student.updated_at else None,
    }


async def _get_profile_image_url(db: AsyncSession, profile_image_id: Optional[int]) -> Optional[str]:
    """Resolve profile image ID to URL."""
    if not profile_image_id:
        return None
    result = await db.execute(select(Asset).where(Asset.id == profile_image_id))
    asset = result.scalar_one_or_none()
    if asset:
        return f"/uploads/assets/{asset.filename}"
    return None


# --- Endpoints ---

@router.get("")
async def list_students(
    country: Optional[str] = None,
    status: Optional[str] = None,
    start_date_from: Optional[date] = Query(None, description="Filter by start_date >= this date"),
    start_date_to: Optional[date] = Query(None, description="Filter by start_date <= this date"),
    search: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List students with optional filters (country, status, date_range, search)."""
    query = select(Student).where(Student.user_id == user_id)

    if country:
        query = query.where(Student.country == country)
    if status:
        query = query.where(Student.status == status)
    if start_date_from:
        query = query.where(Student.start_date >= start_date_from)
    if start_date_to:
        query = query.where(Student.start_date <= start_date_to)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Student.name.ilike(search_term))
            | (Student.city.ilike(search_term))
            | (Student.school_name.ilike(search_term))
            | (Student.host_family_name.ilike(search_term))
            | (Student.bio.ilike(search_term))
        )

    result = await db.execute(query.order_by(Student.created_at.desc()))
    students = result.scalars().all()

    # Resolve profile image URLs
    items = []
    for s in students:
        img_url = await _get_profile_image_url(db, s.profile_image_id)
        items.append(student_to_dict(s, img_url))

    return items


@router.get("/{student_id}")
async def get_student(
    student_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single student by ID."""
    result = await db.execute(
        select(Student).where(
            and_(Student.id == student_id, Student.user_id == user_id)
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    img_url = await _get_profile_image_url(db, student.profile_image_id)
    return student_to_dict(student, img_url)


@router.post("", status_code=201)
async def create_student(
    data: StudentCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new student."""
    # Validate profile_image_id if provided
    if data.profile_image_id:
        result = await db.execute(
            select(Asset).where(
                and_(Asset.id == data.profile_image_id, Asset.user_id == user_id)
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Profile image not found")

    student = Student(
        user_id=user_id,
        name=data.name,
        country=data.country,
        city=data.city,
        school_name=data.school_name,
        host_family_name=data.host_family_name,
        start_date=data.start_date,
        end_date=data.end_date,
        profile_image_id=data.profile_image_id,
        bio=data.bio,
        fun_facts=data.fun_facts,
        status=data.status,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)

    img_url = await _get_profile_image_url(db, student.profile_image_id)
    return student_to_dict(student, img_url)


@router.put("/{student_id}")
async def update_student(
    student_id: int,
    data: StudentUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing student."""
    result = await db.execute(
        select(Student).where(
            and_(Student.id == student_id, Student.user_id == user_id)
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Validate profile_image_id if provided
    if data.profile_image_id is not None and data.profile_image_id:
        result = await db.execute(
            select(Asset).where(
                and_(Asset.id == data.profile_image_id, Asset.user_id == user_id)
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Profile image not found")

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    await db.flush()
    await db.refresh(student)

    img_url = await _get_profile_image_url(db, student.profile_image_id)
    return student_to_dict(student, img_url)


@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a student."""
    result = await db.execute(
        select(Student).where(
            and_(Student.id == student_id, Student.user_id == user_id)
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    await db.delete(student)
    return {"detail": "Student deleted"}
