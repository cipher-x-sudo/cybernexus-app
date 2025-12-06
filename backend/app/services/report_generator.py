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
    
    def generate_executive_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary report.
        
        Args:
            data: Report data
            
        Returns:
            Report metadata
        """
        report_id = f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Generate HTML content
        html_content = self._render_executive_summary(data)
        
        # Save HTML
        html_path = self.output_dir / f"{report_id}.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        return {
            "report_id": report_id,
            "type": "executive_summary",
            "format": "html",
            "path": str(html_path),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _render_executive_summary(self, data: Dict[str, Any]) -> str:
        """Render executive summary HTML.
        
        Args:
            data: Report data
            
        Returns:
            HTML content
        """
        # Default template if no custom templates
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberNexus Executive Summary</title>
    <style>
        :root {{
            --primary: #1e3a5f;
            --secondary: #4a90d9;
            --danger: #dc3545;
            --warning: #ffc107;
            --success: #28a745;
            --bg: #f8f9fa;
            --text: #212529;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
            margin: 0;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: var(--primary);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .header .meta {{ opacity: 0.8; }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: var(--primary);
            border-bottom: 2px solid var(--secondary);
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: var(--bg);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: var(--primary);
        }}
        .stat-card .label {{ color: #666; }}
        .severity-critical {{ color: var(--danger); }}
        .severity-high {{ color: #fd7e14; }}
        .severity-medium {{ color: var(--warning); }}
        .severity-low {{ color: var(--success); }}
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
        th {{ background: var(--primary); color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-critical {{ background: var(--danger); color: white; }}
        .badge-high {{ background: #fd7e14; color: white; }}
        .badge-medium {{ background: var(--warning); color: black; }}
        .badge-low {{ background: var(--success); color: white; }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
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
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">{data.get('total_threats', 0)}</div>
                    <div class="label">Total Threats</div>
                </div>
                <div class="stat-card">
                    <div class="value severity-critical">{data.get('critical_threats', 0)}</div>
                    <div class="label">Critical</div>
                </div>
                <div class="stat-card">
                    <div class="value severity-high">{data.get('high_threats', 0)}</div>
                    <div class="label">High</div>
                </div>
                <div class="stat-card">
                    <div class="value">{data.get('assets_discovered', 0)}</div>
                    <div class="label">Assets Discovered</div>
                </div>
            </div>
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
        
        for report_file in self.output_dir.glob("*.html"):
            reports.append({
                "report_id": report_file.stem,
                "format": "html",
                "path": str(report_file),
                "size": report_file.stat().st_size,
                "created": datetime.fromtimestamp(report_file.stat().st_ctime).isoformat()
            })
        
        return sorted(reports, key=lambda x: x["created"], reverse=True)


