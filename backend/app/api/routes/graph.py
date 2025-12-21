"""
Graph Routes

Handles graph queries, traversals, and relationship management.
Uses database-backed storage with user scoping.
"""

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
    """Types of relationships between entities."""
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
    """Graph node representation."""
    id: str
    label: str
    type: str
    severity: str = "info"
    metadata: dict = {}
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class GraphEdge(BaseModel):
    """Graph edge representation."""
    id: str
    source: str
    target: str
    relation: RelationType
    weight: float = 1.0
    metadata: dict = {}


class GraphData(BaseModel):
    """Complete graph data for visualization."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class PathResult(BaseModel):
    """Path between two nodes."""
    path: List[str]
    total_weight: float
    edges: List[GraphEdge]


class ClusterResult(BaseModel):
    """Node cluster."""
    cluster_id: int
    nodes: List[str]
    center: Optional[str] = None


# Graph data will be populated from real DarkWatch site relationships
# No sample data - graph is built dynamically from collected intelligence
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
    """Get the full graph data for visualization from database storage."""
    try:
        # Get graph data from database storage
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        graph_data = await storage.get_graph_data()
        
        nodes = []
        edges = []
        
        # Convert graph nodes to GraphNode format
        if "nodes" in graph_data:
            for node_id, node_data in graph_data["nodes"].items():
                # Get entity data if available (try to get from entity_id in node data)
                entity_id = node_data.get("data", {}).get("id") if isinstance(node_data.get("data"), dict) else None
                entity = None
                if entity_id:
                    entity = await storage.get_entity(entity_id)
                if entity:
                    severity = entity.get("severity", "info")
                    node_type = entity.get("type", node_data.get("node_type", "unknown"))
                    label = entity.get("value", node_data.get("label", node_id))
                else:
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
        
        # Convert graph edges to GraphEdge format
        if "edges" in graph_data:
            for edge_key, edge_data in graph_data["edges"].items():
                source = edge_data.get("source")
                target = edge_data.get("target")
                relation = edge_data.get("relation", "associated_with")
                weight = edge_data.get("weight", 1.0)
                
                # Only include edges where both nodes are in our filtered nodes
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
        
        # Limit results
        nodes = nodes[:limit]
        # Filter edges to only include those connecting our limited nodes
        node_ids = {n.id for n in nodes}
        edges = [e for e in edges if e.source in node_ids and e.target in node_ids]
    
        return GraphData(nodes=nodes, edges=edges)
        
    except Exception as e:
        logger.error(f"Error getting graph data: {e}", exc_info=True)
        # Fallback to empty graph
        return GraphData(nodes=[], edges=[])


@router.get("/node/{node_id}", response_model=GraphNode)
async def get_node(
    node_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific node by ID from database storage."""
    try:
        # Get entity from storage
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        entity = await storage.get_entity(node_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Get graph data to check node metadata
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
    """Get neighbors of a node up to specified depth from database storage."""
    try:
        # Check if node exists
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        entity = await storage.get_entity(node_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Node not found")
    
        # Use Storage's get_neighbors method
        neighbor_ids = await storage.get_neighbors(node_id, depth=depth)
        
        # Get all neighbor entities
        nodes = []
        edges = []
        visited = {node_id}
        
        # Get starting node
        graph_data = await storage.get_graph_data()
        node_data = graph_data.get("nodes", {}).get(node_id, {})
        nodes.append(GraphNode(
            id=node_id,
            label=entity.get("value", node_data.get("label", node_id)),
            type=entity.get("type", node_data.get("node_type", "unknown")),
            severity=entity.get("severity", "info"),
            metadata=entity
        ))
        
        # Get neighbor nodes
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
        
        # Get edges between these nodes
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
    """Get focused graph data for a specific job, showing relationships of discovered entities."""
    try:
        from urllib.parse import urlparse
        import re
        
        # Get job from database
        from app.core.database.job_storage import DBJobStorage
        job_storage = DBJobStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        job = await job_storage.get_job(job_id)
        
        if not job:
            # Fallback to empty graph if job not found
            logger.warning(f"Job {job_id} not found, returning empty graph")
            return GraphData(nodes=[], edges=[])
        
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        graph_data = await storage.get_graph_data()
        node_ids = []
        
        def detect_entity_type(value: str) -> str:
            """Detect entity type: email, ip_address, or domain."""
            if not value:
                return "domain"
            
            # Check if it's an email address (contains @ and matches pattern)
            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if '@' in value and re.match(email_pattern, value):
                return "email"
            
            # Check if it's an IP address
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if re.match(ip_pattern, value):
                return "ip_address"
            
            # Default to domain
            return "domain"
        
        def extract_domain_or_ip(value: str) -> str:
            """Extract domain or IP from URL or return as-is. Preserves email addresses."""
            if not value:
                return ""
            
            # If it's an email, return as-is
            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if '@' in value and re.match(email_pattern, value):
                return value
            
            # Check if it's already an IP
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if re.match(ip_pattern, value):
                return value
            # Try to parse as URL
            try:
                parsed = urlparse(value)
                domain = parsed.netloc or parsed.path.split('/')[0]
                # Remove port if present
                domain = domain.split(':')[0]
                return domain
            except:
                # If parsing fails, assume it's already a domain/IP
                return value
        
        async def find_or_create_entity(value: str, entity_type: str = "domain") -> Optional[str]:
            """Find entity by value or create it if not found. Returns entity ID."""
            if not value:
                return None
            
            # First, try to find existing entity by value
            entities_by_type = await storage.get_by_type(entity_type)
            for entity in entities_by_type:
                if entity.get("value") == value:
                    return entity.get("id")
            
            # Also check all entities in graph
            for node_id, node_data in graph_data.get("nodes", {}).items():
                entity_id = node_data.get("data", {}).get("id") if isinstance(node_data.get("data"), dict) else None
                if entity_id:
                    entity = await storage.get_entity(entity_id)
                    if entity and entity.get("value") == value:
                        return entity_id
            
            # If not found, create a new entity
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
        
        # Extract entities from job target
        if job.target:
            target_domain_or_ip = extract_domain_or_ip(job.target)
            if target_domain_or_ip:
                entity_type = detect_entity_type(target_domain_or_ip)
                entity_id = await find_or_create_entity(target_domain_or_ip, entity_type)
                if entity_id and entity_id not in node_ids:
                    node_ids.append(entity_id)
        
        # Extract entities from job meta_data
        if job.metadata:
            # Check for common keys that might contain entities
            entity_keys = ['discovered_entities', 'entities', 'assets', 'domains', 'ips', 'ip_addresses', 
                          'discovered_domains', 'discovered_ips', 'targets', 'related_entities']
            
            for key in entity_keys:
                if key in job.metadata:
                    value = job.metadata[key]
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                domain_or_ip = extract_domain_or_ip(item)
                                if domain_or_ip:
                                    entity_type = detect_entity_type(domain_or_ip)
                                    entity_id = await find_or_create_entity(domain_or_ip, entity_type)
                                    if entity_id and entity_id not in node_ids:
                                        node_ids.append(entity_id)
                            elif isinstance(item, dict):
                                # Handle dict with 'value' or 'domain' or 'ip' keys
                                entity_value = item.get('value') or item.get('domain') or item.get('ip') or item.get('target')
                                if entity_value:
                                    domain_or_ip = extract_domain_or_ip(str(entity_value))
                                    if domain_or_ip:
                                        entity_type = detect_entity_type(domain_or_ip)
                                        entity_id = await find_or_create_entity(domain_or_ip, entity_type)
                                        if entity_id and entity_id not in node_ids:
                                            node_ids.append(entity_id)
                    elif isinstance(value, str):
                        domain_or_ip = extract_domain_or_ip(value)
                        if domain_or_ip:
                            entity_type = detect_entity_type(domain_or_ip)
                            entity_id = await find_or_create_entity(domain_or_ip, entity_type)
                            if entity_id and entity_id not in node_ids:
                                node_ids.append(entity_id)
            
            # Also check for nested structures (e.g., capture data)
            if 'capture' in job.metadata and isinstance(job.metadata['capture'], dict):
                capture_data = job.metadata['capture']
                # Check for domain tree or discovered domains
                if 'domain_tree' in capture_data:
                    # Domain tree might be a graph structure, extract nodes
                    domain_tree = capture_data['domain_tree']
                    if isinstance(domain_tree, dict) and 'nodes' in domain_tree:
                        for node in domain_tree['nodes']:
                            if isinstance(node, dict):
                                node_value = node.get('id') or node.get('label') or node.get('value')
                                if node_value:
                                    domain_or_ip = extract_domain_or_ip(str(node_value))
                                    if domain_or_ip:
                                        entity_type = detect_entity_type(domain_or_ip)
                                        entity_id = await find_or_create_entity(domain_or_ip, entity_type)
                                        if entity_id and entity_id not in node_ids:
                                            node_ids.append(entity_id)
        
        # Extract entities from execution_logs
        if job.execution_logs:
            for log_entry in job.execution_logs:
                if isinstance(log_entry, dict):
                    # Look for entity mentions in log messages
                    message = log_entry.get('message', '') or log_entry.get('log', '') or str(log_entry)
                    # Try to extract emails, domains/IPs from log messages using regex
                    # Match email addresses first
                    email_pattern = r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+[a-zA-Z0-9]\b'
                    emails = re.findall(email_pattern, message)
                    for email in emails:
                        if email and '@' in email:
                            entity_id = await find_or_create_entity(email, "email")
                            if entity_id and entity_id not in node_ids:
                                node_ids.append(entity_id)
                    
                    # Match common patterns like "discovered domain.com" or "found 1.2.3.4"
                    domain_pattern = r'\b([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+)\b'
                    ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
                    
                    # Extract domains (excluding emails already extracted)
                    domains = re.findall(domain_pattern, message)
                    for domain in domains:
                        # Filter out emails and common false positives
                        if domain and '@' not in domain and '.' in domain and not domain.startswith('http') and len(domain) > 3:
                            entity_type = detect_entity_type(domain)
                            entity_id = await find_or_create_entity(domain, entity_type)
                            if entity_id and entity_id not in node_ids:
                                node_ids.append(entity_id)
                    
                    # Extract IPs
                    ips = re.findall(ip_pattern, message)
                    for ip in ips:
                        entity_id = await find_or_create_entity(ip, "ip_address")
                        if entity_id and entity_id not in node_ids:
                            node_ids.append(entity_id)
                    
                    # Also check for structured data in logs
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
        
        # Extract entities from job findings
        from app.core.database.finding_storage import DBFindingStorage
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        job_findings = await finding_storage.get_findings_for_job(job_id)
        
        for finding in job_findings:
            # Process affected_assets from findings
            for asset in finding.affected_assets:
                if not asset:
                    continue
                
                # Try as entity ID first
                entity = await storage.get_entity(asset)
                if entity:
                    if asset not in node_ids:
                        node_ids.append(asset)
                    continue
                
                # Extract domain/IP/email from URL
                domain_or_ip = extract_domain_or_ip(asset)
                if not domain_or_ip:
                    continue
                
                # Determine entity type
                entity_type = detect_entity_type(domain_or_ip)
                
                # Find or create entity
                entity_id = await find_or_create_entity(domain_or_ip, entity_type)
                if entity_id and entity_id not in node_ids:
                    node_ids.append(entity_id)
            
            # Process finding target
            if finding.target:
                target_domain_or_ip = extract_domain_or_ip(finding.target)
                if target_domain_or_ip:
                    entity_type = detect_entity_type(target_domain_or_ip)
                    entity_id = await find_or_create_entity(target_domain_or_ip, entity_type)
                    if entity_id and entity_id not in node_ids:
                        node_ids.append(entity_id)
        
        if not node_ids:
            # No nodes to show, return empty graph
            logger.warning(f"Job {job_id} has no associated nodes after processing")
            return GraphData(nodes=[], edges=[])
        
        # Refresh graph data after creating entities
        graph_data = await storage.get_graph_data()
        
        # Add job as a node and create relationships to discovered entities
        job_node_id = f"job-{job_id}"
        all_node_ids = set(node_ids)
        all_node_ids.add(job_node_id)
        
        # Create job entity if it doesn't exist
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
        
        # Create relationships from job to discovered entities
        for asset_node_id in node_ids:
            try:
                # Check if edge already exists
                edge_exists = False
                if "edges" in graph_data:
                    for edge_key, edge_data in graph_data["edges"].items():
                        if (edge_data.get("source") == job_node_id and edge_data.get("target") == asset_node_id) or \
                           (edge_data.get("source") == asset_node_id and edge_data.get("target") == job_node_id):
                            edge_exists = True
                            break
                
                if not edge_exists:
                    await storage.add_relationship(
                        job_node_id,
                        asset_node_id,
                        relation="targets",
                        weight=1.0
                    )
                    logger.debug(f"Created edge from job {job_node_id} to asset {asset_node_id}")
            except Exception as e:
                logger.debug(f"Failed to create edge from job to asset {asset_node_id}: {e}")
        
        # Refresh graph data after adding edges
        graph_data = await storage.get_graph_data()
        
        # Get neighbors for all discovered nodes
        visited = set()
        nodes = []
        edges = []
        
        # Add job node
        job_node_data = graph_data.get("nodes", {}).get(job_node_id, {})
        nodes.append(GraphNode(
            id=job_node_id,
            label=f"{job.capability.value} - {job.target}",
            type="job",
            severity="info",
            metadata={**job_entity, "is_job": True, "job_status": job.status.value}
        ))
        visited.add(job_node_id)
        
        # Get all nodes (discovered entities + their neighbors)
        for node_id in node_ids:
            if node_id in visited:
                continue
            
            # Get the node itself
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
            
            # Get neighbors
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
        
        # Build mapping from GraphNode IDs to Entity IDs
        # Edges in database use GraphNode IDs (e.g., "node-job-123") but we need entity IDs (e.g., "job-123")
        node_id_to_entity_id = {}
        
        # Build list of GraphNode IDs to query (format: "node-{entity_id}")
        graph_node_ids_to_query = [f"node-{entity_id}" for entity_id in all_node_ids]
        
        # Query all GraphNodes at once for better performance
        if graph_node_ids_to_query:
            result = await db.execute(
                select(GraphNodeModel).where(GraphNodeModel.id.in_(graph_node_ids_to_query))
            )
            graph_nodes = result.scalars().all()
            for graph_node in graph_nodes:
                if graph_node.entity_id:
                    node_id_to_entity_id[graph_node.id] = graph_node.entity_id
        
        # Get edges between all nodes
        if "edges" in graph_data:
            for edge_key, edge_data in graph_data["edges"].items():
                source_graph_node_id = edge_data.get("source")
                target_graph_node_id = edge_data.get("target")
                
                # Map GraphNode IDs to Entity IDs
                source_entity_id = node_id_to_entity_id.get(source_graph_node_id)
                target_entity_id = node_id_to_entity_id.get(target_graph_node_id)
                
                # If mapping failed, try removing "node-" prefix as fallback
                if not source_entity_id and source_graph_node_id and source_graph_node_id.startswith("node-"):
                    source_entity_id = source_graph_node_id[5:]  # Remove "node-" prefix
                if not target_entity_id and target_graph_node_id and target_graph_node_id.startswith("node-"):
                    target_entity_id = target_graph_node_id[5:]  # Remove "node-" prefix
                
                # If still no mapping, use original value (might already be entity ID)
                if not source_entity_id:
                    source_entity_id = source_graph_node_id
                if not target_entity_id:
                    target_entity_id = target_graph_node_id
                
                # Only include edge if both entity_ids are in all_node_ids
                if source_entity_id in all_node_ids and target_entity_id in all_node_ids:
                    relation = edge_data.get("relation", "associated_with")
                    edges.append(GraphEdge(
                        id=edge_key,
                        source=source_entity_id,  # Use entity ID
                        target=target_entity_id,  # Use entity ID
                        relation=RelationType(relation) if hasattr(RelationType, relation.upper().replace("-", "_")) else RelationType.ASSOCIATED_WITH,
                        weight=edge_data.get("weight", 1.0),
                        metadata=edge_data.get("metadata", {})
                    ))
        
        return GraphData(nodes=nodes, edges=edges)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting graph for job {job_id}: {e}", exc_info=True)
        # Fallback to empty graph
        return GraphData(nodes=[], edges=[])


@router.get("/path", response_model=PathResult)
async def find_path(
    source: str,
    target: str,
    algorithm: str = Query(default="bfs", regex="^(bfs|dijkstra)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Find path between two nodes using database storage."""
    try:
        if source == target:
            return PathResult(path=[source], total_weight=0, edges=[])
    
        # Use Storage's find_path method
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        path = await storage.find_path(source, target)
        
        if not path:
            raise HTTPException(status_code=404, detail="No path found between nodes")
        
        # Get edges for the path
        graph_data = await storage.get_graph_data()
        edges_list = []
        total_weight = 0
        
        for i in range(len(path) - 1):
            source_id = path[i]
            target_id = path[i + 1]
            
            # Find edge between these nodes
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
    """Find clusters of connected nodes."""
    # Simplified connected components (will use custom Graph DSA)
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
    
    visited = set()
    clusters = []
    cluster_id = 0
    
    for node in all_nodes:
        if node not in visited:
            # BFS to find connected component
            component = []
            queue = [node]
            while queue:
                curr = queue.pop(0)
                if curr not in visited:
                    visited.add(curr)
                    component.append(curr)
                    queue.extend(n for n in adj.get(curr, []) if n not in visited)
            
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
    """Create a new edge between nodes."""
    storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
    await storage.add_relationship(
        source_id=edge.source,
        target_id=edge.target,
        relation=edge.relation.value if isinstance(edge.relation, RelationType) else edge.relation,
        weight=edge.weight,
        metadata=edge.metadata  # Pydantic model uses 'metadata', storage maps to 'meta_data' in DB
    )
    return edge


@router.delete("/edge/{edge_id}")
async def delete_edge(
    edge_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an edge."""
    from app.core.database.models import GraphEdge as GraphEdgeModel
    
    # Find edge
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


