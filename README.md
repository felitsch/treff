# TREFF Post-Generator

A web-based social media content tool for **TREFF Sprachreisen**, a German provider of high school exchange programs in the USA, Canada, Australia, New Zealand, and Ireland.

## Overview

The Post-Generator enables TREFF's social media team to create consistent, high-quality Instagram and TikTok posts in minutes instead of hours, using:

- **AI-powered text generation** (Gemini 3 Flash) for slide headlines, captions, and hashtags
- **AI image generation** (Gemini 3 Pro Image) for branded backgrounds and visuals
- **Pre-built HTML/CSS templates** for all 9 post categories
- **Live preview** with WYSIWYG editing
- **Content calendar** with scheduling and reminders
- **Analytics dashboard** for tracking posting consistency

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue.js 3 (Composition API), Tailwind CSS, Pinia, Vue Router |
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async) |
| Database | SQLite |
| AI | Google Gemini 3 Flash (text), Gemini 3 Pro Image (images) |
| Rendering | Puppeteer (server-side HTML-to-PNG) |
| Build | Vite (frontend), uvicorn (backend) |

## Project Structure

```
treff/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI route handlers
│   │   ├── core/            # Config, database, security
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic
│   │   ├── prompts/         # AI prompt templates
│   │   └── static/uploads/  # User uploads and exports
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── assets/          # CSS, images
│   │   ├── components/      # Vue components by feature area
│   │   ├── composables/     # Reusable composition functions
│   │   ├── router/          # Vue Router configuration
│   │   ├── stores/          # Pinia stores
│   │   ├── views/           # Page-level components
│   │   └── utils/           # API client, helpers
│   ├── package.json
│   └── vite.config.js
├── init.sh                  # Development setup script
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API key (for AI features)

### Setup & Run

```bash
# Make init.sh executable
chmod +x init.sh

# Run the setup script (installs dependencies and starts servers)
./init.sh
```

This will:
1. Set up Python virtual environment and install backend dependencies
2. Install Node.js frontend dependencies
3. Start FastAPI backend on **http://localhost:8000**
4. Start Vite dev server on **http://localhost:5173**

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

```env
GEMINI_API_KEY=your-gemini-api-key    # Required for AI features
OPENAI_API_KEY=                        # Optional fallback
UNSPLASH_ACCESS_KEY=                   # Optional for stock photos
```

## API Documentation

When the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Post Categories

1. **Länder-Spotlight** — Country-specific informative posts
2. **Erfahrungsberichte** — Alumni testimonials
3. **Infografiken** — Visual data and comparisons
4. **Fristen & CTA** — Deadline announcements
5. **Tipps & Tricks** — Practical advice
6. **FAQ** — Frequently asked questions
7. **Foto-Posts** — Student photos with branding
8. **Reel/TikTok Thumbnails** — Video cover images
9. **Story-Posts** — Instagram Story content

## Brand Colors

- **Primary**: `#4C8BC2` (TREFF Blue)
- **Secondary**: `#FDD000` (TREFF Yellow)
- **Dark**: `#1A1A2E`
- **Light**: `#F5F5F5`

## License

Private — TREFF Sprachreisen internal tool.
