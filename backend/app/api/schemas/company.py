from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class Address(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = Field(None, alias="zip")


class KeyAsset(BaseModel):
    name: str
    type: str
    value: str
    description: Optional[str] = None


class AutomationCapabilityConfig(BaseModel):
    enabled: bool = True
    targets: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class AutomationSchedule(BaseModel):
    cron: str = Field(..., description="Cron expression (e.g., '0 9 * * *' for daily at 9 AM)")
    timezone: str = Field(default="UTC", description="Timezone for schedule execution")


class AutomationConfig(BaseModel):
    enabled: bool = Field(default=True, description="Whether automation is enabled")
    schedule: AutomationSchedule
    capabilities: Dict[str, AutomationCapabilityConfig] = Field(
        default_factory=dict,
        description="Configuration for each capability (exposure_discovery, darkweb_intelligence, email_audit, infrastructure_testing, investigation)"
    )


class CompanyProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industry: Optional[str] = None
    company_size: Optional[str] = None
    description: Optional[str] = None
    
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    address: Optional[Address] = None
    
    primary_domain: Optional[str] = None
    additional_domains: List[str] = Field(default_factory=list)
    ip_ranges: List[str] = Field(default_factory=list)
    key_assets: List[KeyAsset] = Field(default_factory=list)
    
    logo_url: Optional[str] = None
    timezone: Optional[str] = "UTC"
    locale: Optional[str] = "en-US"
    automation_config: Optional[AutomationConfig] = None
    
    @field_validator("primary_domain", "additional_domains", mode="before")
    @classmethod
    def validate_domains(cls, v):
        if v is None:
            return v
        if isinstance(v, list):
            for domain in v:
                if domain and not cls._is_valid_domain(domain):
                    raise ValueError(f"Invalid domain format: {domain}")
            return v
        if v and not cls._is_valid_domain(v):
            raise ValueError(f"Invalid domain format: {v}")
        return v
    
    @field_validator("ip_ranges", mode="before")
    @classmethod
    def validate_ip_ranges(cls, v):
        if not v:
            return v
        if isinstance(v, list):
            for ip_range in v:
                if ip_range and not cls._is_valid_ip_or_cidr(ip_range):
                    raise ValueError(f"Invalid IP range format: {ip_range}")
            return v
        return v
    
    @staticmethod
    def _is_valid_domain(domain: str) -> bool:
        if not domain:
            return False
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))
    
    @staticmethod
    def _is_valid_ip_or_cidr(ip_range: str) -> bool:
        if not ip_range:
            return False
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$'
        if re.match(ip_pattern, ip_range):
            parts = ip_range.split('/')
            if len(parts) == 1:
                return True
            try:
                prefix = int(parts[1])
                return 0 <= prefix <= 32
            except ValueError:
                return False
        return False


class CompanyProfileCreate(CompanyProfileBase):
    pass


class CompanyProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    industry: Optional[str] = None
    company_size: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    address: Optional[Address] = None
    primary_domain: Optional[str] = None
    additional_domains: Optional[List[str]] = None
    ip_ranges: Optional[List[str]] = None
    key_assets: Optional[List[KeyAsset]] = None
    logo_url: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    automation_config: Optional[AutomationConfig] = None
    
    @field_validator("primary_domain", "additional_domains", mode="before")
    @classmethod
    def validate_domains(cls, v):
        return CompanyProfileBase.validate_domains(v)
    
    @field_validator("ip_ranges", mode="before")
    @classmethod
    def validate_ip_ranges(cls, v):
        return CompanyProfileBase.validate_ip_ranges(v)


class CompanyProfile(CompanyProfileBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class AutomationSyncResponse(BaseModel):
    success: bool
    message: str
    scheduled_search_ids: List[str] = Field(default_factory=list)
    capabilities_synced: List[str] = Field(default_factory=list)

