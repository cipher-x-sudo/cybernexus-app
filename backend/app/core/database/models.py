"""
Database Models

SQLAlchemy models for all database tables.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Boolean, Float, ForeignKey, 
    DateTime, Text, JSON, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(20), default="user", nullable=False)  # user, admin
    disabled = Column(Boolean, default=False, nullable=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    entities = relationship("Entity", back_populates="user", cascade="all, delete-orphan")
    graph_nodes = relationship("GraphNode", back_populates="user", cascade="all, delete-orphan")
    graph_edges = relationship("GraphEdge", back_populates="user", foreign_keys="GraphEdge.user_id", cascade="all, delete-orphan")
    activity_logs = relationship("UserActivityLog", back_populates="user", cascade="all, delete-orphan")
    network_logs = relationship("NetworkLog", back_populates="user", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="user", foreign_keys="Finding.user_id", cascade="all, delete-orphan")
    company_profile = relationship("CompanyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    scheduled_searches = relationship("ScheduledSearch", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
    )


class CompanyProfile(Base):
    """Company profile model - user-scoped."""
    __tablename__ = "company_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    primary_domain = Column(String(255), nullable=True)
    additional_domains = Column(JSONB, default=list, nullable=True)
    ip_ranges = Column(JSONB, default=list, nullable=True)
    key_assets = Column(JSONB, default=list, nullable=True)
    address = Column(JSONB, nullable=True)
    logo_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=True)
    locale = Column(String(10), default="en-US", nullable=True)
    automation_config = Column(JSONB, nullable=True)  # Automation configuration for scheduled scans
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="company_profile")
    
    __table_args__ = (
        Index('idx_company_profile_user', 'user_id'),
    )


class Entity(Base):
    """Entity model for threat intelligence entities."""
    __tablename__ = "entities"
    
    id = Column(String(255), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    value = Column(String(500), nullable=False, index=True)
    severity = Column(String(20), default="info", nullable=False)
    meta_data = Column(JSONB, default=dict, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="entities")
    graph_nodes = relationship("GraphNode", back_populates="entity", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_entity_user_type', 'user_id', 'type'),
        Index('idx_entity_user_value', 'user_id', 'value'),
    )


class GraphNode(Base):
    """Graph node model for relationship visualization."""
    __tablename__ = "graph_nodes"
    
    id = Column(String(255), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(String(255), ForeignKey("entities.id", ondelete="CASCADE"), nullable=True, index=True)
    label = Column(String(500), nullable=False)
    node_type = Column(String(50), nullable=False, index=True)
    data = Column(JSONB, default=dict, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="graph_nodes")
    entity = relationship("Entity", back_populates="graph_nodes")
    source_edges = relationship("GraphEdge", foreign_keys="GraphEdge.source_id", back_populates="source_node", cascade="all, delete-orphan")
    target_edges = relationship("GraphEdge", foreign_keys="GraphEdge.target_id", back_populates="target_node", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_graph_node_user', 'user_id'),
        Index('idx_graph_node_user_type', 'user_id', 'node_type'),
    )


class GraphEdge(Base):
    """Graph edge model for entity relationships."""
    __tablename__ = "graph_edges"
    
    id = Column(String(255), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(255), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(String(255), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    relation = Column(String(50), nullable=False, index=True)
    weight = Column(Float, default=1.0, nullable=False)
    meta_data = Column(JSONB, default=dict, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="graph_edges", foreign_keys=[user_id])
    source_node = relationship("GraphNode", foreign_keys=[source_id], back_populates="source_edges")
    target_node = relationship("GraphNode", foreign_keys=[target_id], back_populates="target_edges")
    
    __table_args__ = (
        Index('idx_graph_edge_user', 'user_id'),
        Index('idx_graph_edge_source_target', 'source_id', 'target_id'),
        Index('idx_graph_edge_relation', 'user_id', 'relation'),
    )


class UserActivityLog(Base):
    """User activity log model for audit trail."""
    __tablename__ = "user_activity_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, login, logout, etc.
    resource_type = Column(String(50), nullable=True, index=True)  # entity, graph_node, finding, etc.
    resource_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)
    meta_data = Column(JSONB, default=dict, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    __table_args__ = (
        Index('idx_activity_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_activity_action', 'action', 'timestamp'),
    )


class NetworkLog(Base):
    """Network log model for request/response tracking."""
    __tablename__ = "network_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # Nullable for unauthenticated requests
    request_id = Column(String(255), unique=True, nullable=False, index=True)
    ip = Column(String(45), nullable=True, index=True)
    method = Column(String(10), nullable=False, index=True)
    path = Column(String(1000), nullable=False, index=True)
    query = Column(Text, nullable=True)
    status = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Float, nullable=False)
    tunnel_detection = Column(JSONB, nullable=True)
    request_headers = Column(JSONB, nullable=True)
    response_headers = Column(JSONB, nullable=True)
    request_body = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="network_logs")
    
    __table_args__ = (
        Index('idx_network_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_network_ip_timestamp', 'ip', 'timestamp'),
        Index('idx_network_path_timestamp', 'path', 'timestamp'),
    )


class Finding(Base):
    """Finding model for security findings and threats."""
    __tablename__ = "findings"
    
    id = Column(String(255), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    capability = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active", index=True)  # active, resolved, false_positive, accepted_risk
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    evidence = Column(JSONB, default=dict, nullable=True)
    affected_assets = Column(JSONB, default=list, nullable=True)
    recommendations = Column(JSONB, default=list, nullable=True)
    risk_score = Column(Float, nullable=True)
    target = Column(String(500), nullable=True)
    discovered_at = Column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="findings", foreign_keys=[user_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    
    __table_args__ = (
        Index('idx_finding_user_severity', 'user_id', 'severity'),
        Index('idx_finding_user_capability', 'user_id', 'capability'),
        Index('idx_finding_user_status', 'user_id', 'status'),
        Index('idx_finding_discovered', 'discovered_at'),
    )


class PositiveIndicator(Base):
    """Positive security indicator model for tracking good practices and improvements."""
    __tablename__ = "positive_indicators"
    
    id = Column(String(255), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    indicator_type = Column(String(50), nullable=False, index=True)  # strong_config, no_vulnerabilities, improvement, remediated
    category = Column(String(50), nullable=False, index=True)  # exposure, dark_web, email_security, infrastructure, network
    points_awarded = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
    evidence = Column(JSONB, default=dict, nullable=True)
    target = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_positive_user_category', 'user_id', 'category'),
    )


class Notification(Base):
    """Notification model for user alerts and messages."""
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(50), nullable=False, index=True)  # threats, findings, scans, system, etc.
    priority = Column(String(20), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low, info
    read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    meta_data = Column(JSONB, default=dict, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'read'),
        Index('idx_notification_user_created', 'user_id', 'created_at'),
        Index('idx_notification_channel', 'channel', 'created_at'),
    )


class Job(Base):
    """Job model for capability execution jobs."""
    __tablename__ = "jobs"
    
    id = Column(String(255), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    capability = Column(String(50), nullable=False, index=True)
    target = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, index=True)  # pending, queued, running, completed, failed, cancelled
    priority = Column(Integer, nullable=False, default=2)  # 0=critical, 1=high, 2=normal, 3=low, 4=background
    progress = Column(Integer, nullable=False, default=0)  # 0-100
    config = Column(JSONB, default=dict, nullable=True)  # Job configuration/parameters
    meta_data = Column(JSONB, default=dict, nullable=True)  # Additional job metadata (renamed from 'metadata' - reserved in SQLAlchemy)
    error = Column(Text, nullable=True)  # Error message if failed
    execution_logs = Column(JSONB, default=list, nullable=True)  # Execution timeline/logs
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    
    __table_args__ = (
        Index('idx_job_user_status', 'user_id', 'status'),
        Index('idx_job_user_capability', 'user_id', 'capability'),
        Index('idx_job_user_created', 'user_id', 'created_at'),
        Index('idx_job_status_created', 'status', 'created_at'),
    )


class ScheduledSearch(Base):
    """Scheduled search model for automated recurring searches."""
    __tablename__ = "scheduled_searches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    capabilities = Column(JSONB, default=list, nullable=False)  # List of capabilities: ["exposure_discovery", "dark_web_intelligence", etc.]
    target = Column(String(500), nullable=False)  # Domain, keywords, URL, etc.
    config = Column(JSONB, default=dict, nullable=True)  # Capability-specific configuration (can be per-capability)
    schedule_type = Column(String(20), nullable=False, default="cron")  # cron, interval, date
    cron_expression = Column(String(100), nullable=True)  # e.g., "0 9 * * *" for daily at 9 AM
    timezone = Column(String(50), default="UTC", nullable=False)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    run_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="scheduled_searches")
    
    __table_args__ = (
        Index('idx_scheduled_search_user_enabled', 'user_id', 'enabled'),
        Index('idx_scheduled_search_next_run', 'next_run_at'),
    )
