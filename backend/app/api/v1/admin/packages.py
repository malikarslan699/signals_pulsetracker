from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field

from app.core.auth import get_current_active_user, require_role
from app.models.user import User
from app.redis_client import RedisClient, get_redis_client
from app.services.package_config_service import (
    PackageDefinition,
    PackageFeatureFlags,
    PackagesConfig,
    get_package,
    load_packages_config,
    save_packages_config,
)

router = APIRouter(
    prefix="/admin/packages",
    tags=["Admin — Packages"],
    dependencies=[Depends(require_role("admin", "owner"))],
)


# ---------------------------------------------------------------------------
# GET /  — list all packages
# ---------------------------------------------------------------------------
@router.get("/", summary="List all package definitions")
async def list_packages(
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    config = await load_packages_config(redis)
    return {"packages": [p.model_dump() for p in config.packages]}


# ---------------------------------------------------------------------------
# PUT /{slug}  — create or replace a package
# ---------------------------------------------------------------------------
@router.put("/{slug}", summary="Create or update a package definition")
async def upsert_package(
    slug: str,
    payload: PackageDefinition,
    redis: RedisClient = Depends(get_redis_client),
    current_admin: User = Depends(get_current_active_user),
) -> dict:
    if payload.slug != slug:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Slug in URL and body must match.",
        )
    config = await load_packages_config(redis)
    idx = next((i for i, p in enumerate(config.packages) if p.slug == slug), None)
    if idx is not None:
        config.packages[idx] = payload
        action = "updated"
    else:
        config.packages.append(payload)
        action = "created"
    config.packages.sort(key=lambda p: p.sort_order)
    await save_packages_config(redis, config)
    logger.info(
        f"Package '{slug}' {action} by {current_admin.role} {current_admin.id}"
    )
    return {"package": payload.model_dump(), "action": action}


# ---------------------------------------------------------------------------
# PATCH /{slug}/features  — update only feature flags
# ---------------------------------------------------------------------------
@router.patch("/{slug}/features", summary="Update feature flags for a package")
async def update_package_features(
    slug: str,
    payload: PackageFeatureFlags,
    redis: RedisClient = Depends(get_redis_client),
    current_admin: User = Depends(get_current_active_user),
) -> dict:
    config = await load_packages_config(redis)
    pkg = get_package(config, slug)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Package '{slug}' not found.")
    pkg.features = payload
    await save_packages_config(redis, config)
    logger.info(
        f"Package '{slug}' features updated by {current_admin.role} {current_admin.id}"
    )
    return {"package": pkg.model_dump()}


# ---------------------------------------------------------------------------
# PATCH /{slug}/toggle  — enable / disable package
# ---------------------------------------------------------------------------
@router.patch("/{slug}/toggle", summary="Enable or disable a package")
async def toggle_package(
    slug: str,
    redis: RedisClient = Depends(get_redis_client),
    current_admin: User = Depends(get_current_active_user),
) -> dict:
    config = await load_packages_config(redis)
    pkg = get_package(config, slug)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Package '{slug}' not found.")
    pkg.is_active = not pkg.is_active
    await save_packages_config(redis, config)
    logger.info(
        f"Package '{slug}' {'enabled' if pkg.is_active else 'disabled'} "
        f"by {current_admin.role} {current_admin.id}"
    )
    return {"slug": slug, "is_active": pkg.is_active}


# ---------------------------------------------------------------------------
# DELETE /{slug}  — remove a custom package (cannot delete core plans)
# ---------------------------------------------------------------------------
CORE_PLANS = {"trial", "monthly", "yearly", "lifetime"}


@router.delete("/{slug}", summary="Delete a non-core package")
async def delete_package(
    slug: str,
    redis: RedisClient = Depends(get_redis_client),
    current_admin: User = Depends(get_current_active_user),
) -> dict:
    if slug in CORE_PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete core plan '{slug}'. Disable it instead.",
        )
    config = await load_packages_config(redis)
    before = len(config.packages)
    config.packages = [p for p in config.packages if p.slug != slug]
    if len(config.packages) == before:
        raise HTTPException(status_code=404, detail=f"Package '{slug}' not found.")
    await save_packages_config(redis, config)
    logger.info(
        f"Package '{slug}' deleted by {current_admin.role} {current_admin.id}"
    )
    return {"deleted": slug}
