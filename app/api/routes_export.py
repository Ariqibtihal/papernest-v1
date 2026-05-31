from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.rate_limit import RATE_LIMITS, user_limiter
from schemas.paper import PaperDTO
from utils.export import export_bibtex, export_csv, export_json

router = APIRouter()


@router.post("/export")
@user_limiter.limit(RATE_LIMITS["export"])
async def export_papers(
    request: Request,
    papers: list[PaperDTO],
    format: str = Query("json", enum=["json", "csv", "bibtex"]),
) -> PlainTextResponse:
    if format == "bibtex":
        content = export_bibtex(papers)
        return PlainTextResponse(
            content,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=export.bib"},
        )
    if format == "csv":
        content = export_csv(papers)
        return PlainTextResponse(
            content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"},
        )
    content = export_json(papers)
    return PlainTextResponse(
        content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=export.json"},
    )
