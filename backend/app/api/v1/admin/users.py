from __future__ import annotations

import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user, require_role
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.database import get_db
from app.models.user import User
from app.redis_client import RedisClient, get_redis_client
from app.schemas.user import UserAdminUpdate, UserResponse

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin — Users"],
    dependencies=[Depends(require_role("admin", "owner"))],
)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------
@router.get(
    "/",
    summary="Paginated user list with filters",
)
async def list_users(
    search: Optional[str] = Query(default=None, max_length=100),
    plan: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return a paginated list of all users.
    Supports filtering by search (email/username), plan, role, and active status.
    """
    query = select(User)
    count_query = select(func.count()).select_from(User)

    if search:
        search_filter = or_(
            User.email.ilike(f"%{search}%"),
            User.username.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if plan:
        query = query.where(User.plan == plan)
        count_query = count_query.where(User.plan == plan)

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    total_result = await db.execute(count_query)
    total: int = total_result.scalar_one()

    offset = (page - 1) * limit
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    users = list(result.scalars().all())

    pages = math.ceil(total / limit) if limit > 0 else 1

    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


# ---------------------------------------------------------------------------
# GET /{id}
# ---------------------------------------------------------------------------
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user detail by ID",
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Return full user details for a given user ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User", user_id)
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# PUT /{id}
# ---------------------------------------------------------------------------
@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user plan, role, or active status",
)
async def update_user(
    user_id: UUID,
    payload: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Admin update of a user's plan, role, plan_expires_at, is_active, or is_verified.
    Only non-null fields in the payload are applied.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User", user_id)

    if current_admin.role not in ("owner", "superadmin"):
        if user.role in ("owner", "superadmin"):
            raise ConflictError("Only owner can modify owner accounts.")
        if payload.role in ("owner", "superadmin"):
            raise ConflictError("Only owner can assign the owner role.")

    if payload.plan is not None:
        user.plan = payload.plan
    if payload.role is not None:
        user.role = payload.role
    if payload.plan_expires_at is not None:
        user.plan_expires_at = payload.plan_expires_at
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_verified is not None:
        user.is_verified = payload.is_verified
    if payload.market_access is not None:
        user.market_access = payload.market_access
    # Only owner can grant/revoke QA Lab access
    if payload.qa_access is not None:
        if current_admin.role not in ("owner", "superadmin"):
            raise ConflictError("Only owner can grant QA Lab access.")
        user.qa_access = payload.qa_access

    await db.flush()
    logger.info(
        f"Admin {current_admin.id} updated user {user_id}: "
        f"{payload.model_dump(exclude_none=True)}"
    )
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# DELETE /{id}
# ---------------------------------------------------------------------------
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a user account",
)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_active_user),
) -> Response:
    """
    Permanently delete a user account.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User", user_id)

    if user.id == current_admin.id:
        raise ValidationError("Administrators cannot deactivate their own account.")

    if current_admin.role not in ("owner", "superadmin") and user.role in (
        "owner",
        "superadmin",
    ):
        raise ConflictError("Only owner can delete owner accounts.")

    await db.delete(user)
    await db.flush()
    logger.info(f"Admin {current_admin.id} deleted user {user_id}.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# POST /{id}/reset-device
# ---------------------------------------------------------------------------
@router.post(
    "/{user_id}/reset-device",
    summary="Clear the device fingerprint for a user",
)
async def reset_device_fingerprint(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_active_user),
) -> dict:
    """
    Clear the stored device fingerprint for the specified user.
    The user's next login will bind a new fingerprint.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User", user_id)

    user.device_fingerprint = None
    await db.flush()
    logger.info(f"Admin {current_admin.id} reset device fingerprint for user {user_id}.")

    return {
        "status": "ok",
        "message": f"Device fingerprint cleared for user {user_id}.",
        "user_id": str(user_id),
    }
