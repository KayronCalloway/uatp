#!/usr/bin/env python3
"""
UATP Capsule Engine Security Validation Script
Comprehensive security validation for production deployment
"""

import json
import os
import sys
import subprocess
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SecurityValidator:
    """Comprehensive security validation for UATP Capsule Engine"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "version": "2.0",
            "overall_status": "unknown",
            "categories": {},
            "recommendations": [],
            "compliance_status": {},
        }

    def validate_all(self) -> Dict[str, Any]:
        """Run all security validations"""
        logger.info("Starting comprehensive security validation...")

        # Run all validation categories
        self.validate_dependencies()
        self.validate_tls_configuration()
        self.validate_kubernetes_security()
        self.validate_container_security()
        self.validate_network_policies()
        self.validate_rbac_policies()
        self.validate_secrets_management()
        self.validate_compliance_frameworks()

        # Calculate overall status
        self._calculate_overall_status()

        # Generate recommendations
        self._generate_recommendations()

        logger.info(
            f"Security validation completed. Overall status: {self.validation_results['overall_status']}"
        )
        return self.validation_results

    def validate_dependencies(self) -> None:
        """Validate dependency security"""
        logger.info("Validating dependency security...")

        results = {
            "status": "pass",
            "vulnerabilities": [],
            "outdated_packages": [],
            "security_tools": [],
        }

        # Check if security scanning tools are configured
        requirements_files = ["requirements.txt", "requirements-production.txt"]
        security_packages = ["safety", "bandit", "semgrep", "pip-audit"]

        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                content = req_path.read_text()
                for pkg in security_packages:
                    if pkg in content:
                        results["security_tools"].append(pkg)

        # Check for known vulnerable packages (simplified check)
        vulnerable_patterns = [
            "flask<2.0",
            "django<3.2",
            "requests<2.25",
            "pyyaml<5.4",
            "pillow<8.1.1",
        ]

        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                content = req_path.read_text().lower()
                for pattern in vulnerable_patterns:
                    if pattern in content:
                        results["vulnerabilities"].append(
                            {"file": req_file, "pattern": pattern, "severity": "high"}
                        )

        # Update results
        if results["vulnerabilities"]:
            results["status"] = "fail"
        elif len(results["security_tools"]) < 3:
            results["status"] = "warning"

        self.validation_results["categories"]["dependencies"] = results

    def validate_tls_configuration(self) -> None:
        """Validate TLS/SSL configuration"""
        logger.info("Validating TLS configuration...")

        results = {
            "status": "pass",
            "haproxy_config": {},
            "ingress_config": {},
            "issues": [],
        }

        # Check HAProxy configuration
        haproxy_config = self.project_root / "deployment/docker/haproxy/haproxy.cfg"
        if haproxy_config.exists():
            content = haproxy_config.read_text()

            # Check for TLS 1.3 support
            if "TLSv1.3" in content:
                results["haproxy_config"]["tls13_enabled"] = True
            else:
                results["issues"].append("TLS 1.3 not enabled in HAProxy")
                results["status"] = "warning"

            # Check for weak ciphers
            weak_ciphers = ["RC4", "MD5", "SHA1", "DES", "3DES"]
            for cipher in weak_ciphers:
                if cipher in content:
                    results["issues"].append(
                        f"Weak cipher {cipher} found in HAProxy config"
                    )
                    results["status"] = "fail"

            # Check for security headers
            security_headers = [
                "Strict-Transport-Security",
                "X-Frame-Options",
                "X-Content-Type-Options",
                "Content-Security-Policy",
            ]

            for header in security_headers:
                if header in content:
                    results["haproxy_config"][
                        f"{header.lower().replace('-', '_')}_enabled"
                    ] = True
                else:
                    results["issues"].append(f"Missing security header: {header}")
                    results["status"] = "warning"

        # Check Kubernetes Ingress configuration
        ingress_files = list(self.project_root.glob("k8s/**/ingress*.yaml"))
        for ingress_file in ingress_files:
            try:
                with open(ingress_file) as f:
                    ingress_configs = list(yaml.safe_load_all(f))

                for config in ingress_configs:
                    if config and config.get("kind") == "Ingress":
                        annotations = config.get("metadata", {}).get("annotations", {})

                        # Check SSL redirect
                        if (
                            annotations.get("nginx.ingress.kubernetes.io/ssl-redirect")
                            == "true"
                        ):
                            results["ingress_config"]["ssl_redirect"] = True

                        # Check TLS protocols
                        ssl_protocols = annotations.get(
                            "nginx.ingress.kubernetes.io/ssl-protocols", ""
                        )
                        if "TLSv1.3" in ssl_protocols:
                            results["ingress_config"]["tls13_enabled"] = True

            except Exception as e:
                logger.warning(f"Error reading ingress file {ingress_file}: {e}")

        self.validation_results["categories"]["tls_configuration"] = results

    def validate_kubernetes_security(self) -> None:
        """Validate Kubernetes security configurations"""
        logger.info("Validating Kubernetes security...")

        results = {
            "status": "pass",
            "pod_security": {},
            "network_policies": {},
            "rbac": {},
            "issues": [],
        }

        # Check for pod security policies
        k8s_files = list(self.project_root.glob("k8s/**/*.yaml"))

        pod_security_checks = {
            "runAsNonRoot": False,
            "readOnlyRootFilesystem": False,
            "allowPrivilegeEscalation": False,
            "capabilities_dropped": False,
        }

        network_policy_found = False
        rbac_found = False

        for k8s_file in k8s_files:
            try:
                with open(k8s_file) as f:
                    configs = list(yaml.safe_load_all(f))

                for config in configs:
                    if not config:
                        continue

                    kind = config.get("kind", "")

                    # Check NetworkPolicy
                    if kind == "NetworkPolicy":
                        network_policy_found = True
                        results["network_policies"]["policies_found"] = True

                    # Check RBAC
                    if kind in [
                        "Role",
                        "ClusterRole",
                        "RoleBinding",
                        "ClusterRoleBinding",
                    ]:
                        rbac_found = True
                        results["rbac"]["rbac_found"] = True

                    # Check Pod security context
                    if kind in ["Deployment", "StatefulSet", "DaemonSet", "Pod"]:
                        spec = config.get("spec", {})
                        if kind != "Pod":
                            spec = spec.get("template", {}).get("spec", {})

                        security_context = spec.get("securityContext", {})
                        if security_context.get("runAsNonRoot") == True:
                            pod_security_checks["runAsNonRoot"] = True

                        containers = spec.get("containers", [])
                        for container in containers:
                            container_security = container.get("securityContext", {})

                            if container_security.get("readOnlyRootFilesystem") == True:
                                pod_security_checks["readOnlyRootFilesystem"] = True

                            if (
                                container_security.get("allowPrivilegeEscalation")
                                == False
                            ):
                                pod_security_checks["allowPrivilegeEscalation"] = True

                            capabilities = container_security.get("capabilities", {})
                            if "ALL" in capabilities.get("drop", []):
                                pod_security_checks["capabilities_dropped"] = True

            except Exception as e:
                logger.warning(f"Error reading Kubernetes file {k8s_file}: {e}")

        # Evaluate results
        if not network_policy_found:
            results["issues"].append(
                "No NetworkPolicy found - network traffic not restricted"
            )
            results["status"] = "fail"

        if not rbac_found:
            results["issues"].append(
                "No RBAC policies found - access control not implemented"
            )
            results["status"] = "fail"

        failed_pod_checks = [k for k, v in pod_security_checks.items() if not v]
        if failed_pod_checks:
            results["issues"].extend(
                [f"Pod security check failed: {check}" for check in failed_pod_checks]
            )
            results["status"] = "fail"

        results["pod_security"] = pod_security_checks
        results["network_policies"]["found"] = network_policy_found
        results["rbac"]["found"] = rbac_found

        self.validation_results["categories"]["kubernetes_security"] = results

    def validate_container_security(self) -> None:
        """Validate container security"""
        logger.info("Validating container security...")

        results = {"status": "pass", "dockerfile_security": {}, "issues": []}

        # Check Dockerfile
        dockerfile = self.project_root / "Dockerfile"
        if dockerfile.exists():
            content = dockerfile.read_text()

            # Check for non-root user
            if "USER " in content and "USER root" not in content:
                results["dockerfile_security"]["non_root_user"] = True
            else:
                results["issues"].append("Container runs as root user")
                results["status"] = "warning"

            # Check for security updates
            if "apt-get update" in content and "apt-get upgrade" in content:
                results["dockerfile_security"]["security_updates"] = True

            # Check for minimal base image
            base_images = ["alpine", "distroless", "scratch"]
            first_line = content.split("\n")[0].lower()
            if any(base in first_line for base in base_images):
                results["dockerfile_security"]["minimal_base_image"] = True
            else:
                results["issues"].append("Not using minimal base image")
                results["status"] = "warning"

            # Check for COPY vs ADD
            if "ADD " in content:
                results["issues"].append(
                    "Using ADD instead of COPY - potential security risk"
                )
                results["status"] = "warning"

        self.validation_results["categories"]["container_security"] = results

    def validate_network_policies(self) -> None:
        """Validate network security policies"""
        logger.info("Validating network policies...")

        results = {
            "status": "pass",
            "policies_found": [],
            "default_deny": False,
            "issues": [],
        }

        network_policy_files = list(self.project_root.glob("k8s/**/network*.yaml"))
        network_policy_files.extend(
            list(self.project_root.glob("k8s/**/*network*.yaml"))
        )

        for policy_file in network_policy_files:
            try:
                with open(policy_file) as f:
                    configs = list(yaml.safe_load_all(f))

                for config in configs:
                    if config and config.get("kind") == "NetworkPolicy":
                        policy_name = config.get("metadata", {}).get("name", "unknown")
                        results["policies_found"].append(policy_name)

                        # Check for default deny policy
                        spec = config.get("spec", {})
                        pod_selector = spec.get("podSelector", {})

                        if not pod_selector or pod_selector == {}:
                            policy_types = spec.get("policyTypes", [])
                            ingress_rules = spec.get("ingress", [])
                            egress_rules = spec.get("egress", [])

                            if ("Ingress" in policy_types and not ingress_rules) or (
                                "Egress" in policy_types and not egress_rules
                            ):
                                results["default_deny"] = True

            except Exception as e:
                logger.warning(f"Error reading network policy file {policy_file}: {e}")

        if not results["policies_found"]:
            results["issues"].append("No NetworkPolicies found")
            results["status"] = "fail"

        if not results["default_deny"]:
            results["issues"].append("No default deny NetworkPolicy found")
            results["status"] = "warning"

        self.validation_results["categories"]["network_policies"] = results

    def validate_rbac_policies(self) -> None:
        """Validate RBAC policies"""
        logger.info("Validating RBAC policies...")

        results = {
            "status": "pass",
            "service_accounts": [],
            "roles": [],
            "cluster_roles": [],
            "issues": [],
        }

        rbac_files = list(self.project_root.glob("k8s/**/rbac*.yaml"))
        rbac_files.extend(list(self.project_root.glob("k8s/**/*rbac*.yaml")))
        rbac_files.extend(list(self.project_root.glob("k8s/**/security*.yaml")))

        for rbac_file in rbac_files:
            try:
                with open(rbac_file) as f:
                    configs = list(yaml.safe_load_all(f))

                for config in configs:
                    if not config:
                        continue

                    kind = config.get("kind", "")
                    name = config.get("metadata", {}).get("name", "unknown")

                    if kind == "ServiceAccount":
                        results["service_accounts"].append(name)
                    elif kind == "Role":
                        results["roles"].append(name)

                        # Check for overly permissive rules
                        rules = config.get("rules", [])
                        for rule in rules:
                            verbs = rule.get("verbs", [])
                            if "*" in verbs:
                                results["issues"].append(
                                    f"Role {name} has wildcard permissions"
                                )
                                results["status"] = "warning"

                    elif kind == "ClusterRole":
                        results["cluster_roles"].append(name)

                        # Check for cluster-admin permissions
                        rules = config.get("rules", [])
                        for rule in rules:
                            verbs = rule.get("verbs", [])
                            resources = rule.get("resources", [])
                            if "*" in verbs and "*" in resources:
                                results["issues"].append(
                                    f"ClusterRole {name} has cluster-admin permissions"
                                )
                                results["status"] = "fail"

            except Exception as e:
                logger.warning(f"Error reading RBAC file {rbac_file}: {e}")

        if not results["service_accounts"]:
            results["issues"].append("No custom ServiceAccounts found")
            results["status"] = "warning"

        self.validation_results["categories"]["rbac_policies"] = results

    def validate_secrets_management(self) -> None:
        """Validate secrets management"""
        logger.info("Validating secrets management...")

        results = {
            "status": "pass",
            "secret_files": [],
            "hardcoded_secrets": [],
            "issues": [],
        }

        # Check for Kubernetes secret files
        secret_files = list(self.project_root.glob("k8s/**/secret*.yaml"))
        for secret_file in secret_files:
            results["secret_files"].append(
                str(secret_file.relative_to(self.project_root))
            )

        # Scan for potential hardcoded secrets in code
        code_files = list(self.project_root.glob("src/**/*.py"))
        code_files.extend(list(self.project_root.glob("*.py")))

        secret_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "api_key",
            "private_key",
        ]

        for code_file in code_files:
            try:
                content = code_file.read_text()
                lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    if any(pattern in line_lower for pattern in secret_patterns):
                        if "=" in line and not line.strip().startswith("#"):
                            # Check if it looks like a hardcoded secret
                            if (
                                any(char in line for char in ['"', "'"])
                                and len(line.split("=")[1].strip(" \"'")) > 10
                            ):
                                results["hardcoded_secrets"].append(
                                    {
                                        "file": str(
                                            code_file.relative_to(self.project_root)
                                        ),
                                        "line": i,
                                        "content": line.strip()[
                                            :100
                                        ],  # Truncate for safety
                                    }
                                )

            except Exception as e:
                logger.warning(f"Error scanning file {code_file}: {e}")

        if results["hardcoded_secrets"]:
            results["issues"].append(
                f"Found {len(results['hardcoded_secrets'])} potential hardcoded secrets"
            )
            results["status"] = "fail"

        self.validation_results["categories"]["secrets_management"] = results

    def validate_compliance_frameworks(self) -> None:
        """Validate compliance with security frameworks"""
        logger.info("Validating compliance frameworks...")

        frameworks = {
            "OWASP": {
                "status": "unknown",
                "requirements": {
                    "A01_Broken_Access_Control": False,
                    "A02_Cryptographic_Failures": False,
                    "A03_Injection": False,
                    "A04_Insecure_Design": False,
                    "A05_Security_Misconfiguration": False,
                    "A06_Vulnerable_Components": False,
                    "A07_Authentication_Failures": False,
                    "A08_Software_Integrity_Failures": False,
                    "A09_Logging_Failures": False,
                    "A10_SSRF": False,
                },
            },
            "NIST": {
                "status": "unknown",
                "requirements": {
                    "Identify": False,
                    "Protect": False,
                    "Detect": False,
                    "Respond": False,
                    "Recover": False,
                },
            },
        }

        # Basic compliance checks based on previous validations
        categories = self.validation_results["categories"]

        # OWASP compliance
        if categories.get("rbac_policies", {}).get("status") == "pass":
            frameworks["OWASP"]["requirements"]["A01_Broken_Access_Control"] = True

        if categories.get("tls_configuration", {}).get("status") == "pass":
            frameworks["OWASP"]["requirements"]["A02_Cryptographic_Failures"] = True

        if categories.get("dependencies", {}).get("status") == "pass":
            frameworks["OWASP"]["requirements"]["A06_Vulnerable_Components"] = True

        # NIST compliance
        if categories.get("network_policies", {}).get("status") == "pass":
            frameworks["NIST"]["requirements"]["Protect"] = True

        if len(categories.get("dependencies", {}).get("security_tools", [])) > 0:
            frameworks["NIST"]["requirements"]["Detect"] = True

        # Calculate framework compliance percentages
        for framework_name, framework in frameworks.items():
            requirements = framework["requirements"]
            passed = sum(1 for v in requirements.values() if v)
            total = len(requirements)
            compliance_percentage = (passed / total) * 100

            if compliance_percentage >= 80:
                framework["status"] = "compliant"
            elif compliance_percentage >= 60:
                framework["status"] = "partially_compliant"
            else:
                framework["status"] = "non_compliant"

            framework["compliance_percentage"] = compliance_percentage

        self.validation_results["compliance_status"] = frameworks

    def _calculate_overall_status(self) -> None:
        """Calculate overall security status"""
        categories = self.validation_results["categories"]

        failed_categories = [
            k for k, v in categories.items() if v.get("status") == "fail"
        ]
        warning_categories = [
            k for k, v in categories.items() if v.get("status") == "warning"
        ]

        if failed_categories:
            self.validation_results["overall_status"] = "fail"
        elif warning_categories:
            self.validation_results["overall_status"] = "warning"
        else:
            self.validation_results["overall_status"] = "pass"

    def _generate_recommendations(self) -> None:
        """Generate security recommendations"""
        categories = self.validation_results["categories"]
        recommendations = []

        # High priority recommendations
        if self.validation_results["overall_status"] == "fail":
            recommendations.append(
                {
                    "priority": "critical",
                    "category": "general",
                    "title": "Critical Security Issues Found",
                    "description": "Address all failed security categories immediately before production deployment",
                }
            )

        # Specific recommendations
        for category, data in categories.items():
            if data.get("status") == "fail":
                issues = data.get("issues", [])
                for issue in issues[:3]:  # Top 3 issues per category
                    recommendations.append(
                        {
                            "priority": "high",
                            "category": category,
                            "title": f"{category.replace('_', ' ').title()} Issue",
                            "description": issue,
                        }
                    )

        # Compliance recommendations
        compliance = self.validation_results["compliance_status"]
        for framework, data in compliance.items():
            if data["compliance_percentage"] < 80:
                recommendations.append(
                    {
                        "priority": "medium",
                        "category": "compliance",
                        "title": f"{framework} Compliance Gap",
                        "description": f"Only {data['compliance_percentage']:.0f}% compliant with {framework}. Review and implement missing controls.",
                    }
                )

        self.validation_results["recommendations"] = recommendations

    def generate_report(self, output_format: str = "json") -> str:
        """Generate validation report"""
        if output_format == "json":
            return json.dumps(self.validation_results, indent=2)

        elif output_format == "markdown":
            return self._generate_markdown_report()

        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_markdown_report(self) -> str:
        """Generate markdown report"""
        status_emoji = {"pass": "✅", "warning": "⚠️", "fail": "❌", "unknown": "❔"}

        report = f"""# UATP Capsule Engine Security Validation Report

**Validation Date**: {self.validation_results['timestamp']}
**Overall Status**: {status_emoji.get(self.validation_results['overall_status'], '❔')} {self.validation_results['overall_status'].upper()}

## Security Categories

"""

        for category, data in self.validation_results["categories"].items():
            status = data.get("status", "unknown")
            emoji = status_emoji.get(status, "❔")

            report += f"### {emoji} {category.replace('_', ' ').title()}\n"
            report += f"**Status**: {status.upper()}\n\n"

            if data.get("issues"):
                report += "**Issues Found**:\n"
                for issue in data["issues"]:
                    report += f"- {issue}\n"
                report += "\n"

        # Compliance Status
        report += "## Compliance Framework Status\n\n"
        for framework, data in self.validation_results["compliance_status"].items():
            status = data["status"]
            percentage = data["compliance_percentage"]
            emoji = status_emoji.get(
                "pass"
                if percentage >= 80
                else "warning"
                if percentage >= 60
                else "fail",
                "❔",
            )

            report += f"### {emoji} {framework}\n"
            report += f"**Compliance**: {percentage:.0f}%\n"
            report += f"**Status**: {status.replace('_', ' ').title()}\n\n"

        # Recommendations
        if self.validation_results["recommendations"]:
            report += "## Recommendations\n\n"
            for rec in self.validation_results["recommendations"]:
                priority_emoji = {
                    "critical": "🚨",
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢",
                }.get(rec["priority"], "📋")
                report += f"### {priority_emoji} {rec['title']}\n"
                report += f"**Priority**: {rec['priority'].upper()}\n"
                report += f"**Category**: {rec['category']}\n"
                report += f"**Description**: {rec['description']}\n\n"

        return report


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="UATP Security Validation")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument(
        "--output-format",
        choices=["json", "markdown"],
        default="json",
        help="Output format",
    )
    parser.add_argument("--output-file", help="Output file path")
    parser.add_argument(
        "--exit-on-fail",
        action="store_true",
        help="Exit with error code if validation fails",
    )

    args = parser.parse_args()

    # Run validation
    validator = SecurityValidator(args.project_root)
    results = validator.validate_all()

    # Generate report
    report = validator.generate_report(args.output_format)

    # Output results
    if args.output_file:
        with open(args.output_file, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {args.output_file}")
    else:
        print(report)

    # Exit with appropriate code
    if args.exit_on_fail and results["overall_status"] == "fail":
        logger.error("Security validation failed!")
        sys.exit(1)

    logger.info("Security validation completed successfully")


if __name__ == "__main__":
    main()
