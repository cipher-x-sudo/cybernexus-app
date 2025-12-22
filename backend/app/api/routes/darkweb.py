from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger
from datetime import datetime

from app.services.orchestrator import get_orchestrator, Capability, Finding
from app.collectors.dark_watch import (
    OnionSite, BrandMention, ExtractedEntity,
    SiteCategory, ThreatLevel
)


router = APIRouter()


class SiteNodeResponse(BaseModel):
    """Response model for site network node."""
    id: str
    url: str
    title: str
    category: str
    threat_level: str
    risk_score: float


class SiteEdgeResponse(BaseModel):
    """Response model for site network edge (connection)."""
    source: str
    target: str


class SiteNetworkResponse(BaseModel):
    """Response model for site network graph (nodes and edges)."""
    nodes: List[SiteNodeResponse]
    edges: List[SiteEdgeResponse]


class OnionSiteResponse(BaseModel):
    """Response model for dark web onion site information."""
    site_id: str
    onion_url: str
    title: str
    category: str
    first_seen: str
    last_seen: str
    is_online: bool
    language: str
    page_count: int
    linked_sites_count: int
    entities_count: int
    keywords_matched: List[str]
    threat_level: str
    risk_score: float


class ExtractedEntityResponse(BaseModel):
    """Response model for extracted entity (email, bitcoin address, etc.)."""
    type: str
    value: str
    context: str
    source_url: str
    discovered_at: str
    confidence: float


class BrandMentionResponse(BaseModel):
    """Response model for brand mention on dark web."""
    mention_id: str
    keyword: str
    context: str
    source_site: str
    source_url: str
    discovered_at: str
    threat_level: str
    is_impersonation: bool
    is_data_leak: bool


class StatisticsResponse(BaseModel):
    """Response model for dark web intelligence statistics."""
    sites_indexed: int
    entities_extracted: int
    brand_mentions: int
    pages_crawled: int
    last_crawl: Optional[str]
    url_filter_size: int
    graph_sites: int
    graph_connections: int
    queue_size: int
    monitored_keywords: int


class ActivityResponse(BaseModel):
    """Response model for recent dark web activity."""
    period_hours: int
    sites_discovered: int
    brand_mentions: int
    high_risk_count: int
    categories: Dict[str, int]


class MentionResponse(BaseModel):
    """Response model for brand mention with source classification."""
    id: str
    title: str
    content: str
    source: str
    severity: str
    keywords: List[str]
    url: str
    timestamp: str
    author: Optional[str] = None


def _get_darkwatch_instance(job_id: str):
    """Get DarkWatch instance for a job, validating job exists and is dark web intelligence type."""
    orchestrator = get_orchestrator()
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.capability != Capability.DARK_WEB_INTELLIGENCE:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not a dark web intelligence job"
        )
    
    darkwatch = orchestrator.get_darkwatch_instance(job_id)
    if not darkwatch:
        raise HTTPException(
            status_code=404,
            detail=f"DarkWatch instance not available for job {job_id}. "
                   f"Job may still be running or instance was not stored."
        )
    
    return darkwatch, job


def _map_threat_to_severity(threat_level: str) -> str:
    """Map threat level to severity string (normalizes to lowercase)."""
    mapping = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "info"
    }
    return mapping.get(threat_level.lower(), "info")


@router.get("/jobs/{job_id}/sites/{site_id}/network", response_model=SiteNetworkResponse)
async def get_site_network(
    job_id: str,
    site_id: str,
    depth: int = Query(default=2, ge=1, le=5, description="Network traversal depth")
):
    """Get network graph of connected sites starting from a specific site (BFS traversal)."""
    darkwatch, job = _get_darkwatch_instance(job_id)
    
    try:
        network = darkwatch.get_site_network(site_id, depth=depth)
        
        # Convert network nodes to response format
        nodes = [
            SiteNodeResponse(
                id=node["id"],
                url=node["url"],
                title=node.get("title", "Unknown"),
                category=node.get("category", "unknown"),
                threat_level=node.get("threat_level", "info"),
                risk_score=node.get("risk_score", 0.0)
            )
            for node in network.get("nodes", [])
        ]
        
        # Convert network edges to response format
        edges = [
            SiteEdgeResponse(source=edge["source"], target=edge["target"])
            for edge in network.get("edges", [])
        ]
        
        return SiteNetworkResponse(nodes=nodes, edges=edges)
    
    except Exception as e:
        logger.error(f"Error getting site network for {site_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving site network: {str(e)}")


@router.get("/jobs/{job_id}/sites/{site_id}/clones", response_model=List[OnionSiteResponse])
async def get_site_clones(job_id: str, site_id: str):
    """Find cloned/duplicate sites based on content similarity."""
    darkwatch, job = _get_darkwatch_instance(job_id)
    
    try:
        clones = darkwatch.find_clones(site_id)
        
        return [
            OnionSiteResponse(
                site_id=clone.site_id,
                onion_url=clone.onion_url,
                title=clone.title,
                category=clone.category.value,
                first_seen=clone.first_seen.isoformat(),
                last_seen=clone.last_seen.isoformat(),
                is_online=clone.is_online,
                language=clone.language,
                page_count=clone.page_count,
                linked_sites_count=len(clone.linked_sites),
                entities_count=len(clone.extracted_entities),
                keywords_matched=clone.keywords_matched,
                threat_level=clone.threat_level.value,
                risk_score=clone.risk_score
            )
            for clone in clones
        ]
    
    except Exception as e:
        logger.error(f"Error finding clones for {site_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error finding clones: {str(e)}")


@router.get("/jobs/{job_id}/entities/search", response_model=List[ExtractedEntityResponse])
async def search_entities(
    job_id: str,
    entity_type: Optional[str] = Query(None, description="Filter by entity type (email, bitcoin, etc.)"),
    value_pattern: Optional[str] = Query(None, description="Regex pattern to match entity values")
):
    """Search extracted entities by type and/or value pattern."""
    darkwatch, job = _get_darkwatch_instance(job_id)
    
    try:
        entities = darkwatch.search_entities(
            entity_type=entity_type,
            value_pattern=value_pattern
        )
        
        return [
            ExtractedEntityResponse(
                type=entity.entity_type,
                value=entity.value,
                context=entity.context,
                source_url=entity.source_url,
                discovered_at=entity.discovered_at.isoformat(),
                confidence=entity.confidence
            )
            for entity in entities
        ]
    
    except Exception as e:
        logger.error(f"Error searching entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching entities: {str(e)}")


@router.get("/jobs/{job_id}/mentions", response_model=List[BrandMentionResponse])
async def get_brand_mentions(
    job_id: str,
    keyword: Optional[str] = Query(None, description="Filter by specific keyword"),
    min_threat_level: str = Query(default="info", description="Minimum threat level (critical, high, medium, low, info)")
):
    """Get brand mentions from dark web intelligence job, optionally filtered by keyword and threat level."""
    darkwatch, job = _get_darkwatch_instance(job_id)
    
    try:
        # Map string threat level to enum
        threat_level_map = {
            "critical": ThreatLevel.CRITICAL,
            "high": ThreatLevel.HIGH,
            "medium": ThreatLevel.MEDIUM,
            "low": ThreatLevel.LOW,
            "info": ThreatLevel.INFO
        }
        min_level = threat_level_map.get(min_threat_level.lower(), ThreatLevel.INFO)
        
        mentions = darkwatch.get_brand_mentions(
            keyword=keyword,
            min_threat_level=min_level
        )
        
        return [
            BrandMentionResponse(
                mention_id=mention.mention_id,
                keyword=mention.keyword,
                context=mention.context,
                source_site=mention.source_site,
                source_url=mention.source_url,
                discovered_at=mention.discovered_at.isoformat(),
                threat_level=mention.threat_level.value,
                is_impersonation=mention.is_impersonation,
                is_data_leak=mention.is_data_leak
            )
            for mention in mentions
        ]
    
    except Exception as e:
        logger.error(f"Error getting brand mentions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving brand mentions: {str(e)}")


@router.get("/jobs/{job_id}/statistics", response_model=StatisticsResponse)
async def get_statistics(job_id: str):
    """Get aggregated statistics about dark web intelligence collection."""
    darkwatch, job = _get_darkwatch_instance(job_id)
    
    try:
        stats = darkwatch.get_statistics()
        
        return StatisticsResponse(
            sites_indexed=stats.get("sites_indexed", 0),
            entities_extracted=stats.get("entities_extracted", 0),
            brand_mentions=stats.get("brand_mentions", 0),
            pages_crawled=stats.get("pages_crawled", 0),
            last_crawl=stats.get("last_crawl"),
            url_filter_size=stats.get("url_filter_size", 0),
            graph_sites=stats.get("graph_sites", 0),
            graph_connections=stats.get("graph_connections", 0),
            queue_size=stats.get("queue_size", 0),
            monitored_keywords=stats.get("monitored_keywords", 0)
        )
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


@router.get("/jobs/{job_id}/activity", response_model=ActivityResponse)
async def get_recent_activity(
    job_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back")
):
    """Get recent activity statistics for specified time period."""
    darkwatch, job = _get_darkwatch_instance(job_id)
    
    try:
        activity = darkwatch.get_recent_activity(hours=hours)
        
        return ActivityResponse(
            period_hours=activity.get("period_hours", hours),
            sites_discovered=activity.get("sites_discovered", 0),
            brand_mentions=activity.get("brand_mentions", 0),
            high_risk_count=activity.get("high_risk_count", 0),
            categories=activity.get("categories", {})
        )
    
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving activity: {str(e)}")


@router.get("/jobs/{job_id}/high-risk", response_model=List[OnionSiteResponse])
async def get_high_risk_sites(
    job_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of sites to return")
):
    """Get high-risk dark web sites sorted by risk score."""
    darkwatch, job = _get_darkwatch_instance(job_id)
    
    try:
        sites = darkwatch.get_high_risk_sites(limit=limit)
        
        return [
            OnionSiteResponse(
                site_id=site.site_id,
                onion_url=site.onion_url,
                title=site.title,
                category=site.category.value,
                first_seen=site.first_seen.isoformat(),
                last_seen=site.last_seen.isoformat(),
                is_online=site.is_online,
                language=site.language,
                page_count=site.page_count,
                linked_sites_count=len(site.linked_sites),
                entities_count=len(site.extracted_entities),
                keywords_matched=site.keywords_matched,
                threat_level=site.threat_level.value,
                risk_score=site.risk_score
            )
            for site in sites
        ]
    
    except Exception as e:
        logger.error(f"Error getting high-risk sites: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving high-risk sites: {str(e)}")


@router.get("/jobs/{job_id}/export")
async def export_intelligence(
    job_id: str,
    format: str = Query(default="json", description="Export format (json)")
):
    """Export dark web intelligence data in JSON format."""
    darkwatch, job = _get_darkwatch_instance(job_id)
    
    try:
        if format.lower() != "json":
            raise HTTPException(status_code=400, detail="Only JSON format is currently supported")
        
        export_data = darkwatch.export_intel(format="json")
        
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=export_data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=darkweb_intelligence_{job_id}.json"
            }
        )
    
    except Exception as e:
        logger.error(f"Error exporting intelligence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting intelligence: {str(e)}")


@router.get("/mentions", response_model=List[MentionResponse])
async def get_all_mentions(
    job_id: Optional[str] = Query(None, description="Optional: Get mentions from specific job"),
    keyword: Optional[str] = Query(None, description="Filter by keyword"),
    min_threat_level: str = Query(default="info", description="Minimum threat level")
):
    """Get brand mentions from all dark web jobs or a specific job, with source classification."""
    orchestrator = get_orchestrator()
    
    try:
        mentions_list = []
        
        if job_id:
            # Get mentions from specific job
            darkwatch, job = _get_darkwatch_instance(job_id)
            threat_level_map = {
                "critical": ThreatLevel.CRITICAL,
                "high": ThreatLevel.HIGH,
                "medium": ThreatLevel.MEDIUM,
                "low": ThreatLevel.LOW,
                "info": ThreatLevel.INFO
            }
            min_level = threat_level_map.get(min_threat_level.lower(), ThreatLevel.INFO)
            
            mentions = darkwatch.get_brand_mentions(keyword=keyword, min_threat_level=min_level)
            
            # Classify source type based on URL patterns
            for mention in mentions:
                source = "tor_site"
                if "forum" in mention.source_url.lower():
                    source = "forum"
                elif "market" in mention.source_url.lower() or "shop" in mention.source_url.lower():
                    source = "marketplace"
                elif "paste" in mention.source_url.lower():
                    source = "paste_site"
                
                mentions_list.append(MentionResponse(
                    id=mention.mention_id,
                    title=f"Brand mention: {mention.keyword}",
                    content=mention.context,
                    source=source,
                    severity=_map_threat_to_severity(mention.threat_level.value),
                    keywords=[mention.keyword],
                    url=mention.source_url,
                    timestamp=mention.discovered_at.isoformat()
                ))
        else:
            # Get mentions from all dark web jobs
            darkweb_jobs = orchestrator.get_jobs(capability=Capability.DARK_WEB_INTELLIGENCE, limit=100)
            
            for job in darkweb_jobs:
                darkwatch = orchestrator.get_darkwatch_instance(job.id)
                if darkwatch:
                    threat_level_map = {
                        "critical": ThreatLevel.CRITICAL,
                        "high": ThreatLevel.HIGH,
                        "medium": ThreatLevel.MEDIUM,
                        "low": ThreatLevel.LOW,
                        "info": ThreatLevel.INFO
                    }
                    min_level = threat_level_map.get(min_threat_level.lower(), ThreatLevel.INFO)
                    
                    mentions = darkwatch.get_brand_mentions(keyword=keyword, min_threat_level=min_level)
                    
                    # Classify source type
                    for mention in mentions:
                        source = "tor_site"
                        if "forum" in mention.source_url.lower():
                            source = "forum"
                        elif "market" in mention.source_url.lower():
                            source = "marketplace"
                        elif "paste" in mention.source_url.lower():
                            source = "paste_site"
                        
                        mentions_list.append(MentionResponse(
                            id=mention.mention_id,
                            title=f"Brand mention: {mention.keyword}",
                            content=mention.context,
                            source=source,
                            severity=_map_threat_to_severity(mention.threat_level.value),
                            keywords=[mention.keyword],
                            url=mention.source_url,
                            timestamp=mention.discovered_at.isoformat()
                        ))
        
        # Sort by timestamp (newest first)
        mentions_list.sort(key=lambda x: x.timestamp, reverse=True)
        
        return mentions_list
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all mentions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving mentions: {str(e)}")


