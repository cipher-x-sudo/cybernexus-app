from datetime import datetime
from typing import List, Optional
from enum import Enum
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.api.routes.auth import get_current_user, User as UserModel
from app.services.notification import NotificationService, NotificationPriority
from fastapi.security import OAuth2PasswordBearer
from app.config import settings
from jose import JWTError, jwt

router = APIRouter()

_notification_service = NotificationService()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[UserModel]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        
        from app.api.routes.auth import get_user_by_username
        user = await get_user_by_username(db, username=username)
        if user is None or user.disabled:
            return None
        
        return UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled,
            role=user.role,
            onboarding_completed=user.onboarding_completed,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except (JWTError, Exception):
        return None


class ThreatSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ThreatStatus(str, Enum):
    ACTIVE = "active"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class ThreatCategory(str, Enum):
    MALWARE = "malware"
    PHISHING = "phishing"
    DATA_LEAK = "data_leak"
    MISCONFIGURATION = "misconfiguration"
    VULNERABILITY = "vulnerability"
    BRAND_ABUSE = "brand_abuse"
    CREDENTIAL_EXPOSURE = "credential_exposure"
    DARK_WEB_MENTION = "dark_web_mention"


class Threat(BaseModel):
    id: str
    title: str
    description: str
    severity: ThreatSeverity
    status: ThreatStatus = ThreatStatus.ACTIVE
    category: ThreatCategory
    source: str
    score: float
    affected_entities: List[str] = []
    indicators: List[str] = []
    created_at: datetime
    updated_at: datetime
    mitre_tactics: List[str] = []
    recommendations: List[str] = []


class ThreatCreate(BaseModel):
    title: str
    description: str
    severity: ThreatSeverity
    category: ThreatCategory
    source: str
    score: float = 50.0
    affected_entities: List[str] = []
    indicators: List[str] = []
    mitre_tactics: List[str] = []
    recommendations: List[str] = []


class ThreatUpdate(BaseModel):
    status: Optional[ThreatStatus] = None
    severity: Optional[ThreatSeverity] = None
    score: Optional[float] = None
    recommendations: Optional[List[str]] = None


class ThreatStats(BaseModel):
    total: int
    active: int
    critical: int
    high: int
    medium: int
    low: int
    by_category: dict
    avg_score: float


threats_db: dict = {}
threat_counter = 0


def generate_threat_id() -> str:
    global threat_counter
    threat_counter += 1
    return f"THR-{threat_counter:08d}"


def calculate_priority(threat: dict) -> float:
    severity_weights = {
        ThreatSeverity.CRITICAL: 5,
        ThreatSeverity.HIGH: 4,
        ThreatSeverity.MEDIUM: 3,
        ThreatSeverity.LOW: 2,
        ThreatSeverity.INFO: 1
    }
    status_weights = {
        ThreatStatus.ACTIVE: 1.5,
        ThreatStatus.INVESTIGATING: 1.2,
        ThreatStatus.MITIGATED: 0.5,
        ThreatStatus.RESOLVED: 0.1,
        ThreatStatus.FALSE_POSITIVE: 0.0
    }
    
    base_score = threat.get("score", 50)
    severity_mult = severity_weights.get(threat.get("severity"), 1)
    status_mult = status_weights.get(threat.get("status"), 1)
    
    return base_score * severity_mult * status_mult


@router.get("/", response_model=List[Threat])
async def list_threats(
    severity: Optional[ThreatSeverity] = None,
    status: Optional[ThreatStatus] = None,
    category: Optional[ThreatCategory] = None,
    source: Optional[str] = None,
    min_score: float = Query(default=0, ge=0, le=100),
    sort_by: str = Query(default="score", regex="^(score|created_at|severity)$"),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0)
):
    results = list(threats_db.values())
    
    if severity:
        results = [t for t in results if t["severity"] == severity]
    if status:
        results = [t for t in results if t["status"] == status]
    if category:
        results = [t for t in results if t["category"] == category]
    if source:
        results = [t for t in results if t["source"] == source]
    if min_score > 0:
        results = [t for t in results if t["score"] >= min_score]
    
    if sort_by == "score":
        results.sort(key=lambda t: calculate_priority(t), reverse=True)
    elif sort_by == "created_at":
        results.sort(key=lambda t: t["created_at"], reverse=True)
    elif sort_by == "severity":
        severity_order = ["critical", "high", "medium", "low", "info"]
        results.sort(key=lambda t: severity_order.index(t["severity"]))
    
    results = results[offset:offset + limit]
    
    return [Threat(**t) for t in results]


@router.get("/top", response_model=List[Threat])
async def get_top_threats(n: int = Query(default=10, ge=1, le=100)):
    results = list(threats_db.values())
    
    results.sort(key=lambda t: calculate_priority(t), reverse=True)
    
    return [Threat(**t) for t in results[:n]]


@router.get("/stats", response_model=ThreatStats)
async def get_threat_stats():
    threats = list(threats_db.values())
    
    by_category = {}
    total_score = 0
    
    for t in threats:
        cat = t["category"]
        by_category[cat] = by_category.get(cat, 0) + 1
        total_score += t["score"]
    
    active_count = len([t for t in threats if t["status"] == ThreatStatus.ACTIVE])
    critical_count = len([t for t in threats if t["severity"] == ThreatSeverity.CRITICAL])
    high_count = len([t for t in threats if t["severity"] == ThreatSeverity.HIGH])
    medium_count = len([t for t in threats if t["severity"] == ThreatSeverity.MEDIUM])
    low_count = len([t for t in threats if t["severity"] == ThreatSeverity.LOW])
    
    return ThreatStats(
        total=len(threats),
        active=active_count,
        critical=critical_count,
        high=high_count,
        medium=medium_count,
        low=low_count,
        by_category=by_category,
        avg_score=total_score / len(threats) if threats else 0
    )


@router.get("/{threat_id}", response_model=Threat)
async def get_threat(threat_id: str):
    if threat_id not in threats_db:
        raise HTTPException(status_code=404, detail="Threat not found")
    return Threat(**threats_db[threat_id])


@router.post("/", response_model=Threat)
async def create_threat(
    threat: ThreatCreate,
    current_user: Optional[UserModel] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    now = datetime.utcnow()
    threat_id = generate_threat_id()
    
    threat_dict = {
        "id": threat_id,
        "title": threat.title,
        "description": threat.description,
        "severity": threat.severity,
        "status": ThreatStatus.ACTIVE,
        "category": threat.category,
        "source": threat.source,
        "score": threat.score,
        "affected_entities": threat.affected_entities,
        "indicators": threat.indicators,
        "created_at": now,
        "updated_at": now,
        "mitre_tactics": threat.mitre_tactics,
        "recommendations": threat.recommendations
    }
    
    threats_db[threat_id] = threat_dict
    
    if current_user:
        try:
            severity_map = {
                ThreatSeverity.CRITICAL: (NotificationPriority.CRITICAL, "critical"),
                ThreatSeverity.HIGH: (NotificationPriority.HIGH, "high"),
                ThreatSeverity.MEDIUM: (NotificationPriority.MEDIUM, "medium"),
                ThreatSeverity.LOW: (NotificationPriority.LOW, "low"),
                ThreatSeverity.INFO: (NotificationPriority.INFO, "info"),
            }
            priority, severity = severity_map.get(threat.severity, (NotificationPriority.MEDIUM, "medium"))
            
            await _notification_service.create_notification(
                db=db,
                user_id=current_user.id,
                channel="threats",
                priority=priority,
                title=f"New Threat: {threat.title}",
                message=threat.description,
                severity=severity,
                metadata={
                    "threat_id": threat_id,
                    "category": threat.category.value,
                    "source": threat.source,
                    "score": threat.score,
                }
            )
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to create notification for threat {threat_id}: {e}")
    
    return Threat(**threat_dict)


@router.put("/{threat_id}", response_model=Threat)
async def update_threat(threat_id: str, threat: ThreatUpdate):
    if threat_id not in threats_db:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    threat_dict = threats_db[threat_id]
    
    if threat.status is not None:
        threat_dict["status"] = threat.status
    if threat.severity is not None:
        threat_dict["severity"] = threat.severity
    if threat.score is not None:
        threat_dict["score"] = threat.score
    if threat.recommendations is not None:
        threat_dict["recommendations"] = threat.recommendations
    
    threat_dict["updated_at"] = datetime.utcnow()
    
    return Threat(**threat_dict)


@router.delete("/{threat_id}")
async def delete_threat(threat_id: str):
    if threat_id not in threats_db:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    del threats_db[threat_id]
    return {"message": "Threat deleted successfully"}


