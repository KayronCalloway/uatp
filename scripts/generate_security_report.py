#!/usr/bin/env python3
"""
Security Report Generator
Aggregates security scan results into comprehensive reports
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def load_json_safely(file_path: Path) -> Dict[str, Any]:
    """Load JSON file safely, return empty dict if file doesn't exist or is invalid"""
    try:
        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return {}


def parse_safety_report(results_dir: Path) -> Dict[str, Any]:
    """Parse Safety vulnerability report"""
    safety_file = results_dir / "dependency-scan-results" / "safety-report.json"
    safety_data = load_json_safely(safety_file)

    vulnerabilities = []
    if isinstance(safety_data, list):
        for vuln in safety_data:
            if isinstance(vuln, dict):
                vulnerabilities.append(
                    {
                        "package": vuln.get("package_name", "unknown"),
                        "version": vuln.get("analyzed_version", "unknown"),
                        "vulnerability_id": vuln.get("vulnerability_id", "unknown"),
                        "advisory": vuln.get("advisory", "No advisory available"),
                        "severity": vuln.get("severity", "unknown"),
                    }
                )

    return {
        "tool": "safety",
        "total_vulnerabilities": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
    }


def parse_bandit_report(results_dir: Path) -> Dict[str, Any]:
    """Parse Bandit security report"""
    bandit_file = results_dir / "code-security-scan-results" / "bandit-report.json"
    bandit_data = load_json_safely(bandit_file)

    issues = []
    metrics = bandit_data.get("metrics", {})

    for result in bandit_data.get("results", []):
        issues.append(
            {
                "filename": result.get("filename", "unknown"),
                "test_name": result.get("test_name", "unknown"),
                "test_id": result.get("test_id", "unknown"),
                "issue_severity": result.get("issue_severity", "unknown"),
                "issue_confidence": result.get("issue_confidence", "unknown"),
                "issue_text": result.get("issue_text", "No description"),
                "line_number": result.get("line_number", 0),
            }
        )

    return {
        "tool": "bandit",
        "total_issues": len(issues),
        "issues": issues,
        "metrics": {
            "files_scanned": metrics.get("_totals", {}).get("loc", 0),
            "lines_of_code": metrics.get("_totals", {}).get("loc", 0),
        },
    }


def parse_semgrep_report(results_dir: Path) -> Dict[str, Any]:
    """Parse Semgrep security report"""
    semgrep_file = results_dir / "code-security-scan-results" / "semgrep-report.json"
    semgrep_data = load_json_safely(semgrep_file)

    findings = []
    for result in semgrep_data.get("results", []):
        findings.append(
            {
                "rule_id": result.get("check_id", "unknown"),
                "message": result.get("message", "No message"),
                "severity": result.get("extra", {}).get("severity", "unknown"),
                "filename": result.get("path", "unknown"),
                "line": result.get("start", {}).get("line", 0),
                "category": result.get("extra", {})
                .get("metadata", {})
                .get("category", "unknown"),
            }
        )

    return {"tool": "semgrep", "total_findings": len(findings), "findings": findings}


def parse_trivy_report(results_dir: Path) -> Dict[str, Any]:
    """Parse Trivy container security report"""
    trivy_file = results_dir / "container-security-scan-results" / "trivy-results.json"
    trivy_data = load_json_safely(trivy_file)

    vulnerabilities = []
    if "Results" in trivy_data:
        for result in trivy_data["Results"]:
            if "Vulnerabilities" in result:
                for vuln in result["Vulnerabilities"]:
                    vulnerabilities.append(
                        {
                            "vulnerability_id": vuln.get("VulnerabilityID", "unknown"),
                            "package_name": vuln.get("PkgName", "unknown"),
                            "severity": vuln.get("Severity", "unknown"),
                            "title": vuln.get("Title", "No title"),
                            "description": vuln.get("Description", "No description"),
                        }
                    )

    return {
        "tool": "trivy",
        "total_vulnerabilities": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
    }


def parse_license_report(results_dir: Path) -> Dict[str, Any]:
    """Parse license compliance report"""
    license_file = results_dir / "license-compliance-results" / "licenses-pip.json"
    license_data = load_json_safely(license_file)

    licenses = []
    if isinstance(license_data, list):
        for pkg in license_data:
            licenses.append(
                {
                    "name": pkg.get("Name", "unknown"),
                    "version": pkg.get("Version", "unknown"),
                    "license": pkg.get("License", "unknown"),
                    "author": pkg.get("Author", "unknown"),
                }
            )

    # Count license types
    license_counts = {}
    for pkg in licenses:
        license_type = pkg["license"]
        license_counts[license_type] = license_counts.get(license_type, 0) + 1

    return {
        "tool": "pip-licenses",
        "total_packages": len(licenses),
        "packages": licenses,
        "license_distribution": license_counts,
    }


def generate_summary_stats(reports: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary statistics from all reports"""
    total_issues = 0
    critical_issues = 0
    high_issues = 0
    medium_issues = 0
    low_issues = 0

    # Count dependency vulnerabilities
    if "dependency" in reports:
        dep_vulns = reports["dependency"]["total_vulnerabilities"]
        total_issues += dep_vulns
        # Assume all dependency vulns are high priority
        high_issues += dep_vulns

    # Count code security issues
    if "code_security" in reports:
        for issue in reports["code_security"]["issues"]:
            total_issues += 1
            severity = issue.get("issue_severity", "").lower()
            if severity in ["critical", "high"]:
                high_issues += 1
            elif severity == "medium":
                medium_issues += 1
            else:
                low_issues += 1

    # Count semgrep findings
    if "semgrep" in reports:
        for finding in reports["semgrep"]["findings"]:
            total_issues += 1
            severity = finding.get("severity", "").lower()
            if severity == "error":
                high_issues += 1
            elif severity == "warning":
                medium_issues += 1
            else:
                low_issues += 1

    # Count container vulnerabilities
    if "container" in reports:
        for vuln in reports["container"]["vulnerabilities"]:
            total_issues += 1
            severity = vuln.get("severity", "").lower()
            if severity == "critical":
                critical_issues += 1
            elif severity == "high":
                high_issues += 1
            elif severity == "medium":
                medium_issues += 1
            else:
                low_issues += 1

    return {
        "total_issues": total_issues,
        "critical_issues": critical_issues,
        "high_issues": high_issues,
        "medium_issues": medium_issues,
        "low_issues": low_issues,
        "risk_score": calculate_risk_score(
            critical_issues, high_issues, medium_issues, low_issues
        ),
    }


def calculate_risk_score(critical: int, high: int, medium: int, low: int) -> int:
    """Calculate overall risk score (0-100)"""
    score = (critical * 10) + (high * 5) + (medium * 2) + (low * 1)
    return min(100, score)  # Cap at 100


def generate_html_report(reports: Dict[str, Any], summary: Dict[str, Any]) -> str:
    """Generate HTML security report"""

    risk_color = "green"
    if summary["risk_score"] > 50:
        risk_color = "red"
    elif summary["risk_score"] > 20:
        risk_color = "orange"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>UATP Security Scan Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
            .summary {{ background: #e8f4f8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .risk-score {{ font-size: 24px; font-weight: bold; color: {risk_color}; }}
            .section {{ margin: 30px 0; }}
            .issue {{ background: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
            .vulnerability {{ background: #f8d7da; padding: 10px; margin: 10px 0; border-left: 4px solid #dc3545; }}
            .finding {{ background: #d1ecf1; padding: 10px; margin: 10px 0; border-left: 4px solid #17a2b8; }}
            .stats {{ display: flex; gap: 20px; }}
            .stat {{ text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔒 UATP Security Scan Report</h1>
            <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
            <p><strong>Repository:</strong> UATP Capsule Engine</p>
        </div>

        <div class="summary">
            <h2>📊 Executive Summary</h2>
            <div class="stats">
                <div class="stat">
                    <div class="risk-score">{summary["risk_score"]}</div>
                    <div>Risk Score</div>
                </div>
                <div class="stat">
                    <div style="font-size: 20px; font-weight: bold;">{summary["total_issues"]}</div>
                    <div>Total Issues</div>
                </div>
                <div class="stat">
                    <div style="font-size: 20px; font-weight: bold; color: red;">{summary["critical_issues"]}</div>
                    <div>Critical</div>
                </div>
                <div class="stat">
                    <div style="font-size: 20px; font-weight: bold; color: orange;">{summary["high_issues"]}</div>
                    <div>High</div>
                </div>
                <div class="stat">
                    <div style="font-size: 20px; font-weight: bold; color: blue;">{summary["medium_issues"]}</div>
                    <div>Medium</div>
                </div>
                <div class="stat">
                    <div style="font-size: 20px; font-weight: bold; color: gray;">{summary["low_issues"]}</div>
                    <div>Low</div>
                </div>
            </div>
        </div>
    """

    # Add dependency vulnerabilities section
    if "dependency" in reports and reports["dependency"]["total_vulnerabilities"] > 0:
        html += f"""
        <div class="section">
            <h2>🔍 Dependency Vulnerabilities ({reports["dependency"]["total_vulnerabilities"]})</h2>
        """
        for vuln in reports["dependency"]["vulnerabilities"][:10]:  # Show first 10
            html += f"""
            <div class="vulnerability">
                <strong>{vuln["package"]} v{vuln["version"]}</strong> - {vuln["vulnerability_id"]}<br>
                <em>Severity: {vuln["severity"]}</em><br>
                {vuln["advisory"]}
            </div>
            """
        html += "</div>"

    # Add code security issues section
    if "code_security" in reports and reports["code_security"]["total_issues"] > 0:
        html += f"""
        <div class="section">
            <h2>🛡️ Code Security Issues ({reports["code_security"]["total_issues"]})</h2>
        """
        for issue in reports["code_security"]["issues"][:10]:  # Show first 10
            html += f"""
            <div class="issue">
                <strong>{issue["test_name"]}</strong> - {issue["filename"]}:{issue["line_number"]}<br>
                <em>Severity: {issue["issue_severity"]} | Confidence: {issue["issue_confidence"]}</em><br>
                {issue["issue_text"]}
            </div>
            """
        html += "</div>"

    # Add license compliance section
    if "licenses" in reports:
        html += f"""
        <div class="section">
            <h2>📋 License Compliance ({reports["licenses"]["total_packages"]} packages)</h2>
            <p><strong>License Distribution:</strong></p>
            <ul>
        """
        for license_type, count in reports["licenses"]["license_distribution"].items():
            html += f"<li>{license_type}: {count} packages</li>"
        html += "</ul></div>"

    html += """
    </body>
    </html>
    """

    return html


def generate_markdown_summary(summary: Dict[str, Any]) -> str:
    """Generate markdown summary for PR comments"""

    risk_emoji = "🟢"
    if summary["risk_score"] > 50:
        risk_emoji = "🔴"
    elif summary["risk_score"] > 20:
        risk_emoji = "🟠"

    return f"""
### {risk_emoji} Security Scan Summary

**Risk Score:** {summary["risk_score"]}/100

| Severity | Count |
|----------|-------|
| 🔴 Critical | {summary["critical_issues"]} |
| 🟠 High | {summary["high_issues"]} |
| 🟡 Medium | {summary["medium_issues"]} |
| ⚪ Low | {summary["low_issues"]} |
| **Total** | **{summary["total_issues"]}** |

{'⚠️ **Action Required:** Please address critical and high severity issues before merging.' if summary["critical_issues"] + summary["high_issues"] > 0 else '✅ **All Clear:** No critical security issues detected.'}

📊 View the [full security report](../security-report.html) for detailed findings.
    """


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_security_report.py <results_directory>")
        sys.exit(1)

    results_dir = Path(sys.argv[1])

    if not results_dir.exists():
        print(f"Error: Results directory {results_dir} does not exist")
        sys.exit(1)

    print("📊 Generating security report...")

    # Parse all security scan results
    reports = {
        "dependency": parse_safety_report(results_dir),
        "code_security": parse_bandit_report(results_dir),
        "semgrep": parse_semgrep_report(results_dir),
        "container": parse_trivy_report(results_dir),
        "licenses": parse_license_report(results_dir),
    }

    # Generate summary statistics
    summary = generate_summary_stats(reports)

    # Create comprehensive report
    comprehensive_report = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "reports": reports,
    }

    # Write JSON report
    with open("security-report.json", "w") as f:
        json.dump(comprehensive_report, f, indent=2)

    # Write HTML report
    html_report = generate_html_report(reports, summary)
    with open("security-report.html", "w") as f:
        f.write(html_report)

    # Write markdown summary
    md_summary = generate_markdown_summary(summary)
    with open("security-summary.md", "w") as f:
        f.write(md_summary)

    print("✅ Security report generated successfully!")
    print(f"📊 Risk Score: {summary['risk_score']}/100")
    print(f"🔍 Total Issues: {summary['total_issues']}")
    print(
        "📋 Files created: security-report.json, security-report.html, security-summary.md"
    )


if __name__ == "__main__":
    main()
