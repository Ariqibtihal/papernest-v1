from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.rate_limit import RATE_LIMITS, user_limiter
from app.db.session import get_async_session
from models.search_alert import SearchAlert
from schemas.search_alert import SearchAlertCreate, SearchAlertList, SearchAlertOut

router = APIRouter()


@router.post("/alerts", response_model=SearchAlertOut, status_code=201)
@user_limiter.limit(RATE_LIMITS["alerts"])
async def create_alert(
    request: Request,
    data: SearchAlertCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
) -> SearchAlert:
    """Create a search alert. Requires authentication."""
    alert = SearchAlert(**data.model_dump(), user_id=current_user.id)
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


@router.get("/alerts", response_model=SearchAlertList)
@user_limiter.limit(RATE_LIMITS["alerts"])
async def list_alerts(
    request: Request,
    current_user: CurrentUser,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
) -> SearchAlertList:
    """List alerts for the current user."""
    result = await session.execute(
        select(SearchAlert)
        .where(SearchAlert.user_id == current_user.id)
        .order_by(SearchAlert.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = result.scalars().all()
    count_result = await session.execute(
        select(func.count(SearchAlert.id)).where(SearchAlert.user_id == current_user.id)
    )
    total = count_result.scalar_one()
    return SearchAlertList(total=total, items=items)


@router.get("/alerts/{alert_id}", response_model=SearchAlertOut)
@user_limiter.limit(RATE_LIMITS["alerts"])
async def get_alert(
    request: Request,
    alert_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
) -> SearchAlert:
    """Get a specific alert. Must belong to the current user."""
    alert = await session.get(SearchAlert, alert_id)
    if alert is None or alert.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/alerts/{alert_id}/toggle", response_model=SearchAlertOut)
@user_limiter.limit(RATE_LIMITS["alerts"])
async def toggle_alert(
    request: Request,
    alert_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
) -> SearchAlert:
    """Toggle alert active state. Must belong to the current user."""
    alert = await session.get(SearchAlert, alert_id)
    if alert is None or alert.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = not alert.is_active
    await session.commit()
    await session.refresh(alert)
    return alert


@router.delete("/alerts/{alert_id}", status_code=204)
@user_limiter.limit(RATE_LIMITS["alerts"])
async def delete_alert(
    request: Request,
    alert_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Delete an alert. Must belong to the current user."""
    alert = await session.get(SearchAlert, alert_id)
    if alert is None or alert.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    await session.delete(alert)
    await session.commit()
