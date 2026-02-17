# TREFF Post-Generator — Vercel Deployment Guide

## Architecture Overview

The TREFF Post-Generator is deployed as a single Vercel project:

- **Frontend**: Vue.js 3 SPA, built with Vite, served as static files
- **Backend**: FastAPI Python app, running as a Vercel Serverless Function (`api/index.py`)
- **Database**: SQLite (ephemeral on Vercel) or Turso (hosted LibSQL) for persistent storage

```
vercel.json
├── Frontend: frontend/dist (static)
│   └── SPA routes → /index.html (client-side routing)
├── API: /api/* → api/index.py (Python serverless)
└── Uploads: /uploads/* → api/index.py (DB-backed file serving)
```

## Prerequisites

- [Vercel CLI](https://vercel.com/docs/cli) (`npm i -g vercel`)
- A Vercel account linked to the GitHub repository
- Environment variables configured in the Vercel dashboard

## Environment Variables

Configure the following in **Vercel Dashboard > Project Settings > Environment Variables**:

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret for signing JWT tokens (use a long random string) | `aBcDeFgH1234567890xYz...` |
| `DEFAULT_USER_EMAIL` | Default admin user email (seeded on cold start) | `admin@treff.de` |
| `DEFAULT_USER_PASSWORD` | Default admin user password | `your-secure-password` |

### Optional (AI Features)

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key for text/image generation | `AIza...` |
| `OPENAI_API_KEY` | OpenAI API key (fallback for text generation) | `sk-...` |
| `UNSPLASH_ACCESS_KEY` | Unsplash API key for stock photo search | `abc123...` |
| `PEXELS_API_KEY` | Pexels API key for stock photo search | `abc123...` |

### Optional (Persistent Database)

| Variable | Description | Example |
|----------|-------------|---------|
| `TURSO_DATABASE_URL` | Turso/LibSQL connection URL | `libsql://treff-db-user.turso.io` |
| `TURSO_AUTH_TOKEN` | Turso authentication token | `eyJ...` |

### Auto-set by Vercel

| Variable | Description |
|----------|-------------|
| `VERCEL` | Set to `"1"` (configured in vercel.json) |
| `VERCEL_URL` | Current deployment URL (used for CORS) |
| `VERCEL_PROJECT_PRODUCTION_URL` | Production URL (used for CORS) |

### Environment Scopes

- **Production**: Set `JWT_SECRET_KEY` to a unique, long random string
- **Preview**: Can share the same API keys but use a different `JWT_SECRET_KEY`
- **Development**: Uses `.env` file in `backend/` (see `.env.example`)

## Deployment

### Automatic (GitHub Integration)

1. Connect the GitHub repository to Vercel
2. Every push to `main` triggers a production deployment
3. Every push to a feature branch creates a preview deployment
4. PRs get automatic preview deployment URLs as comments

### Manual (CLI)

```bash
# Preview deployment
vercel

# Production deployment
vercel --prod
```

### First Deployment Checklist

1. Link the repository: `vercel link`
2. Set all required environment variables in Vercel dashboard
3. Deploy: `vercel --prod`
4. Verify health: `curl https://your-project.vercel.app/api/health`
5. Login with the default credentials

## How It Works

### Frontend Build

The `buildCommand` in `vercel.json` runs:
```bash
cd frontend && npm install && npm run build
```

This produces static files in `frontend/dist/` which Vercel serves directly.

### Backend Serverless Function

`api/index.py` is the entry point. It:
1. Adds `backend/` to the Python path
2. Imports the FastAPI `app` from `backend/app/main.py`
3. Vercel exposes this as a serverless function

All `/api/*` requests are routed to this function via `vercel.json` rewrites.

### Database on Vercel

**Ephemeral SQLite (default)**:
- On each cold start, the app creates tables and seeds default data
- Data persists between warm invocations but is lost on cold starts
- Suitable for demos and testing

**Turso (recommended for production)**:
- Set `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`
- Data persists permanently across all deployments
- The app detects Turso config and uses it instead of SQLite

### File Uploads on Vercel

Vercel's `/tmp` filesystem is ephemeral. The app handles this by:
1. Storing file bytes as base64 in the database (`file_data` column)
2. Writing to `/tmp/uploads/` for immediate serving
3. Restoring from DB on subsequent requests if the file is missing

### CORS Configuration

The backend automatically allows:
- `http://localhost:5173` (development)
- `https://{VERCEL_URL}` (current deployment)
- `https://{VERCEL_PROJECT_PRODUCTION_URL}` (production domain)

### Preview Deployments

Every push to a non-main branch creates a preview deployment:
- Gets a unique URL: `https://treff-xxx-yyy.vercel.app`
- CORS is automatically configured for the preview URL
- Uses the same environment variables (Preview scope)

## Monitoring

- **Health check**: `GET /api/health` — Returns DB status and table count
- **API docs**: `GET /docs` — Interactive Swagger UI
- **Vercel dashboard**: Logs, function invocations, and error tracking

## Troubleshooting

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| 500 on `/api/*` | Missing Python dependency | Check `requirements.txt` in project root |
| CORS errors | Frontend URL not in allowed origins | Verify `VERCEL_URL` env var is set |
| Login fails | Default user not seeded | Check backend logs for seed errors |
| AI features unavailable | Missing API key | Set `GEMINI_API_KEY` in Vercel dashboard |
| Files disappear | Ephemeral `/tmp` | Enable Turso for persistent storage |
| Cold start slow | Many seed operations | Expected (~3-5s); subsequent requests are fast |

### Viewing Logs

```bash
# Real-time function logs
vercel logs --follow

# Or via Vercel dashboard > Deployments > Functions tab
```

## Local Development

```bash
# Install dependencies
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd frontend && npm install

# Create .env from example
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start both servers
./init.sh

# Or manually:
# Terminal 1: cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000
# Terminal 2: cd frontend && npm run dev
```

Open http://localhost:5173 — Login with `admin@treff.de` / `treff2024`
