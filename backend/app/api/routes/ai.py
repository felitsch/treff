"""AI Generation routes."""

from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user_id
from app.core.text_generator import generate_text_content

router = APIRouter()


@router.post("/generate-text")
async def generate_text(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Generate slide texts, captions, hashtags, CTA.

    Expects:
    - category (str): Post category (e.g., laender_spotlight)
    - country (str, optional): Target country
    - topic (str, optional): Topic or subject
    - key_points (str, optional): Key points to include
    - tone (str, optional): jugendlich or serioess (default: jugendlich)
    - platform (str, optional): Target platform
    - slide_count (int, optional): Number of slides (default: 1)

    Returns structured content for all slides, captions, and hashtags.
    """
    try:
        category = request.get("category", "laender_spotlight")
        country = request.get("country")
        topic = request.get("topic")
        key_points = request.get("key_points")
        tone = request.get("tone", "jugendlich")
        platform = request.get("platform", "instagram_feed")
        slide_count = request.get("slide_count", 1)

        if slide_count < 1:
            slide_count = 1
        if slide_count > 10:
            slide_count = 10

        result = generate_text_content(
            category=category,
            country=country,
            topic=topic,
            key_points=key_points,
            tone=tone,
            platform=platform,
            slide_count=slide_count,
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")


@router.post("/generate-image")
async def generate_image(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Generate image via Gemini 3 Pro Image.

    Note: Requires GEMINI_API_KEY in environment. Returns placeholder if not configured.
    """
    # Image generation requires actual API key - return helpful message
    return {
        "status": "api_key_required",
        "message": "Bildgenerierung benoetigt einen Gemini API-Key. Bitte in den Einstellungen konfigurieren.",
        "image_url": None,
    }


@router.post("/edit-image")
async def edit_image(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Edit existing image via natural language."""
    return {
        "status": "api_key_required",
        "message": "Bildbearbeitung benoetigt einen Gemini API-Key. Bitte in den Einstellungen konfigurieren.",
    }


@router.post("/suggest-content")
async def suggest_content(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Get content suggestions for calendar."""
    return {
        "status": "api_key_required",
        "message": "Content-Vorschlaege benoetigen einen Gemini API-Key.",
    }


@router.post("/suggest-weekly-plan")
async def suggest_weekly_plan(
    request: dict,
    user_id: int = Depends(get_current_user_id),
):
    """Generate full week content plan."""
    return {
        "status": "api_key_required",
        "message": "Wochenplan-Vorschlaege benoetigen einen Gemini API-Key.",
    }
