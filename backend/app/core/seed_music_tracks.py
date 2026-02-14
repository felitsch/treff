"""Seed default royalty-free music tracks for the music library.

Since we cannot bundle actual music files, this creates placeholder entries
with synthetic audio generated via ffmpeg (simple sine wave tones at different
frequencies to simulate different moods). In production, these would be replaced
with real royalty-free tracks.
"""

import logging
import os
import subprocess
import uuid
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paths import get_upload_dir
from app.models.music_track import MusicTrack

logger = logging.getLogger(__name__)

# Default music library entries with metadata
DEFAULT_TRACKS = [
    {
        "name": "Summer Vibes",
        "category": "upbeat",
        "mood": "happy",
        "bpm": 120,
        "description": "Froehlicher, sonniger Beat perfekt fuer Reise-Content und Abenteuer-Highlights.",
        "freq": 440,  # A4
        "duration": 15,
    },
    {
        "name": "Ocean Breeze",
        "category": "chill",
        "mood": "calm",
        "bpm": 85,
        "description": "Entspannter Lo-Fi Beat fuer ruhige Landschafts-Aufnahmen und Reflexions-Posts.",
        "freq": 330,  # E4
        "duration": 15,
    },
    {
        "name": "New Horizons",
        "category": "inspirational",
        "mood": "epic",
        "bpm": 100,
        "description": "Inspirierende Melodie fuer Abschied, Neuanfang und Highschool-Start Momente.",
        "freq": 392,  # G4
        "duration": 15,
    },
    {
        "name": "Party Time",
        "category": "fun",
        "mood": "playful",
        "bpm": 128,
        "description": "Energiegeladener Dance-Beat fuer Prom, Schulveranstaltungen und Feier-Content.",
        "freq": 523,  # C5
        "duration": 15,
    },
    {
        "name": "Homecoming",
        "category": "emotional",
        "mood": "sad",
        "bpm": 72,
        "description": "Sanfte, emotionale Klaviermelodie fuer Abschied und Heimkehr-Momente.",
        "freq": 262,  # C4
        "duration": 15,
    },
    {
        "name": "Adventure Awaits",
        "category": "upbeat",
        "mood": "energetic",
        "bpm": 140,
        "description": "Schneller, dynamischer Beat fuer Sport, Aktivitaeten und Action-Clips.",
        "freq": 494,  # B4
        "duration": 15,
    },
    {
        "name": "Golden Sunset",
        "category": "chill",
        "mood": "calm",
        "bpm": 90,
        "description": "Warmer Ambient-Sound fuer Sonnenuntergang und Natur-Aufnahmen.",
        "freq": 350,  # ~F4
        "duration": 15,
    },
    {
        "name": "School Days",
        "category": "fun",
        "mood": "happy",
        "bpm": 115,
        "description": "Lockerer, froehlicher Track fuer Schulalltag und Campus-Life Content.",
        "freq": 415,  # ~Ab4
        "duration": 15,
    },
    {
        "name": "Epic Journey",
        "category": "dramatic",
        "mood": "epic",
        "bpm": 95,
        "description": "Dramatischer Orchesterklang fuer grosse Momente und Transformations-Stories.",
        "freq": 294,  # D4
        "duration": 15,
    },
    {
        "name": "Chill Study",
        "category": "chill",
        "mood": "calm",
        "bpm": 80,
        "description": "Ruhiger Lo-Fi Beat fuer Lernszenen, Bibliothek und ruhige Momente.",
        "freq": 370,  # ~F#4
        "duration": 15,
    },
    {
        "name": "Heartfelt Goodbye",
        "category": "emotional",
        "mood": "sad",
        "bpm": 68,
        "description": "Emotionaler Streicher-Klang fuer Abschied von Gastfamilie und Freunden.",
        "freq": 247,  # B3
        "duration": 15,
    },
    {
        "name": "Road Trip Energy",
        "category": "upbeat",
        "mood": "energetic",
        "bpm": 130,
        "description": "Energetischer Rock-Beat fuer Road-Trips und Reise-Montagen.",
        "freq": 466,  # Bb4
        "duration": 15,
    },
]


def _generate_synthetic_audio(filepath: Path, freq: int, duration: int) -> bool:
    """Generate a simple synthetic audio file using ffmpeg sine wave.

    Creates a short audio clip with a sine wave tone that simulates a music track.
    """
    try:
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"sine=frequency={freq}:duration={duration}",
            "-af", f"afade=t=in:d=2,afade=t=out:st={duration-2}:d=2,volume=0.3",
            "-c:a", "libmp3lame",
            "-b:a", "128k",
            "-y",
            str(filepath),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0 and filepath.exists() and filepath.stat().st_size > 0:
            return True
        logger.warning(f"ffmpeg audio generation failed: {proc.stderr[:500]}")
        return False
    except FileNotFoundError:
        logger.warning("ffmpeg not found - cannot generate synthetic audio tracks")
        return False
    except Exception as e:
        logger.warning(f"Error generating synthetic audio: {e}")
        return False


async def seed_music_tracks(session: AsyncSession) -> int:
    """Seed default music tracks into the database.

    Returns the number of newly seeded tracks.
    """
    MUSIC_DIR = get_upload_dir("music")
    result = await session.execute(select(func.count(MusicTrack.id)))
    count = result.scalar()

    if count and count > 0:
        return 0  # Already seeded

    seeded = 0
    for track_data in DEFAULT_TRACKS:
        filename = f"{uuid.uuid4()}.mp3"
        filepath = MUSIC_DIR / filename

        # Generate a synthetic audio file
        generated = _generate_synthetic_audio(filepath, track_data["freq"], track_data["duration"])

        if not generated:
            # Create a tiny silent placeholder if ffmpeg fails
            try:
                # Write a minimal valid MP3 frame (silence)
                filepath.write_bytes(b'\xff\xfb\x90\x00' + b'\x00' * 417)
            except Exception:
                continue

        track = MusicTrack(
            name=track_data["name"],
            filename=filename,
            file_path=f"/uploads/music/{filename}",
            duration_seconds=float(track_data["duration"]),
            category=track_data["category"],
            mood=track_data["mood"],
            bpm=track_data["bpm"],
            description=track_data["description"],
            is_default=True,
        )
        session.add(track)
        seeded += 1

    if seeded > 0:
        await session.commit()

    return seeded
