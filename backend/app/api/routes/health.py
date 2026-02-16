"""Health check and API documentation endpoints.

Provides server health monitoring, database schema inspection,
and a machine-readable API endpoint audit.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.cache import api_cache

router = APIRouter()


@router.get(
    "/health",
    summary="Server Health Check",
    description="Verify that the backend server is running and the database connection is active. Returns a list of all database tables.",
    response_description="Health status with database connectivity and table list",
    responses={
        200: {
            "description": "Server is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "database": "connected",
                        "tables": ["posts", "templates", "users"],
                        "table_count": 31,
                        "service": "TREFF Post-Generator API",
                        "version": "1.0.0",
                    }
                }
            },
        }
    },
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check server health and database connectivity.

    This endpoint does NOT require authentication and is suitable
    for load balancer health checks and monitoring systems.
    """
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


@router.get(
    "/health/schema",
    summary="Database Schema Inspection",
    description="Returns detailed column-level schema information for every table in the database. Useful for debugging and development.",
    response_description="Complete database schema with column names, types, and constraints",
)
async def schema_check(db: AsyncSession = Depends(get_db)):
    """Return detailed database schema information for all tables.

    Each table includes its columns with name, type, NOT NULL constraint, and primary key flag.
    """
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


@router.get(
    "/health/api-audit",
    summary="API Endpoint Audit",
    description="Returns a complete inventory of all registered API endpoints with their HTTP methods, paths, tags, and documentation status. Useful for API consolidation and documentation audits.",
    response_description="Full list of API routes with methods and documentation metadata",
    responses={
        200: {
            "description": "API audit report",
            "content": {
                "application/json": {
                    "example": {
                        "total_endpoints": 198,
                        "total_tags": 30,
                        "documented_endpoints": 195,
                        "undocumented_endpoints": 3,
                        "tags": ["Health", "Authentication", "Posts"],
                        "endpoints": [
                            {
                                "path": "/api/health",
                                "methods": ["GET"],
                                "tags": ["Health"],
                                "summary": "Server Health Check",
                                "has_description": True,
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def api_audit(request: Request):
    """Return a complete audit of all registered API endpoints.

    Scans all routes registered in the FastAPI application and returns:
    - Total endpoint count
    - Per-endpoint: path, methods, tags, summary, documentation status
    - Coverage statistics (documented vs undocumented endpoints)
    """
    app = request.app
    endpoints = []
    all_tags = set()
    documented = 0
    undocumented = 0

    for route in app.routes:
        # Only include API routes (skip static files, docs UI routes)
        if not hasattr(route, "methods"):
            continue

        path = getattr(route, "path", "")
        methods = sorted(list(route.methods - {"HEAD", "OPTIONS"}))
        if not methods:
            continue

        tags = getattr(route, "tags", []) or []
        summary = getattr(route, "summary", None) or ""
        description = getattr(route, "description", None) or ""

        # Try to extract from endpoint function docstring
        endpoint_func = getattr(route, "endpoint", None)
        if endpoint_func and not summary:
            summary = (endpoint_func.__doc__ or "").split("\n")[0].strip()

        has_description = bool(summary or description)
        if has_description:
            documented += 1
        else:
            undocumented += 1

        for tag in tags:
            all_tags.add(tag)

        endpoints.append({
            "path": path,
            "methods": methods,
            "tags": tags,
            "summary": summary[:200] if summary else "",
            "has_description": has_description,
        })

    # Sort by path for consistency
    endpoints.sort(key=lambda e: e["path"])
    sorted_tags = sorted(all_tags)

    return {
        "total_endpoints": len(endpoints),
        "total_tags": len(sorted_tags),
        "documented_endpoints": documented,
        "undocumented_endpoints": undocumented,
        "documentation_coverage_percent": round(documented / max(len(endpoints), 1) * 100, 1),
        "tags": sorted_tags,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "endpoints": endpoints,
    }


@router.get(
    "/admin/cache-stats",
    summary="Cache Statistics",
    description="Returns in-memory cache statistics including hit/miss rates, entry counts per prefix, TTL configuration, and invalidation counts. Useful for monitoring cache effectiveness.",
    response_description="Cache statistics and configuration",
)
async def get_cache_stats():
    """Get cache statistics for monitoring.

    Returns hit/miss counts, hit rate percentage, entry counts per prefix,
    configured TTLs, and invalidation/eviction counts. No authentication
    required (read-only monitoring endpoint).
    """
    return api_cache.get_stats()


@router.post(
    "/admin/cache-clear",
    summary="Clear Cache",
    description="Clears the entire in-memory cache. Use for debugging or after manual database changes.",
)
async def clear_cache():
    """Clear all cached data."""
    count = api_cache.invalidate_all()
    return {"message": f"Cache cleared: {count} entries removed", "cleared": count}
