"""Report generation routes.

Generates weekly/monthly performance reports as PDF or CSV.
Reports include summaries, top posts, metrics tables, and recommendations.
PDF reports feature TREFF branding (colors, fonts).
"""

import csv
import io
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.core.database import get_db, Base
from app.core.security import get_current_user_id
from app.models.post import Post

from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

router = APIRouter()


# ─── Report History Model (inline to avoid separate model file) ───────────
class ReportHistory(Base):
    __tablename__ = "report_history"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    report_type: Mapped[str] = mapped_column(String, nullable=False)  # "pdf" or "csv"
    period: Mapped[str] = mapped_column(String, nullable=False)  # "week" or "month"
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


# ─── Helper: Gather report data ──────────────────────────────────────────
async def _gather_report_data(user_id: int, period: str, db: AsyncSession):
    """Collect all data needed for report generation."""
    now = datetime.now(timezone.utc)

    if period == "week":
        start = now - timedelta(days=7)
        period_label = "Wochenbericht"
        date_range = f"{start.strftime('%d.%m.%Y')} - {now.strftime('%d.%m.%Y')}"
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_label = "Monatsbericht"
        date_range = f"{start.strftime('%d.%m.%Y')} - {now.strftime('%d.%m.%Y')}"

    # Get all posts in the period
    result = await db.execute(
        select(Post).where(
            Post.user_id == user_id,
            Post.created_at >= start,
        ).order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()

    # Category distribution
    categories = {}
    platforms = {}
    countries = {}
    statuses = {}

    for p in posts:
        cat = p.category or "unbekannt"
        categories[cat] = categories.get(cat, 0) + 1
        plat = p.platform or "unbekannt"
        platforms[plat] = platforms.get(plat, 0) + 1
        if p.country:
            countries[p.country] = countries.get(p.country, 0) + 1
        st = p.status or "draft"
        statuses[st] = statuses.get(st, 0) + 1

    # Performance metrics
    posts_with_metrics = [
        p for p in posts
        if p.perf_likes is not None or p.perf_reach is not None
    ]
    total_likes = sum(p.perf_likes or 0 for p in posts_with_metrics)
    total_comments = sum(p.perf_comments or 0 for p in posts_with_metrics)
    total_shares = sum(p.perf_shares or 0 for p in posts_with_metrics)
    total_saves = sum(p.perf_saves or 0 for p in posts_with_metrics)
    total_reach = sum(p.perf_reach or 0 for p in posts_with_metrics)
    avg_engagement = 0.0
    if total_reach > 0:
        avg_engagement = round(((total_likes + total_comments + total_shares) / total_reach) * 100, 2)

    # Top posts by engagement
    top_posts = []
    for p in posts_with_metrics:
        likes = p.perf_likes or 0
        comments = p.perf_comments or 0
        shares = p.perf_shares or 0
        reach = p.perf_reach or 0
        eng = round(((likes + comments + shares) / reach) * 100, 2) if reach > 0 else 0
        top_posts.append({
            "id": p.id,
            "title": p.title or f"Post #{p.id}",
            "category": p.category,
            "platform": p.platform,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": p.perf_saves or 0,
            "reach": reach,
            "engagement_rate": eng,
        })
    top_posts.sort(key=lambda x: x["engagement_rate"], reverse=True)
    top_posts = top_posts[:10]

    # Recommendations
    recommendations = []
    if len(posts) == 0:
        recommendations.append("Keine Posts im Berichtszeitraum. Posting-Frequenz erhoehen!")
    else:
        if "instagram_story" not in platforms:
            recommendations.append("Instagram Stories einsetzen fuer hoehere Reichweite")
        if "tiktok" not in platforms:
            recommendations.append("TikTok als Kanal erschliessen")
        missing_countries = [c for c in ["usa", "canada", "australia", "newzealand", "ireland"] if c not in countries]
        if missing_countries:
            labels = {"usa": "USA", "canada": "Kanada", "australia": "Australien", "newzealand": "Neuseeland", "ireland": "Irland"}
            names = ", ".join(labels.get(c, c) for c in missing_countries[:2])
            recommendations.append(f"Mehr Content fuer: {names}")
        if len(posts_with_metrics) < len(posts) * 0.5 and len(posts) > 2:
            recommendations.append("Performance-Metriken fuer mehr Posts nachtragen")

    return {
        "period_label": period_label,
        "date_range": date_range,
        "generated_at": now.isoformat(),
        "total_posts": len(posts),
        "posts_with_metrics": len(posts_with_metrics),
        "categories": categories,
        "platforms": platforms,
        "countries": countries,
        "statuses": statuses,
        "metrics": {
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "total_saves": total_saves,
            "total_reach": total_reach,
            "avg_engagement_rate": avg_engagement,
        },
        "top_posts": top_posts,
        "recommendations": recommendations,
        "posts": posts,
    }


# ─── Generate PDF Report ─────────────────────────────────────────────────
def _generate_pdf(data: dict) -> bytes:
    """Generate a branded PDF report using fpdf2."""
    from fpdf import FPDF

    class TreffPDF(FPDF):
        def header(self):
            # TREFF brand blue header bar
            self.set_fill_color(76, 139, 194)  # #4C8BC2
            self.rect(0, 0, 210, 25, "F")
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(255, 255, 255)
            self.set_y(5)
            self.cell(0, 10, "TREFF Sprachreisen", align="L")
            self.set_font("Helvetica", "", 10)
            self.cell(0, 10, data["period_label"], align="R")
            self.ln(15)
            # Yellow accent line
            self.set_fill_color(253, 208, 0)  # #FDD000
            self.rect(0, 25, 210, 2, "F")
            self.set_y(32)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"TREFF Sprachreisen | Generiert am {datetime.now().strftime('%d.%m.%Y %H:%M')} | Seite {self.page_no()}/{{nb}}", align="C")

    pdf = TreffPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ─── Title Section ───
    pdf.set_text_color(26, 26, 46)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, data["period_label"], ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, f"Zeitraum: {data['date_range']}", ln=True)
    pdf.ln(5)

    # ─── Summary Box ───
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, pdf.get_y(), 190, 30, "F")
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 26, 46)
    y_start = pdf.get_y() + 3

    # 4 columns of summary stats
    col_w = 47.5
    metrics = [
        (str(data["total_posts"]), "Posts erstellt"),
        (str(data["posts_with_metrics"]), "Mit Metriken"),
        (f"{data['metrics']['avg_engagement_rate']}%", "Engagement Rate"),
        (f"{data['metrics']['total_reach']:,}".replace(",", "."), "Reichweite"),
    ]
    for i, (value, label) in enumerate(metrics):
        x = 10 + i * col_w
        pdf.set_xy(x, y_start)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(76, 139, 194)
        pdf.cell(col_w, 10, value, align="C")
        pdf.set_xy(x, y_start + 12)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(col_w, 8, label, align="C")

    pdf.set_y(y_start + 28)
    pdf.ln(5)

    # ─── Performance Metrics Table ───
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 10, "Performance-Metriken", ln=True)

    # Table header
    pdf.set_fill_color(76, 139, 194)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    cols = ["Metrik", "Wert"]
    col_widths = [100, 90]
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 8, col, 1, 0, "C", True)
    pdf.ln()

    # Table rows
    pdf.set_text_color(26, 26, 46)
    pdf.set_font("Helvetica", "", 9)
    metric_rows = [
        ("Likes gesamt", str(data["metrics"]["total_likes"])),
        ("Kommentare gesamt", str(data["metrics"]["total_comments"])),
        ("Shares gesamt", str(data["metrics"]["total_shares"])),
        ("Saves gesamt", str(data["metrics"]["total_saves"])),
        ("Reichweite gesamt", f"{data['metrics']['total_reach']:,}".replace(",", ".")),
        ("Durchschn. Engagement Rate", f"{data['metrics']['avg_engagement_rate']}%"),
    ]
    fill = False
    for label, value in metric_rows:
        if fill:
            pdf.set_fill_color(245, 245, 245)
        pdf.cell(col_widths[0], 7, f"  {label}", 1, 0, "L", fill)
        pdf.cell(col_widths[1], 7, value, 1, 0, "C", fill)
        pdf.ln()
        fill = not fill

    pdf.ln(5)

    # ─── Distribution Section ───
    if data["categories"]:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 10, "Verteilung", ln=True)

        category_labels = {
            "laender_spotlight": "Laender-Spotlight",
            "erfahrungsberichte": "Erfahrungsberichte",
            "infografiken": "Infografiken",
            "fristen_cta": "Fristen/CTA",
            "tipps_tricks": "Tipps & Tricks",
            "faq": "FAQ",
            "foto_posts": "Foto-Posts",
            "reel_tiktok_thumbnails": "Reels/TikTok",
            "story_posts": "Stories",
            "story_teaser": "Story-Teaser",
        }
        platform_labels = {
            "instagram_feed": "Instagram Feed",
            "instagram_story": "Instagram Story",
            "tiktok": "TikTok",
        }

        # Categories
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Kategorien:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for cat, count in sorted(data["categories"].items(), key=lambda x: -x[1]):
            label = category_labels.get(cat, cat)
            pct = round(count / data["total_posts"] * 100) if data["total_posts"] > 0 else 0
            # Draw simple bar
            bar_width = min(pct * 1.2, 120)
            pdf.cell(60, 6, f"  {label}", 0, 0)
            pdf.set_fill_color(76, 139, 194)
            pdf.cell(bar_width, 6, "", 0, 0, "", True)
            pdf.cell(30, 6, f"  {count} ({pct}%)", 0, 1)

        pdf.ln(3)

        # Platforms
        if data["platforms"]:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "Plattformen:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            for plat, count in sorted(data["platforms"].items(), key=lambda x: -x[1]):
                label = platform_labels.get(plat, plat)
                pct = round(count / data["total_posts"] * 100) if data["total_posts"] > 0 else 0
                bar_width = min(pct * 1.2, 120)
                pdf.cell(60, 6, f"  {label}", 0, 0)
                pdf.set_fill_color(253, 208, 0)
                pdf.cell(bar_width, 6, "", 0, 0, "", True)
                pdf.cell(30, 6, f"  {count} ({pct}%)", 0, 1)
            pdf.ln(3)

    # ─── Top Posts Section ───
    if data["top_posts"]:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 10, "Top-Posts nach Engagement", ln=True)

        # Table header
        pdf.set_fill_color(76, 139, 194)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        top_cols = ["#", "Titel", "Likes", "Komm.", "Reach", "Eng.%"]
        top_widths = [10, 75, 20, 20, 30, 25]
        for i, col in enumerate(top_cols):
            pdf.cell(top_widths[i], 7, col, 1, 0, "C", True)
        pdf.ln()

        pdf.set_text_color(26, 26, 46)
        pdf.set_font("Helvetica", "", 8)
        fill = False
        for rank, post in enumerate(data["top_posts"][:10], 1):
            if fill:
                pdf.set_fill_color(245, 245, 245)
            title = (post["title"] or "")[:35]
            if len(post.get("title", "") or "") > 35:
                title += "..."
            pdf.cell(top_widths[0], 6, str(rank), 1, 0, "C", fill)
            pdf.cell(top_widths[1], 6, f"  {title}", 1, 0, "L", fill)
            pdf.cell(top_widths[2], 6, str(post["likes"]), 1, 0, "C", fill)
            pdf.cell(top_widths[3], 6, str(post["comments"]), 1, 0, "C", fill)
            pdf.cell(top_widths[4], 6, f"{post['reach']:,}".replace(",", "."), 1, 0, "C", fill)
            pdf.cell(top_widths[5], 6, f"{post['engagement_rate']}%", 1, 0, "C", fill)
            pdf.ln()
            fill = not fill
        pdf.ln(5)

    # ─── Recommendations ───
    if data["recommendations"]:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 10, "Empfehlungen", ln=True)

        pdf.set_fill_color(253, 248, 220)
        rec_y = pdf.get_y()
        rec_height = len(data["recommendations"]) * 7 + 6
        pdf.rect(10, rec_y, 190, rec_height, "F")
        pdf.set_xy(15, rec_y + 3)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(80, 60, 0)
        for rec in data["recommendations"]:
            pdf.cell(0, 7, f"  > {rec}", ln=True)

    return pdf.output()


# ─── Generate CSV Report ─────────────────────────────────────────────────
def _generate_csv(data: dict) -> str:
    """Generate a CSV report with all post data and metrics."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # Header
    writer.writerow([
        "ID", "Titel", "Kategorie", "Plattform", "Land", "Status",
        "Likes", "Kommentare", "Shares", "Saves", "Reichweite",
        "Engagement Rate (%)", "Erstellt", "Geplant", "Gepostet",
    ])

    for p in data["posts"]:
        likes = p.perf_likes or 0
        comments = p.perf_comments or 0
        shares = p.perf_shares or 0
        reach = p.perf_reach or 0
        eng = round(((likes + comments + shares) / reach) * 100, 2) if reach > 0 else ""

        writer.writerow([
            p.id,
            p.title or "",
            p.category or "",
            p.platform or "",
            p.country or "",
            p.status or "",
            p.perf_likes if p.perf_likes is not None else "",
            p.perf_comments if p.perf_comments is not None else "",
            p.perf_shares if p.perf_shares is not None else "",
            p.perf_saves if p.perf_saves is not None else "",
            p.perf_reach if p.perf_reach is not None else "",
            eng,
            p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
            p.scheduled_date.isoformat() if p.scheduled_date else "",
            p.posted_at.strftime("%Y-%m-%d %H:%M") if p.posted_at else "",
        ])

    return output.getvalue()


# ─── Endpoints ────────────────────────────────────────────────────────────

@router.post("/generate")
async def generate_report(
    body: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a performance report as PDF or CSV.

    Body:
    - period: "week" or "month" (default: "month")
    - format: "pdf" or "csv" (default: "pdf")
    - include_top_posts: bool (default: true)
    - include_recommendations: bool (default: true)
    """
    period = body.get("period", "month")
    report_format = body.get("format", "pdf")

    if period not in ("week", "month"):
        raise HTTPException(status_code=400, detail="Period must be 'week' or 'month'")
    if report_format not in ("pdf", "csv"):
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'csv'")

    # Gather data
    report_data = await _gather_report_data(user_id, period, db)

    # Save to history
    try:
        # Ensure table exists
        async with db.begin_nested():
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS report_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    report_type VARCHAR NOT NULL,
                    period VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    summary TEXT,
                    post_count INTEGER DEFAULT 0,
                    created_at DATETIME
                )
            """))
        history = ReportHistory(
            user_id=user_id,
            report_type=report_format,
            period=period,
            title=f"{report_data['period_label']} - {report_data['date_range']}",
            summary=json.dumps({
                "total_posts": report_data["total_posts"],
                "avg_engagement": report_data["metrics"]["avg_engagement_rate"],
                "total_reach": report_data["metrics"]["total_reach"],
            }),
            post_count=report_data["total_posts"],
            created_at=datetime.now(timezone.utc),
        )
        db.add(history)
        await db.commit()
    except Exception:
        pass  # Best effort history tracking

    if report_format == "pdf":
        pdf_bytes = _generate_pdf(report_data)
        now = datetime.now()
        filename = f"TREFF_{report_data['period_label'].replace(' ', '_')}_{now.strftime('%Y%m%d')}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        csv_content = _generate_csv(report_data)
        now = datetime.now()
        filename = f"TREFF_{report_data['period_label'].replace(' ', '_')}_{now.strftime('%Y%m%d')}.csv"
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@router.get("/history")
async def get_report_history(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get report generation history for the current user."""
    try:
        # Ensure table exists
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS report_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_type VARCHAR NOT NULL,
                period VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                summary TEXT,
                post_count INTEGER DEFAULT 0,
                created_at DATETIME
            )
        """))
        await db.commit()

        result = await db.execute(
            select(ReportHistory)
            .where(ReportHistory.user_id == user_id)
            .order_by(ReportHistory.created_at.desc())
            .limit(20)
        )
        reports = result.scalars().all()

        return [
            {
                "id": r.id,
                "report_type": r.report_type,
                "period": r.period,
                "title": r.title,
                "summary": json.loads(r.summary) if r.summary else None,
                "post_count": r.post_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ]
    except Exception:
        return []


@router.get("/preview")
async def preview_report(
    period: str = Query(default="month", pattern="^(week|month)$"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Preview report data without generating a file. Used for the frontend preview."""
    report_data = await _gather_report_data(user_id, period, db)

    return {
        "period_label": report_data["period_label"],
        "date_range": report_data["date_range"],
        "total_posts": report_data["total_posts"],
        "posts_with_metrics": report_data["posts_with_metrics"],
        "categories": report_data["categories"],
        "platforms": report_data["platforms"],
        "countries": report_data["countries"],
        "statuses": report_data["statuses"],
        "metrics": report_data["metrics"],
        "top_posts": report_data["top_posts"],
        "recommendations": report_data["recommendations"],
    }
