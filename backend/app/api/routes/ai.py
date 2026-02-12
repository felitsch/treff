"""AI Generation routes."""

from fastapi import APIRouter, Depends
from app.core.security import get_current_user_id

router = APIRouter()


@router.post("/generate-text")
async def generate_text(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Generate slide texts, captions, hashtags, CTA via AI."""
    # TODO: Implement with Gemini 3 Flash
    return {"message": "AI text generation endpoint", "data": request}


@router.post("/generate-image")
async def generate_image(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Generate image via Gemini 3 Pro Image."""
    # TODO: Implement with Gemini 3 Pro Image
    return {"message": "AI image generation endpoint", "data": request}


@router.post("/edit-image")
async def edit_image(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Edit existing image via natural language."""
    # TODO: Implement
    return {"message": "AI image editing endpoint", "data": request}


@router.post("/suggest-content")
async def suggest_content(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Get content suggestions for calendar."""
    # TODO: Implement
    return {"message": "Content suggestion endpoint", "data": request}


@router.post("/suggest-weekly-plan")
async def suggest_weekly_plan(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Generate full week content plan."""
    # TODO: Implement
    return {"message": "Weekly plan suggestion endpoint", "data": request}
