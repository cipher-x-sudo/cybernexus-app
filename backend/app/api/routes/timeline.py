"""
Timeline Routes

Handles event timeline management and querying.
Uses custom Doubly Linked List DSA for efficient traversal.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from enum import Enum
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.core.database.job_storage import DBJobStorage
from app.core.database.finding_storage import DBFindingStorage
from app.api.routes.auth import get_current_active_user, User

router = APIRouter()


class EventType(str, Enum):
    """Types of timeline events."""
    THREAT_DETECTED = "threat_detected"
    ENTITY_DISCOVERED = "entity_discovered"
    SCAN_COMPLETED = "scan_completed"
    ALERT_TRIGGERED = "alert_triggered"
    CREDENTIAL_LEAKED = "credential_leaked"
    DARK_WEB_MENTION = "dark_web_mention"
    CONFIG_ISSUE = "config_issue"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"


class EventSeverity(str, Enum):
    """Event severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TimelineEvent(BaseModel):
    """Timeline event model."""
    id: str
    type: EventType
    title: str
    description: str
    severity: EventSeverity
    timestamp: datetime
    source: str
    related_entities: List[str] = []
    metadata: dict = {}


class EventCreate(BaseModel):
    """Create event request."""
    type: EventType
    title: str
    description: str
    severity: EventSeverity
    source: str
    related_entities: List[str] = []
    metadata: dict = {}


class TimelineStats(BaseModel):
    """Timeline statistics."""
    total_events: int
    events_24h: int
    events_7d: int
    by_type: dict
    by_severity: dict


# In-memory event store (will be replaced with custom Doubly Linked List DSA)
events_db: List[dict] = []
event_counter = 0

# Events will be populated from real collector activity
# No sample data - events are created dynamically from collectors


def generate_event_id() -> str:
    """Generate a unique event ID."""
    global event_counter
    event_counter += 1
    return f"EVT-{event_counter:08d}"


@router.get("", response_model=List[TimelineEvent])
@router.get("/", response_model=List[TimelineEvent])
async def get_timeline(
    event_type: Optional[EventType] = None,
    severity: Optional[EventSeverity] = None,
    source: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="desc", regex="^(asc|desc)$"),
    # Support frontend parameter names
    type: Optional[str] = None,
    from_date: Optional[str] = None,
    to: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get timeline events with optional filtering. Generates events from database if in-memory store is empty."""
    results = events_db.copy()
    
    # If in-memory store is empty, generate events from database (same logic as /recent)
    if not results:
        try:
            # Generate events from recent jobs
            job_storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
            recent_jobs = await job_storage.list_jobs(limit=100, offset=0)
            
            for job in recent_jobs:
                if job.status.value == "completed" and job.completed_at:
                    event = {
                        "id": generate_event_id(),
                        "type": EventType.SCAN_COMPLETED.value,
                        "title": f"Scan completed: {job.capability.value} on {job.target}",
                        "description": f"Completed {job.capability.value} scan for {job.target}",
                        "severity": EventSeverity.INFO.value,
                        "timestamp": job.completed_at,
                        "source": job.capability.value,
                        "related_entities": [job.target],
                        "metadata": {"job_id": job.id, "capability": job.capability.value}
                    }
                    results.append(event)
                elif job.status.value == "running" and job.started_at:
                    event = {
                        "id": generate_event_id(),
                        "type": EventType.SCAN_COMPLETED.value,
                        "title": f"Scan started: {job.capability.value} on {job.target}",
                        "description": f"Started {job.capability.value} scan for {job.target}",
                        "severity": EventSeverity.INFO.value,
                        "timestamp": job.started_at,
                        "source": job.capability.value,
                        "related_entities": [job.target],
                        "metadata": {"job_id": job.id, "capability": job.capability.value}
                    }
                    results.append(event)
            
            # Generate events from critical findings
            finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
            critical_findings = await finding_storage.get_critical_findings(limit=100)
            
            for finding in critical_findings:
                severity_map = {
                    "critical": EventSeverity.CRITICAL.value,
                    "high": EventSeverity.HIGH.value,
                    "medium": EventSeverity.MEDIUM.value,
                    "low": EventSeverity.LOW.value,
                    "info": EventSeverity.INFO.value
                }
                event_severity = severity_map.get(finding.severity, EventSeverity.INFO.value)
                
                event_type_val = EventType.THREAT_DETECTED.value
                if "dark" in finding.capability.value.lower() or "web" in finding.capability.value.lower():
                    event_type_val = EventType.DARK_WEB_MENTION.value
                elif "credential" in finding.capability.value.lower() or "breach" in finding.capability.value.lower():
                    event_type_val = EventType.CREDENTIAL_LEAKED.value
                
                event = {
                    "id": generate_event_id(),
                    "type": event_type_val,
                    "title": finding.title,
                    "description": finding.description or finding.title,
                    "severity": event_severity,
                    "timestamp": finding.discovered_at,
                    "source": finding.capability.value,
                    "related_entities": [finding.target] if finding.target else [],
                    "metadata": {"finding_id": finding.id, "risk_score": finding.risk_score}
                }
                results.append(event)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error generating timeline events from database: {e}")
    
    # Map frontend parameters to backend parameters
    if type and not event_type:
        try:
            event_type = EventType(type)
        except ValueError:
            pass  # Invalid type, ignore
    
    if from_date and not start_time:
        try:
            start_time = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    
    if to and not end_time:
        try:
            end_time = datetime.fromisoformat(to.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    
    # Apply filters
    if event_type:
        results = [e for e in results if e.get("type") == event_type.value]
    if severity:
        results = [e for e in results if e.get("severity") == severity.value]
    if source:
        results = [e for e in results if e["source"] == source]
    if start_time:
        results = [e for e in results if e["timestamp"] >= start_time]
    if end_time:
        results = [e for e in results if e["timestamp"] <= end_time]
    
    # Sort by timestamp
    results.sort(key=lambda e: e["timestamp"], reverse=(order == "desc"))
    
    # Pagination
    results = results[offset:offset + limit]
    
    return [TimelineEvent(**e) for e in results]


@router.get("/stats", response_model=TimelineStats)
async def get_timeline_stats():
    """Get timeline statistics."""
    now = datetime.utcnow()
    
    by_type = {}
    by_severity = {}
    events_24h = 0
    events_7d = 0
    
    for event in events_db:
        # Count by type
        t = event["type"]
        by_type[t] = by_type.get(t, 0) + 1
        
        # Count by severity
        s = event["severity"]
        by_severity[s] = by_severity.get(s, 0) + 1
        
        # Count by time range
        age = now - event["timestamp"]
        if age <= timedelta(hours=24):
            events_24h += 1
        if age <= timedelta(days=7):
            events_7d += 1
    
    return TimelineStats(
        total_events=len(events_db),
        events_24h=events_24h,
        events_7d=events_7d,
        by_type=by_type,
        by_severity=by_severity
    )


@router.get("/recent", response_model=List[TimelineEvent])
async def get_recent_events(
    n: int = Query(default=20, ge=1, le=100),
    severity_filter: Optional[List[EventSeverity]] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get most recent N events. Generates events from database if in-memory store is empty."""
    results = events_db.copy()
    
    # If in-memory store is empty, generate events from database
    if not results:
        try:
            # Generate events from recent jobs
            job_storage = DBJobStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
            recent_jobs = await job_storage.list_jobs(limit=50, offset=0)
            
            for job in recent_jobs:
                # Create scan_completed event for completed jobs
                if job.status.value == "completed" and job.completed_at:
                    event = {
                        "id": generate_event_id(),
                        "type": EventType.SCAN_COMPLETED.value,  # Use .value to get string
                        "title": f"Scan completed: {job.capability.value} on {job.target}",
                        "description": f"Completed {job.capability.value} scan for {job.target}",
                        "severity": EventSeverity.INFO.value,  # Use .value to get string
                        "timestamp": job.completed_at,
                        "source": job.capability.value,
                        "related_entities": [job.target],
                        "metadata": {"job_id": job.id, "capability": job.capability.value}
                    }
                    results.append(event)
                # Create scan_started event for running jobs
                elif job.status.value == "running" and job.started_at:
                    event = {
                        "id": generate_event_id(),
                        "type": EventType.SCAN_COMPLETED.value,  # Use .value to get string
                        "title": f"Scan started: {job.capability.value} on {job.target}",
                        "description": f"Started {job.capability.value} scan for {job.target}",
                        "severity": EventSeverity.INFO.value,  # Use .value to get string
                        "timestamp": job.started_at,
                        "source": job.capability.value,
                        "related_entities": [job.target],
                        "metadata": {"job_id": job.id, "capability": job.capability.value}
                    }
                    results.append(event)
                # Also create event for pending/queued jobs
                elif job.status.value in ["pending", "queued"] and job.created_at:
                    event = {
                        "id": generate_event_id(),
                        "type": EventType.SCAN_COMPLETED.value,
                        "title": f"Scan queued: {job.capability.value} on {job.target}",
                        "description": f"Queued {job.capability.value} scan for {job.target}",
                        "severity": EventSeverity.INFO.value,
                        "timestamp": job.created_at,
                        "source": job.capability.value,
                        "related_entities": [job.target],
                        "metadata": {"job_id": job.id, "capability": job.capability.value}
                    }
                    results.append(event)
            
            # Generate events from critical findings
            finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
            critical_findings = await finding_storage.get_critical_findings(limit=50)
            
            for finding in critical_findings:
                # Map finding severity to event severity
                severity_map = {
                    "critical": EventSeverity.CRITICAL,
                    "high": EventSeverity.HIGH,
                    "medium": EventSeverity.MEDIUM,
                    "low": EventSeverity.LOW,
                    "info": EventSeverity.INFO
                }
                event_severity = severity_map.get(finding.severity, EventSeverity.INFO)
                
                # Determine event type based on capability
                event_type = EventType.THREAT_DETECTED
                if "dark" in finding.capability.value.lower() or "web" in finding.capability.value.lower():
                    event_type = EventType.DARK_WEB_MENTION
                elif "credential" in finding.capability.value.lower() or "breach" in finding.capability.value.lower():
                    event_type = EventType.CREDENTIAL_LEAKED
                
                event = {
                    "id": generate_event_id(),
                    "type": event_type.value,  # Use .value to get string
                    "title": finding.title,
                    "description": finding.description or finding.title,
                    "severity": event_severity.value,  # Use .value to get string
                    "timestamp": finding.discovered_at,
                    "source": finding.capability.value,
                    "related_entities": [finding.target] if finding.target else [],
                    "metadata": {"finding_id": finding.id, "risk_score": finding.risk_score}
                }
                results.append(event)
        except Exception as e:
            # Log error but don't fail - return empty or existing events
            import logging
            import logging
            logging.getLogger(__name__).warning(f"Error generating timeline events from database: {e}")
    
    if severity_filter:
        results = [e for e in results if e.get("severity") in severity_filter]
    
    # Sort by timestamp descending
    results.sort(key=lambda e: e.get("timestamp", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    
    # Convert to TimelineEvent objects, handling any validation errors
    events = []
    for e in results[:n]:
        try:
            # Ensure all required fields are present
            if "id" not in e:
                e["id"] = generate_event_id()
            if "related_entities" not in e:
                e["related_entities"] = []
            if "metadata" not in e:
                e["metadata"] = {}
            events.append(TimelineEvent(**e))
        except Exception as ex:
            import logging
            logging.getLogger(__name__).warning(f"Error creating TimelineEvent from {e}: {ex}")
            continue
    
    return events


@router.get("/range")
async def get_events_in_range(
    start: datetime,
    end: datetime,
    granularity: str = Query(default="hour", regex="^(minute|hour|day)$")
):
    """Get events aggregated by time range."""
    results = [e for e in events_db if start <= e["timestamp"] <= end]
    
    # Aggregate by granularity
    aggregated = {}
    for event in results:
        ts = event["timestamp"]
        if granularity == "minute":
            key = ts.strftime("%Y-%m-%d %H:%M")
        elif granularity == "hour":
            key = ts.strftime("%Y-%m-%d %H:00")
        else:  # day
            key = ts.strftime("%Y-%m-%d")
        
        if key not in aggregated:
            aggregated[key] = {"count": 0, "by_severity": {}}
        
        aggregated[key]["count"] += 1
        sev = event["severity"]
        aggregated[key]["by_severity"][sev] = aggregated[key]["by_severity"].get(sev, 0) + 1
    
    return {
        "start": start,
        "end": end,
        "granularity": granularity,
        "data": aggregated
    }


@router.get("/{event_id}", response_model=TimelineEvent)
async def get_event(event_id: str):
    """Get a specific event by ID."""
    for event in events_db:
        if event["id"] == event_id:
            return TimelineEvent(**event)
    raise HTTPException(status_code=404, detail="Event not found")


@router.post("/", response_model=TimelineEvent)
async def create_event(event: EventCreate):
    """Create a new timeline event."""
    event_id = generate_event_id()
    
    event_dict = {
        "id": event_id,
        "type": event.type,
        "title": event.title,
        "description": event.description,
        "severity": event.severity,
        "timestamp": datetime.utcnow(),
        "source": event.source,
        "related_entities": event.related_entities,
        "metadata": event.metadata
    }
    
    # Insert at the beginning (most recent)
    events_db.insert(0, event_dict)
    
    return TimelineEvent(**event_dict)


@router.delete("/{event_id}")
async def delete_event(event_id: str):
    """Delete an event."""
    for i, event in enumerate(events_db):
        if event["id"] == event_id:
            events_db.pop(i)
            return {"message": "Event deleted successfully"}
    raise HTTPException(status_code=404, detail="Event not found")


