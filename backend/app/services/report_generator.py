"""
Report Generator Service

Generate professional PDF and HTML reports.
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from weasyprint import HTML, CSS
from io import BytesIO

from app.config import settings


class ReportGenerator:
    """
    Report Generator Service.
    
    Features:
    - Executive summary reports
    - Technical detail reports
    - Custom templates
    - PDF and HTML output
    """
    
    def __init__(self, templates_dir: Path = None):
        """Initialize report generator.
        
        Args:
            templates_dir: Path to templates directory
        """
        self.templates_dir = templates_dir or Path(__file__).parent / "templates"
        self.output_dir = settings.DATA_DIR / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        if self.templates_dir.exists():
            self._env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        else:
            self._env = None
    
    def generate_executive_summary(self, data: Dict[str, Any], format: str = "pdf", report_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate executive summary report.
        
        Args:
            data: Report data
            format: Output format ("pdf" or "html")
            report_id: Optional custom report ID
            
        Returns:
            Report metadata
        """
        if not report_id:
            report_id = f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Generate HTML content
        html_content = self._render_executive_summary(data)
        
        if format == "pdf":
            # Generate PDF
            pdf_path = self.output_dir / f"{report_id}.pdf"
            HTML(string=html_content).write_pdf(str(pdf_path))
            
            return {
                "report_id": report_id,
                "type": "executive_summary",
                "format": "pdf",
                "path": str(pdf_path),
                "generated_at": datetime.utcnow().isoformat()
            }
        else:
            # Save HTML
            html_path = self.output_dir / f"{report_id}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "report_id": report_id,
                "type": "executive_summary",
                "format": "html",
                "path": str(html_path),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    def generate_pdf_bytes(self, data: Dict[str, Any]) -> bytes:
        """Generate PDF report as bytes.
        
        Args:
            data: Report data
            
        Returns:
            PDF bytes
        """
        html_content = self._render_executive_summary(data)
        pdf_bytes = BytesIO()
        HTML(string=html_content).write_pdf(pdf_bytes)
        return pdf_bytes.getvalue()
    
    def _render_executive_summary(self, data: Dict[str, Any]) -> str:
        """Render executive summary HTML.
        
        Args:
            data: Report data
            
        Returns:
            HTML content
        """
        # Default template if no custom templates
        # Using direct color values instead of CSS variables for better PDF compatibility
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CyberNexus Executive Summary</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.6;
            color: #212529;
            background: #ffffff;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 100%;
            margin: 0 auto;
        }}
        .header {{
            background: #1e3a5f;
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .header .meta {{
            opacity: 0.9;
            font-size: 14px;
        }}
        .section {{
            background: white;
            padding: 25px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .section h2 {{
            color: #1e3a5f;
            border-bottom: 2px solid #4a90d9;
            padding-bottom: 10px;
            margin-top: 0;
            font-size: 20px;
        }}
        .stats-grid {{
            width: 100%;
            margin: 20px 0;
            border: none;
        }}
        .stats-grid td {{
            border: none;
            padding: 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            width: 25%;
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #1e3a5f;
        }}
        .stat-card .label {{
            color: #666;
            margin-top: 10px;
        }}
        .severity-critical {{ color: #dc3545; }}
        .severity-high {{ color: #fd7e14; }}
        .severity-medium {{ color: #ffc107; }}
        .severity-low {{ color: #28a745; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #1e3a5f;
            color: white;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-critical {{
            background: #dc3545;
            color: white;
        }}
        .badge-high {{
            background: #fd7e14;
            color: white;
        }}
        .badge-medium {{
            background: #ffc107;
            color: black;
        }}
        .badge-low {{
            background: #28a745;
            color: white;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
            margin-top: 40px;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ CyberNexus Security Report</h1>
            <div class="meta">
                <strong>Executive Summary</strong> | 
                Generated: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}
            </div>
        </div>

        <div class="section">
            <h2>Overview</h2>
            <table class="stats-grid" style="width: 100%; border: none;">
                <tr>
                    <td class="stat-card">
                        <div class="value">{data.get('total_threats', 0)}</div>
                        <div class="label">Total Threats</div>
                    </td>
                    <td class="stat-card">
                        <div class="value severity-critical">{data.get('critical_threats', 0)}</div>
                        <div class="label">Critical</div>
                    </td>
                    <td class="stat-card">
                        <div class="value severity-high">{data.get('high_threats', 0)}</div>
                        <div class="label">High</div>
                    </td>
                    <td class="stat-card">
                        <div class="value">{data.get('assets_discovered', 0)}</div>
                        <div class="label">Assets Discovered</div>
                    </td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>Top Threats</h2>
            <table>
                <thead>
                    <tr>
                        <th>Threat</th>
                        <th>Severity</th>
                        <th>Category</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td>{t.get('title', 'Unknown')}</td>
                        <td><span class="badge badge-{t.get('severity', 'medium')}">{t.get('severity', 'Medium').upper()}</span></td>
                        <td>{t.get('category', 'N/A')}</td>
                        <td>{t.get('score', 0)}</td>
                    </tr>
                    ''' for t in data.get('top_threats', [])])}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Recommendations</h2>
            <ul>
                {''.join([f'<li>{r}</li>' for r in data.get('recommendations', ['No recommendations at this time'])])}
            </ul>
        </div>

        <div class="footer">
            <p>Generated by CyberNexus | Enterprise Threat Intelligence Platform</p>
            <p>This report is confidential and intended for authorized personnel only.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def generate_threat_report(self, threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed threat report.
        
        Args:
            threats: List of threats
            
        Returns:
            Report metadata
        """
        report_id = f"THR-RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Aggregate data
        data = {
            "total_threats": len(threats),
            "critical_threats": len([t for t in threats if t.get("severity") == "critical"]),
            "high_threats": len([t for t in threats if t.get("severity") == "high"]),
            "top_threats": sorted(threats, key=lambda x: x.get("score", 0), reverse=True)[:10],
            "recommendations": self._generate_recommendations(threats)
        }
        
        return self.generate_executive_summary(data)
    
    def _generate_recommendations(self, threats: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on threats.
        
        Args:
            threats: List of threats
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for critical threats
        critical = [t for t in threats if t.get("severity") == "critical"]
        if critical:
            recommendations.append(f"Immediately address {len(critical)} critical threats")
        
        # Check for credential exposures
        cred_threats = [t for t in threats if t.get("category") == "credential_exposure"]
        if cred_threats:
            recommendations.append("Reset passwords for exposed credentials and enable MFA")
        
        # Check for misconfigurations
        misconfig = [t for t in threats if t.get("category") == "misconfiguration"]
        if misconfig:
            recommendations.append("Review and fix security configurations")
        
        if not recommendations:
            recommendations.append("Continue monitoring for new threats")
        
        return recommendations
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """List all generated reports.
        
        Returns:
            List of report metadata
        """
        reports = []
        
        # List both HTML and PDF reports
        for report_file in self.output_dir.glob("*.*"):
            if report_file.suffix in [".html", ".pdf"]:
                reports.append({
                    "report_id": report_file.stem,
                    "format": report_file.suffix[1:],  # Remove the dot
                    "path": str(report_file),
                    "size": report_file.stat().st_size,
                    "created": datetime.fromtimestamp(report_file.stat().st_ctime).isoformat()
                })
        
        return sorted(reports, key=lambda x: x["created"], reverse=True)


