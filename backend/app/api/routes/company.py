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
    AutomationSyncResponse,
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
        "automation_config": profile.automation_config,
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
        automation_config=profile_data.get("automation_config"),
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
        existing.automation_config = profile_data.get("automation_config")
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
            automation_config=profile_data.get("automation_config"),
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


@router.post("/automation/sync", response_model=AutomationSyncResponse)
async def sync_automation_to_scheduler(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync company profile automation config to scheduled searches.
    
    This endpoint:
    1. Reads the company profile's automation_config
    2. Deletes old scheduled searches with metadata source='company_automation'
    3. Creates new scheduled searches for each enabled capability
    4. Returns created schedule IDs
    """
    from app.core.database.models import ScheduledSearch
    from loguru import logger
    import uuid
    from croniter import croniter
    from datetime import datetime, timezone
    import pytz
    
    # Get company profile
    result = await db.execute(
        select(CompanyProfileModel).where(CompanyProfileModel.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    automation_config = profile.automation_config
    
    if not automation_config or not automation_config.get("enabled"):
        # Delete any existing automation schedules
        from sqlalchemy import delete as delete_query
        await db.execute(
            delete_query(ScheduledSearch).where(
                ScheduledSearch.user_id == current_user.id,
                ScheduledSearch.config["metadata"]["source"].astext == "company_automation"
            )
        )
        await db.commit()
        
        return AutomationSyncResponse(
            success=True,
            message="Automation is disabled. Removed all automation schedules.",
            scheduled_search_ids=[],
            capabilities_synced=[]
        )
    
    # Delete old automation schedules
    try:
        from sqlalchemy import delete as delete_query
        await db.execute(
            delete_query(ScheduledSearch).where(
                ScheduledSearch.user_id == current_user.id,
                ScheduledSearch.config["metadata"]["source"].astext == "company_automation"
            )
        )
    except Exception as e:
        logger.warning(f"Error deleting old automation schedules: {e}")
    
    # Get schedule config
    schedule_config = automation_config.get("schedule", {})
    cron_expression = schedule_config.get("cron", "0 9 * * *")
    tz_name = schedule_config.get("timezone", profile.timezone or "UTC")
    
    # Validate cron expression
    try:
        croniter(cron_expression)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cron expression: {cron_expression}. Error: {str(e)}"
        )
    
    # Calculate next run time
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        cron = croniter(cron_expression, now)
        next_run = cron.get_next(datetime)
    except Exception as e:
        logger.error(f"Error calculating next run time: {e}")
        next_run = datetime.now(timezone.utc)
    
    # Create scheduled searches for each enabled capability
    capabilities_config = automation_config.get("capabilities", {})
    created_ids = []
    synced_capabilities = []
    
    for capability_name, cap_config in capabilities_config.items():
        if not cap_config.get("enabled", False):
            continue
        
        # Get targets
        targets = cap_config.get("targets", [])
        if not targets:
            # Try to auto-populate from profile
            if capability_name in ["exposure_discovery", "email_audit"]:
                targets = [profile.primary_domain] if profile.primary_domain else []
                targets.extend(profile.additional_domains or [])
            elif capability_name in ["infrastructure_testing", "investigation"]:
                # Use key_assets URLs or domains
                if profile.key_assets:
                    for asset in profile.key_assets:
                        if asset.get("type") in ["domain", "url", "server"]:
                            targets.append(asset.get("value"))
                if not targets and profile.primary_domain:
                    targets = [f"https://{profile.primary_domain}"]
        
        if not targets:
            logger.warning(f"No targets found for capability {capability_name}, skipping")
            continue
        
        # For dark web, add keywords
        keywords = cap_config.get("keywords", [])
        if capability_name == "darkweb_intelligence":
            # Auto-add company name and domains as keywords
            if profile.name and profile.name not in keywords:
                keywords.append(profile.name)
            if profile.primary_domain and profile.primary_domain not in keywords:
                keywords.append(profile.primary_domain)
        
        # Create target string (comma-separated for multiple targets)
        target_str = ", ".join(targets) if len(targets) > 1 else targets[0] if targets else ""
        if capability_name == "darkweb_intelligence" and keywords:
            target_str = ", ".join(keywords)
        
        if not target_str:
            continue
        
        # Create scheduled search
        scheduled_search = ScheduledSearch(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            name=f"Auto: {capability_name.replace('_', ' ').title()}",
            description=f"Automated scan from company profile",
            capabilities=[capability_name],
            target=target_str,
            config={
                "capability_config": cap_config.get("config", {}),
                "metadata": {
                    "source": "company_automation",
                    "profile_id": profile.id,
                    "targets": targets,
                    "keywords": keywords if capability_name == "darkweb_intelligence" else []
                }
            },
            schedule_type="cron",
            cron_expression=cron_expression,
            timezone=tz_name,
            enabled=True,
            next_run_at=next_run,
            run_count=0
        )
        
        db.add(scheduled_search)
        created_ids.append(scheduled_search.id)
        synced_capabilities.append(capability_name)
    
    await db.commit()
    
    # Log activity
    await log_activity(
        db=db,
        user_id=current_user.id,
        action="sync_automation",
        resource_type="company_profile",
        resource_id=profile.id,
        metadata={"scheduled_searches": created_ids, "capabilities": synced_capabilities}
    )
    
    return AutomationSyncResponse(
        success=True,
        message=f"Successfully synced {len(created_ids)} scheduled searches",
        scheduled_search_ids=created_ids,
        capabilities_synced=synced_capabilities
    )

