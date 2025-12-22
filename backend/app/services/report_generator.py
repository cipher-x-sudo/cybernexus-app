

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
    def __init__(self, templates_dir: Path = None):
        self.templates_dir = templates_dir or Path(__file__).parent / "templates"
        self.output_dir = settings.DATA_DIR / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.templates_dir.exists():
            self._env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        else:
            self._env = None
    
    def generate_executive_summary(self, data: Dict[str, Any], format: str = "pdf", report_id: Optional[str] = None) -> Dict[str, Any]:
        if not report_id:
            report_id = f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        html_content = self._render_executive_summary(data)
        
        if format == "pdf":
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
        html_content = self._render_executive_summary(data)
        pdf_bytes = BytesIO()
        HTML(string=html_content).write_pdf(pdf_bytes)
        return pdf_bytes.getvalue()
    
    def _render_executive_summary(self, data: Dict[str, Any]) -> str:
        

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CyberNexus Executive Summary</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: A4;
            margin: 2cm;
            background: #0a0e1a;
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: rgba(255, 255, 255, 0.95);
            background: #0a0e1a;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            font-weight: 600;
            letter-spacing: -0.02em;
        }}
        .container {{
            max-width: 100%;
            margin: 0 auto;
            background: #0a0e1a;
        }}
        .header {{
            background: #1a2035;
            color: rgba(255, 255, 255, 0.95);
            padding: 35px;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid rgba(245, 158, 11, 0.3);
            box-shadow: 0 0 20px rgba(245, 158, 11, 0.1);
        }}
        .header h1 {{
            margin: 0 0 12px 0;
            font-size: 28px;
            font-weight: 700;
            color: #f59e0b;
            text-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
        }}
        .header .meta {{
            opacity: 0.8;
            font-size: 14px;
            color: rgba(255, 255, 255, 0.7);
            font-family: 'Inter', sans-serif;
        }}
        .section {{
            background: rgba(255, 255, 255, 0.03);
            padding: 28px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            margin-bottom: 24px;
            backdrop-filter: blur(10px);
        }}
        .section h2 {{
            color: #f59e0b;
            border-bottom: 2px solid rgba(245, 158, 11, 0.4);
            padding-bottom: 12px;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 22px;
            font-weight: 600;
        }}
        .stats-grid {{
            width: 100%;
            margin: 20px 0;
            border: none;
            border-collapse: separate;
            border-spacing: 12px;
        }}
        .stats-grid td {{
            border: none;
            padding: 0;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.03);
            padding: 24px;
            border-radius: 10px;
            text-align: center;
            width: 25%;
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s ease;
        }}
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: 700;
            color: #f59e0b;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 8px;
        }}
        .stat-card .label {{
            color: rgba(255, 255, 255, 0.7);
            margin-top: 8px;
            font-size: 13px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .severity-critical {{ color: #ef4444 !important; }}
        .severity-high {{ color: #f97316 !important; }}
        .severity-medium {{ color: #eab308 !important; }}
        .severity-low {{ color: #3b82f6 !important; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }}
        th {{
            background: #1a2035;
            color: #f59e0b;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid rgba(245, 158, 11, 0.4);
        }}
        tbody tr {{
            background: rgba(255, 255, 255, 0.02);
        }}
        tbody tr:nth-child(even) {{
            background: rgba(255, 255, 255, 0.04);
        }}
        tbody tr:hover {{
            background: rgba(255, 255, 255, 0.06);
        }}
        td {{
            color: rgba(255, 255, 255, 0.9);
        }}
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 0.8em;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .badge-critical {{
            background: #ef4444;
            color: white;
        }}
        .badge-high {{
            background: #f97316;
            color: white;
        }}
        .badge-medium {{
            background: #eab308;
            color: #0a0e1a;
        }}
        .badge-low {{
            background: #3b82f6;
            color: white;
        }}
        .badge-info {{
            background: #8b5cf6;
            color: white;
        }}
        .footer {{
            text-align: center;
            padding: 30px 20px;
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.85em;
            margin-top: 50px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .footer p {{
            margin: 6px 0;
        }}
        ul {{
            padding-left: 24px;
            list-style: none;
        }}
        li {{
            margin-bottom: 12px;
            padding-left: 20px;
            position: relative;
            color: rgba(255, 255, 255, 0.85);
        }}
        li:before {{
            content: "▸";
            position: absolute;
            left: 0;
            color: #f59e0b;
            font-weight: bold;
        }}
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: rgba(255, 255, 255, 0.5);
            font-style: italic;
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
            {'<table><thead><tr><th>Threat</th><th>Severity</th><th>Category</th><th>Score</th></tr></thead><tbody>' + ''.join([f'''
                    <tr>
                        <td>{t.get('title', 'Unknown')}</td>
                        <td><span class="badge badge-{t.get('severity', 'medium')}">{t.get('severity', 'Medium').upper()}</span></td>
                        <td>{t.get('category', 'N/A')}</td>
                        <td>{t.get('score', 0)}</td>
                    </tr>
                    ''' for t in data.get('top_threats', [])]) + '</tbody></table>' if data.get('top_threats') else '<div class="empty-state">No threats identified at this time.</div>'}
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
        
        report_id = f"THR-RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        

        data = {
            "total_threats": len(threats),
            "critical_threats": len([t for t in threats if t.get("severity") == "critical"]),
            "high_threats": len([t for t in threats if t.get("severity") == "high"]),
            "top_threats": sorted(threats, key=lambda x: x.get("score", 0), reverse=True)[:10],
            "recommendations": self._generate_recommendations(threats)
        }
        
        return self.generate_executive_summary(data)
    
    def _generate_recommendations(self, threats: List[Dict[str, Any]]) -> List[str]:
        
        recommendations = []
        

        critical = [t for t in threats if t.get("severity") == "critical"]
        if critical:
            recommendations.append(f"Immediately address {len(critical)} critical threats")
        

        cred_threats = [t for t in threats if t.get("category") == "credential_exposure"]
        if cred_threats:
            recommendations.append("Reset passwords for exposed credentials and enable MFA")
        

        misconfig = [t for t in threats if t.get("category") == "misconfiguration"]
        if misconfig:
            recommendations.append("Review and fix security configurations")
        
        if not recommendations:
            recommendations.append("Continue monitoring for new threats")
        
        return recommendations
    
    def list_reports(self) -> List[Dict[str, Any]]:
        
        reports = []
        

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


