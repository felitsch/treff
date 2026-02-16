"""Pydantic models for Content Pipeline request/response schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════
# Analyze Media
# ═══════════════════════════════════════════════════════════════════════

class AnalyzeMediaResponse(BaseModel):
    """Response from POST /api/pipeline/analyze-media."""
    pipeline_item_id: int
    suggested_post_type: str
    suggested_caption_seeds: list[str]
    suggested_platforms: list[str]
    detected_country: Optional[str] = None
    analysis_summary: str


# ═══════════════════════════════════════════════════════════════════════
# Inbox
# ═══════════════════════════════════════════════════════════════════════

class InboxItemResponse(BaseModel):
    """Single inbox item in the list response."""
    id: int
    user_id: int
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    asset_id: Optional[int] = None
    asset_filename: Optional[str] = None
    asset_file_type: Optional[str] = None
    asset_thumbnail_path: Optional[str] = None
    suggested_post_type: Optional[str] = None
    suggested_caption_seeds: Optional[list[str]] = None
    suggested_platforms: Optional[list[str]] = None
    detected_country: Optional[str] = None
    analysis_summary: Optional[str] = None
    status: str
    result_post_id: Optional[int] = None
    error_message: Optional[str] = None
    source_description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class InboxListResponse(BaseModel):
    """Response from GET /api/pipeline/inbox."""
    items: list[InboxItemResponse]
    total: int
    page: int
    limit: int


# ═══════════════════════════════════════════════════════════════════════
# Process
# ═══════════════════════════════════════════════════════════════════════

class ProcessRequest(BaseModel):
    """Request body for POST /api/pipeline/process."""
    inbox_item_id: int
    post_type: Optional[str] = None  # Override suggested_post_type
    platform: Optional[str] = None  # Override suggested platform
    tone: Optional[str] = Field(default="jugendlich")
    country: Optional[str] = None  # Override detected_country


class ProcessResponse(BaseModel):
    """Response from POST /api/pipeline/process."""
    post_id: int
    title: str
    category: str
    platform: str
    country: Optional[str] = None
    status: str
    caption_instagram: Optional[str] = None
    caption_tiktok: Optional[str] = None
    message: str


# ═══════════════════════════════════════════════════════════════════════
# Multiply (Content Multiplier)
# ═══════════════════════════════════════════════════════════════════════

class MultiplyRequest(BaseModel):
    """Request body for POST /api/pipeline/multiply."""
    post_id: int
    formats: list[str] = Field(
        default=["instagram_story", "tiktok"],
        description="Derivative formats to generate. Options: instagram_feed, instagram_story, tiktok, carousel"
    )


class DerivativePostInfo(BaseModel):
    """Info about a generated derivative post."""
    post_id: int
    platform: str
    title: str
    status: str


class MultiplyResponse(BaseModel):
    """Response from POST /api/pipeline/multiply."""
    source_post_id: int
    derivatives: list[DerivativePostInfo]
    message: str
