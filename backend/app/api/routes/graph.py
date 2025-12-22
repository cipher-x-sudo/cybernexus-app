from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from enum import Enum
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.core.database.db_storage import DBStorage
from app.core.database.models import GraphNode as GraphNodeModel
from app.api.routes.auth import get_current_active_user, User, is_admin
from app.services.orchestrator import get_orchestrator
from sqlalchemy import select

router = APIRouter()


class RelationType(str, Enum):
    """Types of relationships between graph nodes."""
    RESOLVES_TO = "resolves_to"
    CONTAINS = "contains"
    COMMUNICATES_WITH = "communicates_with"
    HOSTS = "hosts"
    REGISTERED_BY = "registered_by"
    ASSOCIATED_WITH = "associated_with"
    LEAKED_IN = "leaked_in"
    TARGETS = "targets"
    USES = "uses"
    EXPLOITS = "exploits"


class GraphNode(BaseModel):
    """Graph node model with optional 3D coordinates for visualization."""
    id: str
    label: str
    type: str
    severity: str = "info"
    metadata: dict = {}
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class GraphEdge(BaseModel):
    """Graph edge model representing relationship between nodes."""
    id: str
    source: str
    target: str
    relation: RelationType
    weight: float = 1.0
    metadata: dict = {}


class GraphData(BaseModel):
    """Complete graph structure with nodes and edges."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class PathResult(BaseModel):
    """Result of path finding algorithm between two nodes."""
    path: List[str]
    total_weight: float
    edges: List[GraphEdge]


class ClusterResult(BaseModel):
    """Result of graph clustering algorithm (connected components)."""
    cluster_id: int
    nodes: List[str]
    center: Optional[str] = None


sample_nodes = []
sample_edges = []


@router.get("", response_model=GraphData)
async def get_full_graph(
    limit: int = Query(default=1000, le=10000),
    entity_types: Optional[List[str]] = Query(default=None),
    min_severity: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get full graph data with optional filtering by entity types and minimum severity."""
    try:
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        graph_data = await storage.get_graph_data()
        
        nodes = []
        edges = []
        
        # Process nodes with entity data enrichment
        if "nodes" in graph_data:
            for node_id, node_data in graph_data["nodes"].items():
                # Try to get entity data for richer node information
                entity_id = node_data.get("data", {}).get("id") if isinstance(node_data.get("data"), dict) else None
                entity = None
                if entity_id:
                    entity = await storage.get_entity(entity_id)
                if entity:
                    # Use entity data if available
                    severity = entity.get("severity", "info")
                    node_type = entity.get("type", node_data.get("node_type", "unknown"))
                    label = entity.get("value", node_data.get("label", node_id))
                else:
                    # Fall back to node data
                    severity = node_data.get("severity", "info")
                    node_type = node_data.get("node_type", "unknown")
                    label = node_data.get("label", node_id)
    
                # Apply filters
                if entity_types and node_type not in entity_types:
                    continue
                if min_severity:
                    severity_levels = ["info", "low", "medium", "high", "critical"]
                    if severity_levels.index(severity) < severity_levels.index(min_severity):
                        continue
                
                nodes.append(GraphNode(
                    id=node_id,
                    label=label,
                    type=node_type,
                    severity=severity,
                    metadata=node_data.get("data", {})
                ))
        
        # Process edges (only include edges between filtered nodes)
        if "edges" in graph_data:
            for edge_key, edge_data in graph_data["edges"].items():
                source = edge_data.get("source")
                target = edge_data.get("target")
                relation = edge_data.get("relation", "associated_with")
                weight = edge_data.get("weight", 1.0)
                
                # Only include edges between nodes that passed filters
                node_ids = {n.id for n in nodes}
                if source in node_ids and target in node_ids:
                    edges.append(GraphEdge(
                        id=edge_key,
                        source=source,
                        target=target,
                        relation=RelationType(relation) if hasattr(RelationType, relation.upper().replace("-", "_")) else RelationType.ASSOCIATED_WITH,
                        weight=weight,
                        metadata=edge_data.get("metadata", {})
                    ))
        
        # Apply limit and filter edges to match nodes
        nodes = nodes[:limit]
        node_ids = {n.id for n in nodes}
        edges = [e for e in edges if e.source in node_ids and e.target in node_ids]
    
        return GraphData(nodes=nodes, edges=edges)
        
    except Exception as e:
        logger.error(f"Error getting graph data: {e}", exc_info=True)
        return GraphData(nodes=[], edges=[])


@router.get("/node/{node_id}", response_model=GraphNode)
async def get_node(
    node_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific graph node by ID."""
    try:
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        entity = await storage.get_entity(node_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Node not found")
        
        graph_data = await storage.get_graph_data()
        node_data = graph_data.get("nodes", {}).get(node_id, {})
        
        return GraphNode(
            id=node_id,
            label=entity.get("value", node_data.get("label", node_id)),
            type=entity.get("type", node_data.get("node_type", "unknown")),
            severity=entity.get("severity", "info"),
            metadata=entity
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node {node_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving node: {str(e)}")


@router.get("/node/{node_id}/neighbors", response_model=GraphData)
async def get_neighbors(
    node_id: str,
    depth: int = Query(default=1, ge=1, le=5),
    direction: str = Query(default="both", regex="^(in|out|both)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get neighboring nodes up to specified depth (BFS traversal)."""
    try:
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        entity = await storage.get_entity(node_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Node not found")
    
        # Get neighbor IDs using BFS traversal
        neighbor_ids = await storage.get_neighbors(node_id, depth=depth)
        
        nodes = []
        edges = []
        visited = {node_id}
        
        # Add the starting node
        graph_data = await storage.get_graph_data()
        node_data = graph_data.get("nodes", {}).get(node_id, {})
        nodes.append(GraphNode(
            id=node_id,
            label=entity.get("value", node_data.get("label", node_id)),
            type=entity.get("type", node_data.get("node_type", "unknown")),
            severity=entity.get("severity", "info"),
            metadata=entity
        ))
        
        # Add neighbor nodes
        for neighbor_id in neighbor_ids:
            if neighbor_id in visited:
                continue
            visited.add(neighbor_id)
            
            neighbor_entity = await storage.get_entity(neighbor_id)
            if neighbor_entity:
                neighbor_node_data = graph_data.get("nodes", {}).get(neighbor_id, {})
                nodes.append(GraphNode(
                    id=neighbor_id,
                    label=neighbor_entity.get("value", neighbor_node_data.get("label", neighbor_id)),
                    type=neighbor_entity.get("type", neighbor_node_data.get("node_type", "unknown")),
                    severity=neighbor_entity.get("severity", "info"),
                    metadata=neighbor_entity
                ))
        
        # Include edges between visited nodes
        if "edges" in graph_data:
            for edge_key, edge_data in graph_data["edges"].items():
                source = edge_data.get("source")
                target = edge_data.get("target")
                if source in visited and target in visited:
                    relation = edge_data.get("relation", "associated_with")
                    edges.append(GraphEdge(
                        id=edge_key,
                        source=source,
                        target=target,
                        relation=RelationType(relation) if hasattr(RelationType, relation.upper().replace("-", "_")) else RelationType.ASSOCIATED_WITH,
                        weight=edge_data.get("weight", 1.0),
                        metadata=edge_data.get("metadata", {})
                    ))
    
        return GraphData(nodes=nodes, edges=edges)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting neighbors for {node_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving neighbors: {str(e)}")


@router.get("/job/{job_id}", response_model=GraphData)
async def get_graph_for_job(
    job_id: str,
    depth: int = Query(default=2, ge=1, le=5),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Build graph from job data by extracting entities from logs, findings, and metadata."""
    try:
        from urllib.parse import urlparse
        import re
        
        from app.core.database.job_storage import DBJobStorage
        job_storage = DBJobStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        job = await job_storage.get_job(job_id)
        
        if not job:
            logger.warning(f"Job {job_id} not found, returning empty graph")
            return GraphData(nodes=[], edges=[])
        
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        graph_data = await storage.get_graph_data()
        node_ids = []
        
        # Helper functions for entity type detection and extraction
        def detect_entity_type(value: str) -> str:
            """Detect entity type (email, ip_address, domain) from string value."""
            if not value:
                return "domain"
            
            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if '@' in value and re.match(email_pattern, value):
                return "email"
            
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if re.match(ip_pattern, value):
                return "ip_address"
            
            return "domain"
        
        def extract_domain_or_ip(value: str) -> str:
            """Extract domain or IP from URL or string value."""
            if not value:
                return ""
            
            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if '@' in value and re.match(email_pattern, value):
                return value
            
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if re.match(ip_pattern, value):
                return value
            try:
                parsed = urlparse(value)
                domain = parsed.netloc or parsed.path.split('/')[0]
                domain = domain.split(':')[0]
                return domain
            except:
                return value
        
        async def find_or_create_entity(value: str, entity_type: str = "domain") -> Optional[str]:
            """Find existing entity by value or create new one if not found."""
            if not value:
                return None
            
            search_types = [entity_type, "email", "domain", "ip_address"]
            for search_type in search_types:
                entities_by_type = await storage.get_by_type(search_type)
                for entity in entities_by_type:
                    if entity.get("value") == value:
                        entity_id = entity.get("id")
                        if entity.get("type") != entity_type:
                            logger.debug(f"Updating entity {entity_id} type from {entity.get('type')} to {entity_type}")
                            entity_data = {
                                "id": entity_id,
                                "type": entity_type,
                                "value": value,
                                "severity": entity.get("severity", "info"),
                                "metadata": entity.get("metadata", {})
                            }
                            await storage.save_entity(entity_data)
                        return entity_id
            
            for node_id, node_data in graph_data.get("nodes", {}).items():
                entity_id = node_data.get("data", {}).get("id") if isinstance(node_data.get("data"), dict) else None
                if entity_id:
                    entity = await storage.get_entity(entity_id)
                    if entity and entity.get("value") == value:
                        if entity.get("type") != entity_type:
                            logger.debug(f"Updating entity {entity_id} type from {entity.get('type')} to {entity_type}")
                            entity_data = {
                                "id": entity_id,
                                "type": entity_type,
                                "value": value,
                                "severity": entity.get("severity", "info"),
                                "metadata": entity.get("metadata", {})
                            }
                            await storage.save_entity(entity_data)
                        return entity_id
            
            try:
                from uuid import uuid4
                entity_id = f"{entity_type}-{uuid4().hex[:8]}"
                entity_data = {
                    "id": entity_id,
                    "type": entity_type,
                    "value": value,
                    "severity": "info",
                    "discovered_at": job.created_at.isoformat() if job.created_at else None,
                    "source": "job_graph"
                }
                await storage.save_entity(entity_data)
                logger.debug(f"Created entity {entity_id} for value {value}")
                return entity_id
            except Exception as e:
                logger.warning(f"Failed to create entity for {value}: {e}")
                return None
        
        crawled_urls = []
        if job.metadata:
            if 'crawled_urls' in job.metadata:
                crawled_urls = job.metadata.get('crawled_urls', [])
            elif 'discovered_urls' in job.metadata:
                crawled_urls = job.metadata.get('discovered_urls', [])
        
        if job.execution_logs:
            for log_entry in job.execution_logs:
                if isinstance(log_entry, dict):
                    message = log_entry.get('message', '') or log_entry.get('log', '') or str(log_entry)
                    email_pattern = r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+[a-zA-Z0-9]\b'
                    emails = re.findall(email_pattern, message)
                    for email in emails:
                        if email and '@' in email:
                            entity_id = await find_or_create_entity(email, "email")
                            if entity_id and entity_id not in node_ids:
                                node_ids.append(entity_id)
                    
                    domain_pattern = r'\b([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+)\b'
                    ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
                    
                    domains = re.findall(domain_pattern, message)
                    for domain in domains:
                        if domain and '@' not in domain and '.' in domain and not domain.startswith('http') and len(domain) > 3:
                            entity_type = detect_entity_type(domain)
                            entity_id = await find_or_create_entity(domain, entity_type)
                            if entity_id and entity_id not in node_ids:
                                node_ids.append(entity_id)
                    
                    ips = re.findall(ip_pattern, message)
                    for ip in ips:
                        entity_id = await find_or_create_entity(ip, "ip_address")
                        if entity_id and entity_id not in node_ids:
                                node_ids.append(entity_id)
                    
                    for key in ['domain', 'ip', 'email', 'target', 'url', 'host']:
                        if key in log_entry:
                            value = log_entry[key]
                            if isinstance(value, str):
                                domain_or_ip = extract_domain_or_ip(value)
                                if domain_or_ip:
                                    entity_type = detect_entity_type(domain_or_ip)
                                    entity_id = await find_or_create_entity(domain_or_ip, entity_type)
                                    if entity_id and entity_id not in node_ids:
                                        node_ids.append(entity_id)
        
        from app.core.database.finding_storage import DBFindingStorage
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        job_findings = await finding_storage.get_findings_for_job(job_id)
        
        keyword_node_id = None
        if job.target:
            keyword_value = job.target.strip()
            keyword_node_id = await find_or_create_entity(keyword_value, "keyword")
            if keyword_node_id and keyword_node_id not in node_ids:
                node_ids.append(keyword_node_id)
        
        website_to_entities = {}
        keyword_to_websites = []
        processed_websites = set()
        
        for url in crawled_urls:
            if not url or url in processed_websites:
                continue
            
            if ".onion" in url:
                website_value = url
            else:
                website_value = extract_domain_or_ip(url)
            
            if website_value:
                website_node_id = await find_or_create_entity(website_value, "website")
                if website_node_id and website_node_id not in node_ids:
                    node_ids.append(website_node_id)
                if website_node_id not in keyword_to_websites:
                    keyword_to_websites.append(website_node_id)
                if website_node_id not in website_to_entities:
                    website_to_entities[website_node_id] = []
                processed_websites.add(url)
        
        for finding in job_findings:
            website_url = None
            entity_type_from_evidence = None
            
            if finding.evidence:
                site_data = finding.evidence.get("site")
                if isinstance(site_data, str):
                    website_url = site_data
                elif isinstance(site_data, dict):
                    website_url = site_data.get("onion_url") or site_data.get("url")
                
                if not website_url:
                    website_url = finding.evidence.get("url") or finding.evidence.get("source_url")
                
                entity_data = finding.evidence.get("entity")
                if entity_data:
                    entity_type_from_evidence = entity_data.get("type") or entity_data.get("entity_type")
            
            if not website_url and finding.target:
                website_url = finding.target
            
            website_node_id = None
            if website_url:
                if ".onion" in website_url:
                    website_value = website_url
                else:
                    website_value = extract_domain_or_ip(website_url)
                
                if website_value:
                    website_node_id = await find_or_create_entity(website_value, "website")
                    if website_node_id and website_node_id not in node_ids:
                        node_ids.append(website_node_id)
                    if website_node_id not in keyword_to_websites:
                        keyword_to_websites.append(website_node_id)
                    if website_node_id not in website_to_entities:
                        website_to_entities[website_node_id] = []
                    processed_websites.add(website_url)
            
            for asset in finding.affected_assets:
                if not asset:
                    continue
                
                entity_id = None
                entity_type = None
                
                entity = await storage.get_entity(asset)
                if entity:
                    entity_type = entity.get("type", "unknown")
                    entity_id = asset
                else:
                    domain_or_ip = extract_domain_or_ip(asset)
                    if not domain_or_ip:
                        continue
                    
                    if entity_type_from_evidence:
                        entity_type = entity_type_from_evidence
                    else:
                        entity_type = detect_entity_type(domain_or_ip)
                    
                    entity_id = await find_or_create_entity(domain_or_ip, entity_type)
                
                if entity_id and entity_id not in node_ids:
                    node_ids.append(entity_id)
                
                if website_node_id and entity_id:
                    if website_node_id not in website_to_entities:
                        website_to_entities[website_node_id] = []
                    if entity_id not in website_to_entities[website_node_id]:
                        website_to_entities[website_node_id].append(entity_id)
        
        if not node_ids:
            logger.warning(f"Job {job_id} has no associated nodes after processing")
            return GraphData(nodes=[], edges=[])
        
        graph_data = await storage.get_graph_data()
        
        job_node_id = f"job-{job_id}"
        all_node_ids = set(node_ids)
        all_node_ids.add(job_node_id)
        
        job_entity = await storage.get_entity(job_node_id)
        if not job_entity:
            job_entity = {
                "id": job_node_id,
                "type": "job",
                "value": f"{job.capability.value} - {job.target}",
                "severity": "info",
                "title": f"{job.capability.value} Job",
                "description": f"Job targeting {job.target}",
                "capability": job.capability.value,
                "status": job.status.value,
                "target": job.target,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "source": "orchestrator"
            }
            await storage.save_entity(job_entity)
            logger.debug(f"Created job entity {job_node_id}")
        
        if keyword_node_id:
            for website_node_id in keyword_to_websites:
                try:
                    await storage.add_relationship(
                        keyword_node_id,
                        website_node_id,
                        relation="discovered",
                        weight=1.0
                    )
                    logger.debug(f"Created edge from keyword {keyword_node_id} to website {website_node_id}")
                except Exception as e:
                    logger.debug(f"Failed to create edge from keyword to website {website_node_id}: {e}")
        
        for website_node_id, entity_ids in website_to_entities.items():
            for entity_id in entity_ids:
                try:
                    await storage.add_relationship(
                        website_node_id,
                        entity_id,
                        relation="contains",
                        weight=1.0
                    )
                    logger.debug(f"Created edge from website {website_node_id} to entity {entity_id}")
                except Exception as e:
                    logger.debug(f"Failed to create edge from website to entity {entity_id}: {e}")
        
        if keyword_node_id:
            try:
                await storage.add_relationship(
                    job_node_id,
                    keyword_node_id,
                    relation="searches",
                    weight=1.0
                )
                logger.debug(f"Created edge from job {job_node_id} to keyword {keyword_node_id}")
            except Exception as e:
                logger.debug(f"Failed to create edge from job to keyword: {e}")
        
        graph_data = await storage.get_graph_data()
        
        visited = set()
        nodes = []
        edges = []
        
        job_node_data = graph_data.get("nodes", {}).get(job_node_id, {})
        nodes.append(GraphNode(
            id=job_node_id,
            label=f"{job.capability.value} - {job.target}",
            type="job",
            severity="info",
            metadata={**job_entity, "is_job": True, "job_status": job.status.value}
        ))
        visited.add(job_node_id)
        
        for node_id in node_ids:
            if node_id in visited:
                continue
            
            entity = await storage.get_entity(node_id)
            if entity:
                node_data = graph_data.get("nodes", {}).get(node_id, {})
                nodes.append(GraphNode(
                    id=node_id,
                    label=entity.get("value", node_data.get("label", node_id)),
                    type=entity.get("type", node_data.get("node_type", "unknown")),
                    severity=entity.get("severity", "info"),
                    metadata={**entity, "is_job_asset": True}
                ))
                visited.add(node_id)
            
            neighbor_ids = await storage.get_neighbors(node_id, depth=depth)
            for neighbor_id in neighbor_ids:
                if neighbor_id not in visited:
                    all_node_ids.add(neighbor_id)
                    visited.add(neighbor_id)
                    
                    neighbor_entity = await storage.get_entity(neighbor_id)
                    if neighbor_entity:
                        neighbor_node_data = graph_data.get("nodes", {}).get(neighbor_id, {})
                        nodes.append(GraphNode(
                            id=neighbor_id,
                            label=neighbor_entity.get("value", neighbor_node_data.get("label", neighbor_id)),
                            type=neighbor_entity.get("type", neighbor_node_data.get("node_type", "unknown")),
                            severity=neighbor_entity.get("severity", "info"),
                            metadata=neighbor_entity
                        ))
        
        node_id_to_entity_id = {}
        
        graph_node_ids_to_query = [f"node-{entity_id}" for entity_id in all_node_ids]
        
        if graph_node_ids_to_query:
            result = await db.execute(
                select(GraphNodeModel).where(GraphNodeModel.id.in_(graph_node_ids_to_query))
            )
            graph_nodes = result.scalars().all()
            for graph_node in graph_nodes:
                if graph_node.entity_id:
                    node_id_to_entity_id[graph_node.id] = graph_node.entity_id
        
        if "edges" in graph_data:
            for edge_key, edge_data in graph_data["edges"].items():
                source_graph_node_id = edge_data.get("source")
                target_graph_node_id = edge_data.get("target")
                
                source_entity_id = node_id_to_entity_id.get(source_graph_node_id)
                target_entity_id = node_id_to_entity_id.get(target_graph_node_id)
                
                if not source_entity_id and source_graph_node_id and source_graph_node_id.startswith("node-"):
                    source_entity_id = source_graph_node_id[5:]
                if not target_entity_id and target_graph_node_id and target_graph_node_id.startswith("node-"):
                    target_entity_id = target_graph_node_id[5:]
                
                if not source_entity_id:
                    source_entity_id = source_graph_node_id
                if not target_entity_id:
                    target_entity_id = target_graph_node_id
                
                if source_entity_id in all_node_ids and target_entity_id in all_node_ids:
                    relation = edge_data.get("relation", "associated_with")
                    edges.append(GraphEdge(
                        id=edge_key,
                        source=source_entity_id,
                        target=target_entity_id,
                        relation=RelationType(relation) if hasattr(RelationType, relation.upper().replace("-", "_")) else RelationType.ASSOCIATED_WITH,
                        weight=edge_data.get("weight", 1.0),
                        metadata=edge_data.get("metadata", {})
                    ))
        
        return GraphData(nodes=nodes, edges=edges)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting graph for job {job_id}: {e}", exc_info=True)
        return GraphData(nodes=[], edges=[])


@router.get("/path", response_model=PathResult)
async def find_path(
    source: str,
    target: str,
    algorithm: str = Query(default="bfs", regex="^(bfs|dijkstra)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Find shortest path between two nodes using BFS or Dijkstra algorithm."""
    try:
        if source == target:
            return PathResult(path=[source], total_weight=0, edges=[])
    
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        path = await storage.find_path(source, target)
        
        if not path:
            raise HTTPException(status_code=404, detail="No path found between nodes")
        
        # Build edge list for path
        graph_data = await storage.get_graph_data()
        edges_list = []
        total_weight = 0
        
        for i in range(len(path) - 1):
            source_id = path[i]
            target_id = path[i + 1]
            
            # Find edge between consecutive nodes in path
            if "edges" in graph_data:
                for edge_key, edge_data in graph_data["edges"].items():
                    if (edge_data.get("source") == source_id and edge_data.get("target") == target_id) or \
                       (edge_data.get("source") == target_id and edge_data.get("target") == source_id):
                        relation = edge_data.get("relation", "associated_with")
                        weight = edge_data.get("weight", 1.0)
                        edges_list.append(GraphEdge(
                            id=edge_key,
                            source=source_id,
                            target=target_id,
                            relation=RelationType(relation) if hasattr(RelationType, relation.upper().replace("-", "_")) else RelationType.ASSOCIATED_WITH,
                            weight=weight,
                            metadata=edge_data.get("metadata", {})
                        ))
                        total_weight += weight
                        break
        
        return PathResult(path=path, total_weight=total_weight, edges=edges_list)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding path from {source} to {target}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error finding path: {str(e)}")


@router.get("/clusters", response_model=List[ClusterResult])
async def find_clusters(min_size: int = Query(default=2, ge=2)):
    """Find connected components (clusters) in the graph using BFS."""
    # Build adjacency list from edges
    adj = {}
    all_nodes = set()
    
    for edge in sample_edges:
        if edge.source not in adj:
            adj[edge.source] = []
        adj[edge.source].append(edge.target)
        if edge.target not in adj:
            adj[edge.target] = []
        adj[edge.target].append(edge.source)
        all_nodes.add(edge.source)
        all_nodes.add(edge.target)
    
    # Find connected components using BFS
    visited = set()
    clusters = []
    cluster_id = 0
    
    for node in all_nodes:
        if node not in visited:
            component = []
            queue = [node]
            while queue:
                curr = queue.pop(0)
                if curr not in visited:
                    visited.add(curr)
                    component.append(curr)
                    queue.extend(n for n in adj.get(curr, []) if n not in visited)
            
            # Only include components meeting minimum size
            if len(component) >= min_size:
                clusters.append(ClusterResult(
                    cluster_id=cluster_id,
                    nodes=component,
                    center=component[0]
                ))
                cluster_id += 1
    
    return clusters


@router.post("/edge", response_model=GraphEdge)
async def create_edge(
    edge: GraphEdge,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new relationship edge between two nodes."""
    storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
    await storage.add_relationship(
        source_id=edge.source,
        target_id=edge.target,
        relation=edge.relation.value if isinstance(edge.relation, RelationType) else edge.relation,
        weight=edge.weight,
        metadata=edge.metadata
    )
    return edge


@router.delete("/edge/{edge_id}")
async def delete_edge(
    edge_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a graph edge by ID (non-admin users can only delete their own edges)."""
    from app.core.database.models import GraphEdge as GraphEdgeModel
    
    query = select(GraphEdgeModel).where(GraphEdgeModel.id == edge_id)
    if not is_admin(current_user):
        query = query.where(GraphEdgeModel.user_id == current_user.id)
    
    result = await db.execute(query)
    edge = result.scalar_one_or_none()
    
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    
    await db.delete(edge)
    await db.commit()
    
    return {"message": "Edge deleted successfully"}


