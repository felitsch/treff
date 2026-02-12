"""Health check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check server health and database connectivity."""
    db_status = "disconnected"
    tables = []
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_status = "connected"
        # List all tables
        table_result = await db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        tables = [row[0] for row in table_result.fetchall()]
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status,
        "tables": tables,
        "table_count": len(tables),
        "service": "TREFF Post-Generator API",
        "version": "1.0.0",
    }


@router.get("/health/schema")
async def schema_check(db: AsyncSession = Depends(get_db)):
    """Return detailed database schema information for all tables."""
    schema = {}
    try:
        # Get all tables
        table_result = await db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        )
        table_names = [row[0] for row in table_result.fetchall()]

        for table_name in table_names:
            col_result = await db.execute(text(f"PRAGMA table_info({table_name})"))
            columns = []
            for row in col_result.fetchall():
                columns.append({
                    "name": row[1],
                    "type": row[2],
                    "notnull": bool(row[3]),
                    "pk": bool(row[5]),
                })
            schema[table_name] = columns

    except Exception as e:
        return {"error": str(e)}

    return {
        "tables": list(schema.keys()),
        "table_count": len(schema),
        "schema": schema,
    }
