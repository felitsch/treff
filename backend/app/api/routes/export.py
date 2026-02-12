"""Export routes."""

from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user_id

router = APIRouter()


@router.post("/render")
async def render_post(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Render post to PNG via Puppeteer."""
    # TODO: Implement Puppeteer rendering
    return {"message": "Render endpoint", "data": request}


@router.post("/render-carousel")
async def render_carousel(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Render all slides of a carousel."""
    # TODO: Implement
    return {"message": "Carousel render endpoint", "data": request}


@router.get("/download/{export_id}")
async def download_export(
    export_id: int,
    user_id: int = Depends(get_current_user_id),
):
    """Download rendered file."""
    # TODO: Implement file serving
    raise HTTPException(status_code=404, detail="Export not found")


@router.post("/batch")
async def batch_export(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Render multiple posts."""
    # TODO: Implement
    return {"message": "Batch export endpoint", "data": request}
