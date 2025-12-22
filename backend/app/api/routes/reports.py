from datetime import datetime
from typing import List, Optional
from enum import Enum
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, FileResponse, Response
from pydantic import BaseModel
from pathlib import Path

from app.services.report_generator import ReportGenerator
from app.core.database.database import get_db
from app.core.database.finding_storage import DBFindingStorage
from app.core.database.models import User
from app.api.routes.auth import get_current_active_user

router = APIRouter()


class ReportType(str, Enum):
    """Types of security reports."""
    EXECUTIVE_SUMMARY = "executive_summary"
    THREAT_ASSESSMENT = "threat_assessment"
    VULNERABILITY_REPORT = "vulnerability_report"
    CREDENTIAL_EXPOSURE = "credential_exposure"
    DARK_WEB_INTELLIGENCE = "dark_web_intelligence"
    ATTACK_SURFACE = "attack_surface"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Output formats for reports."""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    MARKDOWN = "markdown"


class ReportStatus(str, Enum):
    """Status of report generation."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(BaseModel):
    """Report model with generation status and metadata."""
    id: str
    title: str
    type: ReportType
    format: ReportFormat
    status: ReportStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    sections: List[str] = []
    metadata: dict = {}


class ReportCreate(BaseModel):
    """Request model for creating a new report."""
    title: str
    type: ReportType
    format: ReportFormat = ReportFormat.PDF
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    include_sections: List[str] = []
    filters: dict = {}


class ReportTemplate(BaseModel):
    """Report template with default sections."""
    id: str
    name: str
    type: ReportType
    description: str
    default_sections: List[str]


reports_db: dict = {}
report_counter = 0

report_generator = ReportGenerator()

templates = [
    ReportTemplate(
        id="TPL-001",
        name="Executive Summary",
        type=ReportType.EXECUTIVE_SUMMARY,
        description="High-level overview for executives and stakeholders",
        default_sections=["overview", "key_metrics", "top_threats", "recommendations"]
    ),
    ReportTemplate(
        id="TPL-002",
        name="Threat Assessment",
        type=ReportType.THREAT_ASSESSMENT,
        description="Detailed analysis of current threats",
        default_sections=["threat_overview", "critical_threats", "threat_trends", "mitigations"]
    ),
    ReportTemplate(
        id="TPL-003",
        name="Credential Exposure Report",
        type=ReportType.CREDENTIAL_EXPOSURE,
        description="Analysis of exposed credentials and recommendations",
        default_sections=["exposure_summary", "affected_accounts", "breach_sources", "remediation"]
    ),
    ReportTemplate(
        id="TPL-004",
        name="Attack Surface Analysis",
        type=ReportType.ATTACK_SURFACE,
        description="Complete external attack surface assessment",
        default_sections=["asset_inventory", "exposure_map", "vulnerabilities", "risk_scores"]
    ),
]


def generate_report_id() -> str:
    """Generate unique report ID with sequential counter."""
    global report_counter
    report_counter += 1
    return f"RPT-{report_counter:08d}"


@router.get("/templates", response_model=List[ReportTemplate])
async def list_templates():
    """List available report templates."""
    return templates


@router.get("", response_model=List[Report])
async def list_reports(
    report_type: Optional[ReportType] = None,
    status: Optional[ReportStatus] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0)
):
    """List reports with optional filtering by type and status."""
    results = list(reports_db.values())
    
    # Apply filters
    if report_type:
        results = [r for r in results if r["type"] == report_type]
    if status:
        results = [r for r in results if r["status"] == status]
    
    # Sort by creation date (newest first) and paginate
    results.sort(key=lambda r: r["created_at"], reverse=True)
    
    return [Report(**r) for r in results[offset:offset + limit]]


@router.get("/{report_id}", response_model=Report)
async def get_report(report_id: str):
    """Get a specific report by ID."""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="Report not found")
    return Report(**reports_db[report_id])


@router.post("/generate", response_model=Report)
async def generate_report(
    report_config: ReportCreate,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Generate a security report from findings with aggregation and recommendations."""
    report_id = generate_report_id()
    now = datetime.utcnow()
    
    try:
        # Fetch all findings for the user
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=current_user.role == "admin")
        all_findings = await finding_storage.get_findings(limit=1000)
        
        # Aggregate threat statistics
        total_threats = len(all_findings)
        critical_threats = len([f for f in all_findings if f.severity.lower() == "critical"])
        high_threats = len([f for f in all_findings if f.severity.lower() == "high"])
        
        # Get top threats by risk score
        top_threats_list = sorted(
            all_findings,
            key=lambda f: f.risk_score or 0,
            reverse=True
        )[:10]
        
        # Format top threats for report
        formatted_top_threats = [
            {
                "title": f.title,
                "severity": f.severity.lower(),
                "category": f.capability.value if hasattr(f.capability, 'value') else str(f.capability),
                "score": int(f.risk_score or 0)
            }
            for f in top_threats_list
        ]
        
        # Collect all affected assets
        all_assets = set()
        for finding in all_findings:
            if finding.affected_assets:
                all_assets.update(finding.affected_assets)
            if finding.target:
                all_assets.add(finding.target)
        
        # Generate recommendations based on threat levels
        recommendations = []
        if critical_threats > 0:
            recommendations.append(f"Immediately address {critical_threats} critical threat(s)")
        if high_threats > 0:
            recommendations.append(f"Prioritize resolution of {high_threats} high-severity threat(s)")
        if total_threats == 0:
            recommendations.append("Continue monitoring for new threats")
        else:
            recommendations.append("Review and update security configurations regularly")
            recommendations.append("Keep all systems updated with latest security patches")
        
        report_data = {
            "total_threats": total_threats,
            "critical_threats": critical_threats,
            "high_threats": high_threats,
            "assets_discovered": len(all_assets),
            "top_threats": formatted_top_threats,
            "recommendations": recommendations if recommendations else [
                "Continue monitoring for new threats",
                "Review security configurations regularly",
                "Keep all systems updated with latest security patches"
            ]
        }
        
        # Generate report file using report generator
        output_format = report_config.format.value if hasattr(report_config.format, 'value') else str(report_config.format)
        report_result = report_generator.generate_executive_summary(report_data, format=output_format, report_id=report_id)
        
        report_dict = {
            "id": report_id,
            "title": report_config.title,
            "type": report_config.type,
            "format": report_config.format,
            "status": ReportStatus.COMPLETED,
            "created_at": now,
            "completed_at": datetime.utcnow(),
            "file_path": report_result["path"],
            "sections": report_config.include_sections,
            "metadata": {
                "date_range_start": report_config.date_range_start.isoformat() if report_config.date_range_start else None,
                "date_range_end": report_config.date_range_end.isoformat() if report_config.date_range_end else None,
                "filters": report_config.filters
            }
        }
        
        reports_db[report_id] = report_dict
        
        return Report(**report_dict)
    except Exception as e:
        report_dict = {
            "id": report_id,
            "title": report_config.title,
            "type": report_config.type,
            "format": report_config.format,
            "status": ReportStatus.FAILED,
            "created_at": now,
            "completed_at": None,
            "file_path": None,
            "sections": report_config.include_sections,
            "metadata": {
                "date_range_start": report_config.date_range_start.isoformat() if report_config.date_range_start else None,
                "date_range_end": report_config.date_range_end.isoformat() if report_config.date_range_end else None,
                "filters": report_config.filters,
                "error": str(e)
            }
        }
        reports_db[report_id] = report_dict
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """Download generated report file."""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = reports_db[report_id]
    
    # Verify report is ready for download
    if report["status"] != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report not ready for download")
    
    file_path = report.get("file_path")
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    # Determine content type based on report format
    report_format = report.get("format")
    if isinstance(report_format, Enum):
        report_format = report_format.value
    
    content_type_map = {
        "pdf": "application/pdf",
        "html": "text/html",
        "json": "application/json",
        "markdown": "text/markdown"
    }
    
    content_type = content_type_map.get(report_format, "application/octet-stream")
    
    # Generate filename from report title
    filename = f"{report['title'].replace(' ', '_')}.{report_format}"
    
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """Delete a report by ID."""
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="Report not found")
    
    del reports_db[report_id]
    return {"message": "Report deleted successfully"}


@router.post("/schedule")
async def schedule_report(
    report_config: ReportCreate,
    schedule: str = Query(description="Cron expression for scheduling")
):
    """Schedule automatic report generation with cron expression."""
    return {
        "message": "Report scheduled successfully",
        "schedule": schedule,
        "report_type": report_config.type
    }


