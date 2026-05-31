from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.rate_limit import RATE_LIMITS, user_limiter
from app.db.session import get_async_session
from models.saved_paper import SavedPaper
from schemas.saved_paper import SavedPaperCreate, SavedPaperList, SavedPaperOut

router = APIRouter()


@router.post("/saved", response_model=SavedPaperOut, status_code=201)
@user_limiter.limit(RATE_LIMITS["saved_papers"])
async def create_saved(
    request: Request,
    data: SavedPaperCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
) -> SavedPaper:
    """Save a paper. Requires authentication."""
    paper = SavedPaper(**data.model_dump(), user_id=current_user.id)
    session.add(paper)
    await session.commit()
    await session.refresh(paper)
    return paper


@router.get("/saved", response_model=SavedPaperList)
@user_limiter.limit(RATE_LIMITS["saved_papers"])
async def list_saved(
    request: Request,
    current_user: CurrentUser,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
) -> SavedPaperList:
    """List saved papers for the current user."""
    result = await session.execute(
        select(SavedPaper)
        .where(SavedPaper.user_id == current_user.id)
        .order_by(SavedPaper.saved_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = result.scalars().all()
    count_result = await session.execute(
        select(func.count(SavedPaper.id)).where(SavedPaper.user_id == current_user.id)
    )
    total = count_result.scalar_one()
    return SavedPaperList(total=total, items=items)


@router.get("/saved/{paper_id}", response_model=SavedPaperOut)
@user_limiter.limit(RATE_LIMITS["saved_papers"])
async def get_saved(
    request: Request,
    paper_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
) -> SavedPaper:
    """Get a specific saved paper. Must belong to the current user."""
    paper = await session.get(SavedPaper, paper_id)
    if paper is None or paper.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Saved paper not found")
    return paper


@router.delete("/saved/{paper_id}", status_code=204)
@user_limiter.limit(RATE_LIMITS["saved_papers"])
async def delete_saved(
    request: Request,
    paper_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Delete a saved paper. Must belong to the current user."""
    paper = await session.get(SavedPaper, paper_id)
    if paper is None or paper.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Saved paper not found")
    await session.delete(paper)
    await session.commit()
