import { InfrastructureFinding, InfrastructureStats } from "@/components/infrastructure/helpers";

export function exportInfrastructureJSON(
  findings: InfrastructureFinding[],
  stats: InfrastructureStats,
  filename?: string
): void {
  const data = {
    metadata: {
      exportDate: new Date().toISOString(),
      totalFindings: findings.length,
      stats,
    },
    findings,
  };

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || `infrastructure-findings-${new Date().toISOString().split("T")[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function exportInfrastructureCSV(
  findings: InfrastructureFinding[],
  filename?: string
): void {
  const headers = [
    "ID",
    "Title",
    "Severity",
    "Category",
    "Description",
    "Risk Score",
    "Affected Assets",
    "Timestamp",
    "Recommendations",
  ];

  const rows = findings.map((finding) => {
    return [
      finding.id,
      `"${finding.title.replace(/"/g, '""')}"`,
      finding.severity,
      finding.category,
      `"${finding.description.replace(/"/g, '""')}"`,
      finding.riskScore.toString(),
      finding.affectedAssets.join("; "),
      finding.timestamp,
      `"${finding.recommendations.join("; ").replace(/"/g, '""')}"`,
    ];
  });

  const csvContent = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || `infrastructure-findings-${new Date().toISOString().split("T")[0]}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Export findings as PDF (basic implementation using browser print)
 * For a full PDF implementation, you would need a library like jsPDF or pdfkit
 */
export function exportInfrastructurePDF(
  findings: InfrastructureFinding[],
  stats: InfrastructureStats,
  target: string
): void {
  // Create a printable HTML document
  const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <title>Infrastructure Security Report</title>
  <style>
    body {
      font-family: 'Courier New', monospace;
      padding: 20px;
      color: #333;
    }
    h1 { color: #10b981; }
    h2 { color: #3b82f6; margin-top: 20px; }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 8px;
      text-align: left;
    }
    th {
      background-color: #f2f2f2;
    }
    .severity-critical { color: #ef4444; font-weight: bold; }
    .severity-high { color: #f97316; font-weight: bold; }
    .severity-medium { color: #eab308; }
    .severity-low { color: #3b82f6; }
    .severity-info { color: #8b5cf6; }
    .stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      margin: 20px 0;
    }
    .stat-box {
      border: 1px solid #ddd;
      padding: 15px;
      text-align: center;
    }
    .stat-value {
      font-size: 24px;
      font-weight: bold;
      color: #10b981;
    }
    @media print {
      body { margin: 0; }
      .no-print { display: none; }
    }
  </style>
</head>
<body>
  <h1>Infrastructure Security Report</h1>
  <p><strong>Target:</strong> ${target}</p>
  <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
  
  <h2>Summary Statistics</h2>
  <div class="stats">
    <div class="stat-box">
      <div class="stat-value">${stats.totalFindings}</div>
      <div>Total Findings</div>
    </div>
    <div class="stat-box">
      <div class="stat-value">${stats.criticalFindings}</div>
      <div>Critical</div>
    </div>
    <div class="stat-box">
      <div class="stat-value">${stats.highFindings}</div>
      <div>High</div>
    </div>
  </div>
  
  <h2>Findings</h2>
  <table>
    <thead>
      <tr>
        <th>Title</th>
        <th>Severity</th>
        <th>Category</th>
        <th>Risk Score</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
      ${findings
        .map(
          (finding) => `
        <tr>
          <td>${finding.title}</td>
          <td class="severity-${finding.severity}">${finding.severity.toUpperCase()}</td>
          <td>${finding.category}</td>
          <td>${finding.riskScore}</td>
          <td>${finding.description}</td>
        </tr>
      `
        )
        .join("")}
    </tbody>
  </table>
</body>
</html>
  `;

  // Open in new window and trigger print
  const printWindow = window.open("", "_blank");
  if (printWindow) {
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
  }
}

/**
 * Export all formats
 */
export function exportInfrastructure(
  format: "json" | "csv" | "pdf",
  findings: InfrastructureFinding[],
  stats: InfrastructureStats,
  target: string,
  filename?: string
): void {
  switch (format) {
    case "json":
      exportInfrastructureJSON(findings, stats, filename);
      break;
    case "csv":
      exportInfrastructureCSV(findings, filename);
      break;
    case "pdf":
      exportInfrastructurePDF(findings, stats, target);
      break;
    default:
      throw new Error(`Unsupported export format: ${format}`);
  }
}

