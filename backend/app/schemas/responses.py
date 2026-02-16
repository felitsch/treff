"""Standard API response schemas for consistent response formats.

All API endpoints should use these response models for consistent formatting:
- APIResponse: Standard envelope {data, meta, error}
- PaginatedResponse: Paginated data with {data, meta: {page, total, ...}, error}
- ErrorResponse: Error details {data: null, meta: null, error: {code, message, details}}

Usage in routes:
    from app.schemas.responses import api_response, paginated_response, error_response

    @router.get("/items")
    async def list_items():
        items = [...]
        return api_response(data=items)

    @router.get("/items/paged")
    async def list_items_paged(page: int, limit: int):
        items = [...]
        return paginated_response(data=items, page=1, limit=20, total=100)
"""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


# ─── Meta Models ────────────────────────────────────────────────────────────

class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""
    page: int = Field(..., description="Current page number (1-based)", examples=[1])
    limit: int = Field(..., description="Items per page", examples=[20])
    total: int = Field(..., description="Total number of items matching the query", examples=[42])
    total_pages: int = Field(..., description="Total number of pages", examples=[3])


class ResponseMeta(BaseModel):
    """Optional metadata attached to any response."""
    page: Optional[int] = Field(None, description="Current page (if paginated)")
    limit: Optional[int] = Field(None, description="Items per page (if paginated)")
    total: Optional[int] = Field(None, description="Total items (if paginated)")
    total_pages: Optional[int] = Field(None, description="Total pages (if paginated)")


# ─── Error Models ───────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """Structured error detail."""
    code: str = Field(..., description="Machine-readable error code", examples=["VALIDATION_ERROR"])
    message: str = Field(..., description="Human-readable error message", examples=["The request body contains invalid data."])
    details: Optional[Any] = Field(None, description="Additional error details (field errors, etc.)")


# ─── Standard Response Models ───────────────────────────────────────────────

class APIResponse(BaseModel):
    """Standard API response envelope.

    All successful responses follow this structure:
    {
        "data": <payload>,
        "meta": { ... } | null,
        "error": null
    }
    """
    data: Any = Field(..., description="Response payload")
    meta: Optional[ResponseMeta] = Field(None, description="Response metadata (pagination, etc.)")
    error: Optional[ErrorDetail] = Field(None, description="Error details (null on success)")

    model_config = {"json_schema_extra": {
        "examples": [
            {
                "data": {"id": 1, "title": "Example Post"},
                "meta": None,
                "error": None,
            }
        ]
    }}


class PaginatedResponse(BaseModel):
    """Paginated response with items array and pagination metadata.

    {
        "data": [<items>],
        "meta": {"page": 1, "limit": 20, "total": 42, "total_pages": 3},
        "error": null
    }
    """
    data: List[Any] = Field(..., description="List of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    error: Optional[ErrorDetail] = Field(None, description="Error details (null on success)")

    model_config = {"json_schema_extra": {
        "examples": [
            {
                "data": [{"id": 1, "title": "Post A"}, {"id": 2, "title": "Post B"}],
                "meta": {"page": 1, "limit": 20, "total": 2, "total_pages": 1},
                "error": None,
            }
        ]
    }}


class ErrorResponse(BaseModel):
    """Standard error response.

    {
        "data": null,
        "meta": null,
        "error": {"code": "NOT_FOUND", "message": "Resource not found", "details": null}
    }
    """
    data: Optional[Any] = Field(None, description="Always null on error")
    meta: Optional[ResponseMeta] = Field(None, description="Always null on error")
    error: ErrorDetail = Field(..., description="Error details")

    model_config = {"json_schema_extra": {
        "examples": [
            {
                "data": None,
                "meta": None,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found.",
                    "details": None,
                },
            }
        ]
    }}


# ─── Helper Functions ───────────────────────────────────────────────────────

def api_response(
    data: Any,
    meta: Optional[dict] = None,
) -> dict:
    """Create a standard API response dict.

    Args:
        data: The response payload (any serializable object)
        meta: Optional metadata dict

    Returns:
        Dict in {data, meta, error} format
    """
    response = {
        "data": data,
        "meta": meta,
        "error": None,
    }
    return response


def paginated_response(
    data: list,
    page: int,
    limit: int,
    total: int,
) -> dict:
    """Create a paginated API response dict.

    Args:
        data: List of items for the current page
        page: Current page number (1-based)
        limit: Items per page
        total: Total number of items across all pages

    Returns:
        Dict in {data, meta: {page, limit, total, total_pages}, error} format
    """
    total_pages = max(1, (total + limit - 1) // limit)
    return {
        "data": data,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
        },
        "error": None,
    }


def error_response(
    code: str,
    message: str,
    details: Any = None,
    status_code: int = 400,
) -> dict:
    """Create a standard error response dict.

    Note: This returns the body dict. To send as HTTP response with status code,
    use raise_api_error() or return JSONResponse directly.

    Args:
        code: Machine-readable error code (e.g., "VALIDATION_ERROR")
        message: Human-readable error message
        details: Additional error context
        status_code: HTTP status code (not included in body, for reference)

    Returns:
        Dict in {data: null, meta: null, error: {code, message, details}} format
    """
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }


# ─── HTTP Error Codes Mapping ──────────────────────────────────────────────

ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
}
