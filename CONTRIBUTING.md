# Contributing — TREFF Post-Generator

Dieses Dokument beschreibt den Development-Workflow fuer den TREFF Post-Generator.

---

## Voraussetzungen

- **Python 3.11+** mit `pip`
- **Node.js 18+** mit `npm`
- **Git**
- Ein Code-Editor (z.B. VS Code mit Volar-Extension fuer Vue.js)

---

## Development Setup

### 1. Repository klonen

```bash
git clone <repository-url>
cd treff
```

### 2. Server starten

```bash
chmod +x init.sh
./init.sh
```

Das Script erstellt automatisch:
- Python Virtual Environment (`backend/venv/`)
- `.env` aus `.env.example` (falls nicht vorhanden)
- Installiert alle Abhaengigkeiten
- Startet Backend (Port 8000) und Frontend (Port 5173)

### 3. Ersten User anlegen

Nach dem Start: http://localhost:5173/register aufrufen und einen Account erstellen.

---

## Projektstruktur-Konventionen

### Frontend (Vue.js 3)

| Verzeichnis | Konvention |
|------------|-----------|
| `views/` | Eine Datei pro Seite, benannt als `*View.vue` (z.B. `DashboardView.vue`) |
| `components/` | Gruppiert nach Feature-Bereich (z.B. `components/posts/`, `components/calendar/`) |
| `composables/` | `use*.js` — Wiederverwendbare Logik (z.B. `useToast.js`, `useApi.js`) |
| `stores/` | Pinia Stores als `*.js` — Ein Store pro Domaene |
| `router/` | Zentrale Route-Definitionen mit Lazy-Loading |
| `config/` | Statische Konfiguration (Design-Tokens, Strategie-Daten) |

**Vue-Komponenten-Style:**
- Immer `<script setup>` (Composition API)
- Tailwind CSS fuer Styling (kein Scoped CSS noetig)
- Props mit `defineProps()`, Events mit `defineEmits()`
- Composables fuer wiederverwendbare Logik extrahieren

### Backend (FastAPI)

| Verzeichnis | Konvention |
|------------|-----------|
| `api/routes/` | Ein Modul pro Resource (z.B. `posts.py`, `assets.py`) |
| `models/` | SQLAlchemy ORM-Modelle, eine Datei pro Tabelle |
| `schemas/` | Pydantic-Schemas fuer Request/Response-Validierung |
| `services/` | Business-Logik, die von Routes aufgerufen wird |
| `core/` | Infrastruktur: Config, Database, Security, Caching |
| `core/seed_*.py` | Seed-Scripts fuer Initialdaten |

**API-Konventionen:**
- Alle Endpoints unter `/api/` prefix
- RESTful: `GET /api/posts/`, `POST /api/posts/`, `PUT /api/posts/{id}`, `DELETE /api/posts/{id}`
- Authentifizierung via JWT Bearer Token
- Async-Funktionen (`async def`) fuer alle Route-Handler
- Pydantic-Models fuer Request-Body und Response-Validierung

---

## Development-Workflow

### Neue Feature implementieren

1. **Neuen Branch erstellen:**
   ```bash
   git checkout -b feature/mein-feature
   ```

2. **Backend-Aenderungen** (falls noetig):
   - Model in `backend/app/models/` anlegen/erweitern
   - Model in `backend/app/models/__init__.py` registrieren
   - Route in `backend/app/api/routes/` erstellen
   - Route in `backend/app/main.py` einbinden
   - Migration erstellen: `cd backend && python migrate.py revision "beschreibung"`
   - Migration ausfuehren: `python migrate.py upgrade`

3. **Frontend-Aenderungen:**
   - View in `frontend/src/views/` anlegen (falls neue Seite)
   - Route in `frontend/src/router/index.js` registrieren
   - Komponenten in `frontend/src/components/<bereich>/` erstellen
   - Store in `frontend/src/stores/` anlegen (falls neuer State noetig)

4. **Testen:**
   - Frontend im Browser pruefen (http://localhost:5173)
   - API im Swagger UI testen (http://localhost:8000/docs)
   - Console-Errors im Browser ueberpruefen

5. **Commit und Push:**
   ```bash
   git add .
   git commit -m "feat: kurze Beschreibung"
   git push origin feature/mein-feature
   ```

### Datenbank-Aenderungen

Bei Schema-Aenderungen immer Alembic-Migrationen verwenden:

```bash
cd backend
source venv/bin/activate

# Nach Model-Aenderung: Migration generieren
python migrate.py revision "add column xyz to posts"

# Migration ausfuehren
python migrate.py upgrade

# Aktuellen Stand pruefen
python migrate.py current
```

### API-Entwicklung

Neue Endpoints folgen diesem Muster:

```python
# backend/app/api/routes/mein_modul.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/api/mein-modul", tags=["Mein Modul"])

@router.get("/")
async def list_items(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # ... Implementierung
    pass
```

Dann in `backend/app/main.py` einbinden:

```python
from app.api.routes.mein_modul import router as mein_modul_router
app.include_router(mein_modul_router)
```

---

## Code-Style

### Allgemein
- Deutsche Benutzer-sichtbare Texte (UI, Fehlermeldungen)
- Englischer Code (Variablen, Funktionen, Kommentare)
- Keine hartcodierten Strings — Konstanten oder Config verwenden

### Git-Commit-Messages
- `feat:` — Neues Feature
- `fix:` — Bugfix
- `docs:` — Nur Dokumentation
- `refactor:` — Code-Umstrukturierung ohne Funktionsaenderung
- `style:` — Formatierung, Whitespace
- `chore:` — Build-Prozess, Dependencies

### Tailwind CSS
- Utility-First — keine separaten CSS-Dateien pro Komponente
- Design-Tokens aus `frontend/src/config/designTokens.js` verwenden
- Dark-Mode via `dark:` Prefix (Tailwind Dark Mode)

---

## Debugging

### Backend-Logs
```bash
# SQL-Queries anzeigen
SQL_ECHO=True python -m uvicorn app.main:app --reload

# Debug-Level Logging
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --reload
```

### Frontend-Debugging
- Vue DevTools Browser-Extension installieren
- Pinia DevTools fuer State-Inspektion
- Network-Tab fuer API-Calls pruefen
- Console fuer JavaScript-Fehler

### Haeufige Probleme

| Problem | Loesung |
|---------|---------|
| CORS-Fehler | `FRONTEND_URL` in `.env` pruefen |
| 401 Unauthorized | Token abgelaufen — neu einloggen |
| SQLite Lock | Nur eine Schreib-Connection gleichzeitig |
| Port belegt | `lsof -ti :8000 \| xargs kill -9` |
| Module not found | `pip install -r requirements.txt` / `npm install` |

---

## Deployment

Siehe [README.md](README.md#deployment) fuer Deployment-Anleitungen (Vercel, Docker).

---

## Kontakt

Bei Fragen zum Projekt: TREFF Sprachreisen, Eningen u.A.
