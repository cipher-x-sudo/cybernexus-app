"""
Company Profile Routes

Handles company profile CRUD operations - user-scoped.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database.database import get_db
from app.core.database.models import CompanyProfile as CompanyProfileModel, User as UserModel
from app.api.routes.auth import get_current_active_user, User
from app.api.schemas.company import (
    CompanyProfile,
    CompanyProfileCreate,
    CompanyProfileUpdate,
)
from app.services.activity_logger import log_activity

router = APIRouter()


def _model_to_dict(profile: CompanyProfileModel) -> dict:
    """Convert CompanyProfile model to dict."""
    return {
        "id": profile.id,
        "name": profile.name,
        "industry": profile.industry,
        "company_size": profile.company_size,
        "description": profile.description,
        "phone": profile.phone,
        "email": profile.email,
        "website": profile.website,
        "primary_domain": profile.primary_domain,
        "additional_domains": profile.additional_domains or [],
        "ip_ranges": profile.ip_ranges or [],
        "key_assets": profile.key_assets or [],
        "address": profile.address,
        "logo_url": profile.logo_url,
        "timezone": profile.timezone or "UTC",
        "locale": profile.locale or "en-US",
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


@router.get("/profile", response_model=CompanyProfile)
async def get_company_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's company profile."""
    result = await db.execute(
        select(CompanyProfileModel).where(CompanyProfileModel.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found. Please create a profile first."
        )
    
    return CompanyProfile(**_model_to_dict(profile))


@router.post("/profile", response_model=CompanyProfile, status_code=status.HTTP_201_CREATED)
async def create_company_profile(
    profile: CompanyProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new company profile for current user."""
    # Check if profile already exists
    result = await db.execute(
        select(CompanyProfileModel).where(CompanyProfileModel.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company profile already exists. Use PUT or PATCH to update."
        )
    
    # Create new profile
    import uuid
    profile_data = profile.model_dump()
    db_profile = CompanyProfileModel(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=profile_data["name"],
        industry=profile_data.get("industry"),
        company_size=profile_data.get("company_size"),
        description=profile_data.get("description"),
        phone=profile_data.get("phone"),
        email=profile_data.get("email"),
        website=profile_data.get("website"),
        primary_domain=profile_data.get("primary_domain"),
        additional_domains=profile_data.get("additional_domains", []),
        ip_ranges=profile_data.get("ip_ranges", []),
        key_assets=profile_data.get("key_assets", []),
        address=profile_data.get("address"),
        logo_url=profile_data.get("logo_url"),
        timezone=profile_data.get("timezone", "UTC"),
        locale=profile_data.get("locale", "en-US"),
    )
    
    db.add(db_profile)
    
    # Mark onboarding as completed
    user_result = await db.execute(
        select(UserModel).where(UserModel.id == current_user.id)
    )
    user = user_result.scalar_one()
    user.onboarding_completed = True
    
    await db.commit()
    await db.refresh(db_profile)
    
    # Log activity
    await log_activity(
        db=db,
        user_id=current_user.id,
        action="create",
        resource_type="company_profile",
        resource_id=db_profile.id
    )
    
    return CompanyProfile(**_model_to_dict(db_profile))


@router.put("/profile", response_model=CompanyProfile)
async def update_company_profile(
    profile: CompanyProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update company profile (full replace)."""
    result = await db.execute(
        select(CompanyProfileModel).where(CompanyProfileModel.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    profile_data = profile.model_dump()
    
    if existing:
        # Update existing profile
        existing.name = profile_data["name"]
        existing.industry = profile_data.get("industry")
        existing.company_size = profile_data.get("company_size")
        existing.description = profile_data.get("description")
        existing.phone = profile_data.get("phone")
        existing.email = profile_data.get("email")
        existing.website = profile_data.get("website")
        existing.primary_domain = profile_data.get("primary_domain")
        existing.additional_domains = profile_data.get("additional_domains", [])
        existing.ip_ranges = profile_data.get("ip_ranges", [])
        existing.key_assets = profile_data.get("key_assets", [])
        existing.address = profile_data.get("address")
        existing.logo_url = profile_data.get("logo_url")
        existing.timezone = profile_data.get("timezone", "UTC")
        existing.locale = profile_data.get("locale", "en-US")
        existing.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(existing)
        
        # Log activity
        await log_activity(
            db=db,
            user_id=current_user.id,
            action="update",
            resource_type="company_profile",
            resource_id=existing.id
        )
        
        return CompanyProfile(**_model_to_dict(existing))
    else:
        # Create new profile (same as POST)
        import uuid
        db_profile = CompanyProfileModel(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            name=profile_data["name"],
            industry=profile_data.get("industry"),
            company_size=profile_data.get("company_size"),
            description=profile_data.get("description"),
            phone=profile_data.get("phone"),
            email=profile_data.get("email"),
            website=profile_data.get("website"),
            primary_domain=profile_data.get("primary_domain"),
            additional_domains=profile_data.get("additional_domains", []),
            ip_ranges=profile_data.get("ip_ranges", []),
            key_assets=profile_data.get("key_assets", []),
            address=profile_data.get("address"),
            logo_url=profile_data.get("logo_url"),
            timezone=profile_data.get("timezone", "UTC"),
            locale=profile_data.get("locale", "en-US"),
        )
        
        db.add(db_profile)
        
        # Mark onboarding as completed
        user_result = await db.execute(
            select(UserModel).where(UserModel.id == current_user.id)
        )
        user = user_result.scalar_one()
        user.onboarding_completed = True
        
        await db.commit()
        await db.refresh(db_profile)
        
        return CompanyProfile(**_model_to_dict(db_profile))


@router.patch("/profile", response_model=CompanyProfile)
async def patch_company_profile(
    profile: CompanyProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Partially update company profile."""
    result = await db.execute(
        select(CompanyProfileModel).where(CompanyProfileModel.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found. Use POST to create a new profile."
        )
    
    # Merge updates
    update_data = profile.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(existing, key):
            setattr(existing, key, value)
    
    existing.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(existing)
    
    # Log activity
    await log_activity(
        db=db,
        user_id=current_user.id,
        action="update",
        resource_type="company_profile",
        resource_id=existing.id
    )
    
    return CompanyProfile(**_model_to_dict(existing))


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete company profile."""
    result = await db.execute(
        select(CompanyProfileModel).where(CompanyProfileModel.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    from sqlalchemy import delete
    await db.execute(
        delete(CompanyProfileModel).where(CompanyProfileModel.id == profile.id)
    )
    await db.commit()
    
    return None
