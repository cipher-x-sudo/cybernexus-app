from datetime import datetime
from typing import List, Optional
from enum import Enum
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class EntityType(str, Enum):
    DOMAIN = "domain"
    IP = "ip"
    EMAIL = "email"
    HASH = "hash"
    URL = "url"
    CREDENTIAL = "credential"
    ACTOR = "actor"
    MALWARE = "malware"
    CVE = "cve"


class EntitySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Entity(BaseModel):
    id: str
    type: EntityType
    value: str
    severity: EntitySeverity = EntitySeverity.INFO
    source: str
    first_seen: datetime
    last_seen: datetime
    tags: List[str] = []
    metadata: dict = {}


class EntityCreate(BaseModel):
    type: EntityType
    value: str
    severity: EntitySeverity = EntitySeverity.INFO
    source: str
    tags: List[str] = []
    metadata: dict = {}


class EntityUpdate(BaseModel):
    severity: Optional[EntitySeverity] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class EntityStats(BaseModel):
    total: int
    by_type: dict
    by_severity: dict
    recent_24h: int


entities_db: dict = {}
entity_counter = 0


def generate_entity_id() -> str:
    global entity_counter
    entity_counter += 1
    return f"ENT-{entity_counter:08d}"


@router.get("/", response_model=List[Entity])
async def list_entities(
    entity_type: Optional[EntityType] = None,
    severity: Optional[EntitySeverity] = None,
    source: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0)
):
    results = list(entities_db.values())
    
    if entity_type:
        results = [e for e in results if e["type"] == entity_type]
    if severity:
        results = [e for e in results if e["severity"] == severity]
    if source:
        results = [e for e in results if e["source"] == source]
    if tag:
        results = [e for e in results if tag in e.get("tags", [])]
    
    total = len(results)
    results = results[offset:offset + limit]
    
    return [Entity(**e) for e in results]


@router.get("/stats", response_model=EntityStats)
async def get_entity_stats():
    entities = list(entities_db.values())
    
    by_type = {}
    by_severity = {}
    
    for e in entities:
        t = e["type"]
        by_type[t] = by_type.get(t, 0) + 1
        
        s = e["severity"]
        by_severity[s] = by_severity.get(s, 0) + 1
    
    recent_24h = len(entities)
    
    return EntityStats(
        total=len(entities),
        by_type=by_type,
        by_severity=by_severity,
        recent_24h=recent_24h
    )


@router.get("/{entity_id}", response_model=Entity)
async def get_entity(entity_id: str):
    if entity_id not in entities_db:
        raise HTTPException(status_code=404, detail="Entity not found")
    return Entity(**entities_db[entity_id])


@router.post("/", response_model=Entity)
async def create_entity(entity: EntityCreate):
    now = datetime.utcnow()
    entity_id = generate_entity_id()
    
    entity_dict = {
        "id": entity_id,
        "type": entity.type,
        "value": entity.value,
        "severity": entity.severity,
        "source": entity.source,
        "first_seen": now,
        "last_seen": now,
        "tags": entity.tags,
        "metadata": entity.metadata
    }
    
    entities_db[entity_id] = entity_dict
    return Entity(**entity_dict)


@router.put("/{entity_id}", response_model=Entity)
async def update_entity(entity_id: str, entity: EntityUpdate):
    if entity_id not in entities_db:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    entity_dict = entities_db[entity_id]
    
    if entity.severity is not None:
        entity_dict["severity"] = entity.severity
    if entity.tags is not None:
        entity_dict["tags"] = entity.tags
    if entity.metadata is not None:
        entity_dict["metadata"].update(entity.metadata)
    
    entity_dict["last_seen"] = datetime.utcnow()
    
    return Entity(**entity_dict)


@router.delete("/{entity_id}")
async def delete_entity(entity_id: str):
    if entity_id not in entities_db:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    del entities_db[entity_id]
    return {"message": "Entity deleted successfully"}


@router.post("/bulk", response_model=List[Entity])
async def bulk_create_entities(entities: List[EntityCreate]):
    created = []
    now = datetime.utcnow()
    
    for entity in entities:
        entity_id = generate_entity_id()
        entity_dict = {
            "id": entity_id,
            "type": entity.type,
            "value": entity.value,
            "severity": entity.severity,
            "source": entity.source,
            "first_seen": now,
            "last_seen": now,
            "tags": entity.tags,
            "metadata": entity.metadata
        }
        entities_db[entity_id] = entity_dict
        created.append(Entity(**entity_dict))
    
    return created


