# Plan: Fix 2 Vercel Production Bugs

## Kontext

Nach dem Gemini-Fix zeigen die Vercel-Logs zwei wiederkehrende 500er:
1. `POST /api/series-reminders/check` und `GET /api/series-reminders/series-status` crashen mit `TypeError: can't subtract offset-naive and offset-aware datetimes`
2. `DELETE /api/assets/{id}` crasht beim Commit mit `FOREIGN KEY constraint failed`

## Bug 1: Datetime naive/aware Mismatch (series_reminders.py)

**Root Cause**: `now = datetime.now(timezone.utc)` ist timezone-aware, aber `last_episode.created_at` kommt aus Turso als naive datetime (ohne tzinfo). Subtraktion schlaegt fehl.

**Fix**: `now` und `today` als naive UTC verwenden — konsistent mit dem was die DB zurueckgibt.

**Datei**: `backend/app/api/routes/series_reminders.py`

- **Zeile 213**: `now = datetime.now(timezone.utc)` → `now = datetime.utcnow()`
- **Zeile 351**: `now = datetime.now(timezone.utc)` → `now = datetime.utcnow()`

Das reicht, weil `today = now.date()` automatisch mitgeht und alle DB-Werte naive datetimes sind.

## Bug 2: Asset Delete FK Constraint (5 Models)

**Root Cause**: Asset-Delete schlaegt fehl weil 5 Tabellen Foreign Keys auf `assets.id` haben — ohne `ondelete="SET NULL"` oder `"CASCADE"`.

**Fix**: `ondelete="SET NULL"` fuer nullable FKs, `ondelete="CASCADE"` fuer non-nullable FKs.

| Datei | Feld | Nullable | ondelete |
|---|---|---|---|
| `backend/app/models/post_slide.py:22` | `image_asset_id` | Ja | `SET NULL` |
| `backend/app/models/student.py:27` | `profile_image_id` | Ja | `SET NULL` |
| `backend/app/models/story_arc.py:29` | `cover_image_id` | Ja | `SET NULL` |
| `backend/app/models/video_overlay.py:15` | `asset_id` | Nein | `CASCADE` |
| `backend/app/models/video_export.py:15` | `asset_id` | Nein | `CASCADE` |

## Verifikation

1. Syntax-Check: `python3 -c "import ast; ..."`
2. Push zu Vercel
3. Logs pruefen: keine 500er mehr bei `/api/series-reminders/check`, `/api/series-reminders/series-status`, und `DELETE /api/assets/{id}`
