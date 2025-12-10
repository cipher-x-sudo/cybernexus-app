"""
Company Profile Routes

Handles company profile CRUD operations.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.schemas.company import (
    CompanyProfile,
    CompanyProfileCreate,
    CompanyProfileUpdate,
)

router = APIRouter()

# Profile storage path
PROFILE_DIR = settings.DATA_DIR / "profiles"
PROFILE_FILE = PROFILE_DIR / "company_profile.json"
PROFILE_ID = "company_profile_001"  # Single profile instance


def _ensure_profile_directory():
    """Ensure profile directory exists."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def _load_profile() -> Optional[dict]:
    """Load company profile from disk."""
    if not PROFILE_FILE.exists():
        return None
    
    try:
        with open(PROFILE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _save_profile(profile_data: dict) -> dict:
    """Save company profile to disk atomically."""
    _ensure_profile_directory()
    
    # Write to temp file first, then rename (atomic on most filesystems)
    temp_file = PROFILE_FILE.with_suffix('.json.tmp')
    
    try:
        with open(temp_file, 'w') as f:
            json.dump(profile_data, f, indent=2, default=str)
        
        # Atomic rename
        temp_file.replace(PROFILE_FILE)
        return profile_data
    except Exception as e:
        # Clean up temp file on error
        if temp_file.exists():
            temp_file.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save profile: {str(e)}"
        )


def _create_profile_dict(profile: CompanyProfileCreate, profile_id: str = None) -> dict:
    """Create profile dictionary from model."""
    now = datetime.utcnow()
    profile_dict = profile.model_dump(exclude_unset=True)
    
    return {
        "id": profile_id or PROFILE_ID,
        **profile_dict,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


def _update_profile_dict(existing: dict, update: CompanyProfileUpdate) -> dict:
    """Update existing profile with new data."""
    update_dict = update.model_dump(exclude_unset=True)
    
    # Handle nested address update
    if "address" in update_dict and existing.get("address"):
        existing_addr = existing["address"]
        new_addr = update_dict["address"]
        if isinstance(new_addr, dict):
            existing_addr.update(new_addr)
            update_dict["address"] = existing_addr
    
    existing.update(update_dict)
    existing["updated_at"] = datetime.utcnow().isoformat()
    
    return existing


@router.get("/profile", response_model=CompanyProfile)
async def get_company_profile():
    """Get current company profile."""
    profile = _load_profile()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found. Please create a profile first."
        )
    
    return CompanyProfile(**profile)


@router.post("/profile", response_model=CompanyProfile, status_code=status.HTTP_201_CREATED)
async def create_company_profile(profile: CompanyProfileCreate):
    """Create a new company profile."""
    # Check if profile already exists
    existing = _load_profile()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company profile already exists. Use PUT or PATCH to update."
        )
    
    # Create and save profile
    profile_dict = _create_profile_dict(profile)
    saved = _save_profile(profile_dict)
    
    return CompanyProfile(**saved)


@router.put("/profile", response_model=CompanyProfile)
async def update_company_profile(profile: CompanyProfileCreate):
    """Update company profile (full replace)."""
    existing = _load_profile()
    
    if existing:
        # Update existing profile
        profile_dict = _create_profile_dict(profile, existing["id"])
        profile_dict["created_at"] = existing.get("created_at", datetime.utcnow().isoformat())
    else:
        # Create new profile
        profile_dict = _create_profile_dict(profile)
    
    saved = _save_profile(profile_dict)
    return CompanyProfile(**saved)


@router.patch("/profile", response_model=CompanyProfile)
async def patch_company_profile(profile: CompanyProfileUpdate):
    """Partially update company profile."""
    existing = _load_profile()
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found. Use POST to create a new profile."
        )
    
    # Merge updates
    updated = _update_profile_dict(existing, profile)
    saved = _save_profile(updated)
    
    return CompanyProfile(**saved)


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_profile():
    """Delete company profile."""
    if not PROFILE_FILE.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    try:
        PROFILE_FILE.unlink()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )
    
    return None
