# report_generator.py
"""
Report Generation Module
Creates detailed compliance reports highlighting issues, decisions, and actions
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ReportType(str, Enum):
    TRANSACTION_ANALYSIS = "transaction_analysis"
    COMPLIANCE_DECISION = "compliance_decision"
    EXECUTIVE_SUMMARY = "executive_summary"
    AUDIT_REPORT = "audit_report"
    RISK_ASSESSMENT = "risk_assessment"


class ReportSection(BaseModel):
    """Individual section of a report"""

    title: str
    content: str
    severity: Optional[str] = None  # Low, Medium, High, Critical
    highlights: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ComplianceReport(BaseModel):
    """Comprehensive compliance report"""

    report_id: str
    report_type: ReportType
    transaction_id: str
    generated_at: datetime = Field(default_factory=datetime.now)
    generated_by: str = "Compliance System"

    # Report content
    executive_summary: str
    sections: List[ReportSection] = Field(default_factory=list)

    # Key findings
    key_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    risk_indicators: Dict[str, Any] = Field(default_factory=dict)

    # Decision information
    final_decision: Optional[str] = None
    approval_status: Optional[str] = None
    approver_name: Optional[str] = None
    approver_comments: Optional[str] = None

    # Actions and outcomes
    actions_taken: List[str] = Field(default_factory=list)
    notifications_sent: List[str] = Field(default_factory=list)

    # Regulatory compliance
    regulations_involved: List[str] = Field(default_factory=list)
    reporting_requirements: List[str] = Field(default_factory=list)

    # Metadata
    tags: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)


def send_llm(data: Any) -> str:
    """Send analysis to LLM for report generation" """
    system_prompt = f"""
    Format the following analysis into a structured report. 
    Use formal language suitable for regulatory review.

    {data}
    """
    # send to groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    groq_response = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=[{"role": "user", "content": system_prompt}],
    )
    groq_response = groq_response.choices[0].message.content

    # save in reports/ folder as text file
    report_folder = "reports/"
    os.makedirs(report_folder, exist_ok=True)
    report_path = os.path.join(report_folder, f"{data.report_id}.txt")
    with open(report_path, "w") as report_file:
        report_file.write(groq_response)

    return groq_response


class ReportGenerator:
    """
    Generates comprehensive compliance reports
    """

    def __init__(self):
        self.report_counter = 0

    def generate_transaction_analysis_report(
        self,
        transaction_id: str,
        anomaly_report: Any,
        department_results: Dict[str, Any],
    ) -> ComplianceReport:
        """Generate detailed transaction analysis report"""

        self.report_counter += 1
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d')}-{self.report_counter:04d}"

        # Executive Summary
        executive_summary = self._create_executive_summary(
            transaction_id, anomaly_report, department_results
        )

        # Create sections
        sections = []

        # Section 1: Transaction Overview
        sections.append(self._create_transaction_overview_section(anomaly_report))

        # Section 2: Risk Assessment
        sections.append(self._create_risk_assessment_section(anomaly_report))

        # Section 3: Department Analysis
        sections.append(self._create_department_analysis_section(department_results))

        # Section 4: Regulatory Compliance
        sections.append(
            self._create_regulatory_section(anomaly_report, department_results)
        )

        # Extract key issues
        key_issues = self._extract_key_issues(anomaly_report, department_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            anomaly_report, department_results
        )

        # Risk indicators
        risk_indicators = {
            "risk_score": anomaly_report.risk_score,
            "prior_alerts": anomaly_report.prior_alert_count_30d,
            "legal_risk": department_results.get("Legal", {}).get(
                "legal_risk_level", "Unknown"
            ),
            "escalation_required": department_results.get("FrontOffice", {}).get(
                "escalation_needed", False
            ),
        }

        # Regulations involved
        regulations = [anomaly_report.regulation]

        # Reporting requirements
        reporting_reqs = []
        compliance = department_results.get("Compliance", {})
        if isinstance(compliance, dict):
            req = compliance.get("required_reporting", "None")
            if req != "None":
                reporting_reqs.append(req)

        compliance_report = ComplianceReport(
            report_id=report_id,
            report_type=ReportType.TRANSACTION_ANALYSIS,
            transaction_id=transaction_id,
            executive_summary=executive_summary,
            sections=sections,
            key_issues=key_issues,
            recommendations=recommendations,
            risk_indicators=risk_indicators,
            regulations_involved=regulations,
            reporting_requirements=reporting_reqs,
            tags=[anomaly_report.product, anomaly_report.customer_segment or "Unknown"],
        )
        return compliance_report

    def generate_compliance_decision_report(
        self,
        transaction_id: str,
        anomaly_report: Any,
        department_results: Dict[str, Any],
        approval_response: Optional[Any],
        execution_plan: Any,
        execution_results: List[Any],
    ) -> ComplianceReport:
        """Generate compliance decision report including human approval and actions"""

        self.report_counter += 1
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d')}-{self.report_counter:04d}"

        # Executive Summary
        executive_summary = self._create_decision_executive_summary(
            transaction_id, anomaly_report, approval_response, execution_plan
        )

        # Create sections
        sections = []

        # Section 1: Decision Overview
        sections.append(
            self._create_decision_overview_section(
                anomaly_report, department_results, approval_response
            )
        )

        # Section 2: Human Approval Process
        if approval_response:
            sections.append(self._create_approval_section(approval_response))

        # Section 3: Action Execution
        sections.append(
            self._create_execution_section(execution_plan, execution_results)
        )

        # Section 4: Risk Mitigation
        sections.append(
            self._create_risk_mitigation_section(execution_plan, execution_results)
        )

        # Extract information
        key_issues = self._extract_decision_issues(approval_response, execution_results)

        compliance_result = department_results.get("Compliance", {})
        final_decision = compliance_result.get(
            "final_decision", anomaly_report.recommendation
        )

        actions_taken = [result.details for result in execution_results]
        notifications_sent = list(execution_plan.notification_recipients)

        # Generate recommendations
        recommendations = []
        if execution_plan and hasattr(execution_plan, "actions"):
            recommendations = [
                f"Execute: {action.value}" for action in execution_plan.actions
            ]
        if not recommendations:
            recommendations = ["Follow standard compliance procedures"]

        report = ComplianceReport(
            report_id=report_id,
            report_type=ReportType.COMPLIANCE_DECISION,
            transaction_id=transaction_id,
            executive_summary=executive_summary,
            sections=sections,
            key_issues=key_issues,
            recommendations=recommendations,
            final_decision=final_decision,
            actions_taken=actions_taken,
            notifications_sent=notifications_sent,
            regulations_involved=[anomaly_report.regulation],
            tags=["compliance_decision", anomaly_report.product],
        )

        if approval_response:
            report.approval_status = approval_response.status.value
            report.approver_name = approval_response.approver_name
            report.approver_comments = approval_response.comments

        return report

    def generate_executive_summary_report(
        self,
        transaction_id: str,
        anomaly_report: Any,
        department_results: Dict[str, Any],
        approval_response: Optional[Any],
        execution_results: List[Any],
    ) -> ComplianceReport:
        """Generate executive summary report for senior management"""

        self.report_counter += 1
        report_id = (
            f"RPT-EXEC-{datetime.now().strftime('%Y%m%d')}-{self.report_counter:04d}"
        )

        # Create concise executive summary
        exec_summary = f"""
EXECUTIVE SUMMARY - Transaction {transaction_id}

Risk Level: {'CRITICAL' if anomaly_report.risk_score >= 0.85 else 'HIGH' if anomaly_report.risk_score >= 0.75 else 'MEDIUM'}
Risk Score: {anomaly_report.risk_score:.2f}
Recommendation: {anomaly_report.recommendation}
{'Approval: ' + approval_response.status.value.upper() if approval_response else 'No approval required'}

Key Concern: {anomaly_report.regulation}
Actions Taken: {len(execution_results)} actions executed
Status: {'COMPLETED' if all(r.status == 'success' for r in execution_results) else 'PARTIAL'}
"""

        sections = [
            ReportSection(
                title="Overview",
                content=exec_summary.strip(),
                severity="Critical" if anomaly_report.risk_score >= 0.85 else "High",
            )
        ]

        # Generate recommendations for executive summary
        recommendations = []
        compliance_result = department_results.get("Compliance", {})
        if isinstance(compliance_result, dict):
            final_decision = compliance_result.get("final_decision", "")
            if final_decision:
                recommendations.append(f"{final_decision} transaction")

            required_reporting = compliance_result.get("required_reporting", "")
            if required_reporting and required_reporting != "None":
                recommendations.append(f"File {required_reporting} report")

        if execution_results:
            success_count = sum(1 for r in execution_results if r.status == "success")
            recommendations.append(
                f"Monitor execution: {success_count}/{len(execution_results)} actions completed"
            )

        if not recommendations:
            recommendations = ["Await further instructions"]

        compliance_report = ComplianceReport(
            report_id=report_id,
            report_type=ReportType.EXECUTIVE_SUMMARY,
            transaction_id=transaction_id,
            executive_summary=exec_summary.strip(),
            sections=sections,
            recommendations=recommendations,
            final_decision=department_results.get("Compliance", {}).get(
                "final_decision", "Pending"
            ),
            tags=["executive", "summary"],
        )
        return compliance_report

    # Helper methods for section creation

    def _create_executive_summary(
        self,
        transaction_id: str,
        anomaly_report: Any,
        department_results: Dict[str, Any],
    ) -> str:
        compliance = department_results.get("Compliance", {})
        final_decision = (
            compliance.get("final_decision", "Pending")
            if isinstance(compliance, dict)
            else "Pending"
        )

        return f"""
Transaction {transaction_id} flagged with risk score {anomaly_report.risk_score:.2f} for potential violation of {anomaly_report.regulation}.
Product: {anomaly_report.product} | Customer: {anomaly_report.customer_segment or 'Unknown'}
Evidence: {anomaly_report.evidence[:100]}...
Departmental coordination completed across FrontOffice, Legal, and Compliance.
Final Decision: {final_decision}
        """.strip()

    def _create_transaction_overview_section(
        self, anomaly_report: Any
    ) -> ReportSection:
        content = f"""
Transaction ID: {anomaly_report.transaction_id}
Product Type: {anomaly_report.product}
Customer Segment: {anomaly_report.customer_segment or 'Not specified'}
Initial Recommendation: {anomaly_report.recommendation}
Prior Alert Count (30 days): {anomaly_report.prior_alert_count_30d}

Evidence:
{anomaly_report.evidence}
        """.strip()

        return ReportSection(
            title="Transaction Overview",
            content=content,
            severity="High" if anomaly_report.risk_score >= 0.75 else "Medium",
            metrics={
                "risk_score": anomaly_report.risk_score,
                "prior_alerts": anomaly_report.prior_alert_count_30d,
            },
        )

    def _create_risk_assessment_section(self, anomaly_report: Any) -> ReportSection:
        risk_level = (
            "CRITICAL"
            if anomaly_report.risk_score >= 0.85
            else "HIGH" if anomaly_report.risk_score >= 0.75 else "MEDIUM"
        )

        content = f"""
Risk Score: {anomaly_report.risk_score:.2f} ({risk_level})
Regulation Involved: {anomaly_report.regulation}

Risk Factors:
- Transaction pattern analysis indicates suspicious activity
- Prior alert history: {anomaly_report.prior_alert_count_30d} alerts in past 30 days
- Regulatory compliance concern: {anomaly_report.regulation}
        """.strip()

        highlights = [
            f"Risk Score: {anomaly_report.risk_score:.2f}",
            f"Risk Level: {risk_level}",
            f"Prior Alerts: {anomaly_report.prior_alert_count_30d}",
        ]

        return ReportSection(
            title="Risk Assessment",
            content=content,
            severity=risk_level.capitalize(),
            highlights=highlights,
            metrics={"risk_score": anomaly_report.risk_score, "risk_level": risk_level},
        )

    def _create_department_analysis_section(
        self, department_results: Dict[str, Any]
    ) -> ReportSection:
        content_parts = []

        # FrontOffice
        front = department_results.get("FrontOffice", {})
        if isinstance(front, dict):
            content_parts.append(
                f"""
FRONT OFFICE ASSESSMENT:
Action Plan: {front.get('action_plan', 'N/A')}
Escalation Needed: {front.get('escalation_needed', False)}
Notes: {front.get('notes', 'None')}
            """.strip()
            )

        # Legal
        legal = department_results.get("Legal", {})
        if isinstance(legal, dict):
            content_parts.append(
                f"""
LEGAL ASSESSMENT:
Violation Assessment: {legal.get('violation_assessment', 'N/A')}
Legal Risk Level: {legal.get('legal_risk_level', 'Unknown')}
Required Disclosure: {legal.get('required_disclosure', 'None')}
Comments: {legal.get('comments', 'None')}
            """.strip()
            )

        # Compliance
        compliance = department_results.get("Compliance", {})
        if isinstance(compliance, dict):
            content_parts.append(
                f"""
COMPLIANCE ASSESSMENT:
Final Decision: {compliance.get('final_decision', 'Pending')}
Rationale: {compliance.get('rationale', 'N/A')}
Required Reporting: {compliance.get('required_reporting', 'None')}
Next Steps: {compliance.get('next_steps', 'N/A')}
            """.strip()
            )

        return ReportSection(
            title="Department Analysis",
            content="\n\n".join(content_parts),
            highlights=[
                f"Legal Risk: {legal.get('legal_risk_level', 'Unknown') if isinstance(legal, dict) else 'Unknown'}",
                f"Final Decision: {compliance.get('final_decision', 'Pending') if isinstance(compliance, dict) else 'Pending'}",
            ],
        )

    def _create_regulatory_section(
        self, anomaly_report: Any, department_results: Dict[str, Any]
    ) -> ReportSection:
        compliance = department_results.get("Compliance", {})
        reporting = (
            compliance.get("required_reporting", "None")
            if isinstance(compliance, dict)
            else "None"
        )
        legal = department_results.get("Legal", {})
        disclosure = (
            legal.get("required_disclosure", "None")
            if isinstance(legal, dict)
            else "None"
        )

        content = f"""
Regulation: {anomaly_report.regulation}
Required Reporting: {reporting}
Required Disclosure: {disclosure}

Compliance Status: {'COMPLIANT' if reporting != 'None' else 'PENDING REVIEW'}
        """.strip()

        return ReportSection(
            title="Regulatory Compliance",
            content=content,
            severity="High" if reporting != "None" else "Medium",
            highlights=[
                f"Regulation: {anomaly_report.regulation}",
                f"Reporting Required: {reporting}",
            ],
        )

    def _create_decision_executive_summary(
        self,
        transaction_id: str,
        anomaly_report: Any,
        approval_response: Optional[Any],
        execution_plan: Any,
    ) -> str:
        approval_text = (
            f"Approval: {approval_response.status.value.upper()} by {approval_response.approver_name}"
            if approval_response
            else "No approval required"
        )

        return f"""
Compliance decision for transaction {transaction_id} has been executed.
{approval_text}
Actions: {len(execution_plan.actions)} planned actions
Risk Score: {anomaly_report.risk_score:.2f}
Regulation: {anomaly_report.regulation}
        """.strip()

    def _create_decision_overview_section(
        self,
        anomaly_report: Any,
        department_results: Dict[str, Any],
        approval_response: Optional[Any],
    ) -> ReportSection:
        compliance = department_results.get("Compliance", {})
        final_decision = (
            compliance.get("final_decision", "Pending")
            if isinstance(compliance, dict)
            else "Pending"
        )

        content = f"""
Original Recommendation: {anomaly_report.recommendation}
Final Decision: {final_decision}
Approval Required: {'Yes' if approval_response else 'No'}
"""

        if approval_response:
            content += f"""
Approval Status: {approval_response.status.value.upper()}
Approver: {approval_response.approver_name} ({approval_response.approver_role})
Decision: {approval_response.decision or 'N/A'}
            """.strip()

        return ReportSection(
            title="Decision Overview",
            content=content.strip(),
            highlights=[
                f"Final Decision: {final_decision}",
                f"Approval: {approval_response.status.value if approval_response else 'Not Required'}",
            ],
        )

    def _create_approval_section(self, approval_response: Any) -> ReportSection:
        content = f"""
Approver: {approval_response.approver_name}
Role: {approval_response.approver_role}
Status: {approval_response.status.value.upper()}
Decision: {approval_response.decision or 'N/A'}
Comments: {approval_response.comments or 'None'}
Approved At: {approval_response.approved_at.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        severity_map = {
            "approved": "Medium",
            "rejected": "High",
            "escalated": "Critical",
        }

        return ReportSection(
            title="Human Approval Process",
            content=content,
            severity=severity_map.get(approval_response.status.value, "Medium"),
            highlights=[
                f"Status: {approval_response.status.value.upper()}",
                f"Approver: {approval_response.approver_name}",
            ],
        )

    def _create_execution_section(
        self, execution_plan: Any, execution_results: List[Any]
    ) -> ReportSection:
        content = f"""
Planned Actions: {len(execution_plan.actions)}
Executed Actions: {len(execution_results)}
Success Rate: {len([r for r in execution_results if r.status == 'success'])}/{len(execution_results)}

Execution Details:
"""
        for i, result in enumerate(execution_results, 1):
            status_icon = "✅" if result.status == "success" else "❌"
            content += f"\n{i}. {status_icon} {result.action.value}: {result.details}"

        if execution_plan.rollback_plan:
            content += f"\n\nExecution Notes:\n{execution_plan.rollback_plan}"

        return ReportSection(
            title="Action Execution",
            content=content.strip(),
            highlights=[
                f"{len(execution_results)} actions executed",
                f"Success: {len([r for r in execution_results if r.status == 'success'])}/{len(execution_results)}",
            ],
            metrics={
                "planned_actions": len(execution_plan.actions),
                "executed_actions": len(execution_results),
                "success_count": len(
                    [r for r in execution_results if r.status == "success"]
                ),
            },
        )

    def _create_risk_mitigation_section(
        self, execution_plan: Any, execution_results: List[Any]
    ) -> ReportSection:
        content = f"""
Notification Channels: {', '.join([ch.value for ch in execution_plan.notification_channels])}
Recipients Notified: {len(execution_plan.notification_recipients)}
Recipients: {', '.join(execution_plan.notification_recipients)}

Risk Mitigation Actions Completed:
"""
        for result in execution_results:
            if result.status == "success":
                content += f"\n✅ {result.action.value}"

        return ReportSection(
            title="Risk Mitigation",
            content=content.strip(),
            highlights=[
                f"{len(execution_plan.notification_recipients)} recipients notified",
                f"{len([r for r in execution_results if r.status == 'success'])} actions successful",
            ],
        )

    def _extract_key_issues(
        self, anomaly_report: Any, department_results: Dict[str, Any]
    ) -> List[str]:
        issues = []

        if anomaly_report.risk_score >= 0.85:
            issues.append(
                f"CRITICAL: Risk score {anomaly_report.risk_score:.2f} exceeds critical threshold"
            )
        elif anomaly_report.risk_score >= 0.75:
            issues.append(
                f"HIGH: Risk score {anomaly_report.risk_score:.2f} exceeds high threshold"
            )

        if anomaly_report.prior_alert_count_30d >= 3:
            issues.append(
                f"Multiple alerts: {anomaly_report.prior_alert_count_30d} alerts in past 30 days"
            )

        legal = department_results.get("Legal", {})
        if isinstance(legal, dict) and legal.get("legal_risk_level") == "High":
            issues.append("High legal risk identified")

        compliance = department_results.get("Compliance", {})
        if isinstance(compliance, dict) and "MAS" in compliance.get(
            "required_reporting", ""
        ):
            issues.append("MAS reporting required - regulatory submission needed")

        return issues

    def _generate_recommendations(
        self, anomaly_report: Any, department_results: Dict[str, Any]
    ) -> List[str]:
        recommendations = []

        compliance = department_results.get("Compliance", {})
        if isinstance(compliance, dict):
            final_decision = compliance.get("final_decision", "")
            if final_decision == "Block":
                recommendations.append(
                    "Immediate blocking of transaction/account recommended"
                )
                recommendations.append(
                    "File Suspicious Transaction Report (STR) within regulatory timeframe"
                )
            elif final_decision == "Monitor":
                recommendations.append("Enhanced monitoring for 30 days recommended")
                recommendations.append("Review customer transaction patterns weekly")

        if anomaly_report.prior_alert_count_30d >= 2:
            recommendations.append("Consider customer relationship review")

        legal = department_results.get("Legal", {})
        if isinstance(legal, dict):
            disclosure = legal.get("required_disclosure", "")
            if "MAS" in disclosure:
                recommendations.append("Notify MAS within required timeframe")
            if "Customer" in disclosure:
                recommendations.append(
                    "Prepare customer notification with legal review"
                )

        # Ensure recommendations is always a list
        if not recommendations:
            recommendations = ["Follow standard compliance procedures"]

        return recommendations

    def _extract_decision_issues(
        self, approval_response: Optional[Any], execution_results: List[Any]
    ) -> List[str]:
        issues = []

        if approval_response:
            if approval_response.status.value == "rejected":
                issues.append(
                    f"Management rejected recommendation: {approval_response.comments or 'No reason provided'}"
                )
            elif approval_response.status.value == "escalated":
                issues.append(
                    f"Case escalated to higher authority: {approval_response.comments or 'Pending executive decision'}"
                )
            elif (
                approval_response.decision
                and "modify" in approval_response.decision.lower()
            ):
                issues.append(
                    f"Recommendation modified by management: {approval_response.decision}"
                )

        failed_actions = [r for r in execution_results if r.status != "success"]
        if failed_actions:
            for result in failed_actions:
                issues.append(
                    f"Action failed: {result.action.value} - {result.error_message or 'Unknown error'}"
                )

        return issues

    def export_report_to_text(self, report: ComplianceReport) -> str:
        """Export report as formatted text"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"COMPLIANCE REPORT: {report.report_type.value.upper()}")
        lines.append("=" * 80)
        lines.append(f"Report ID: {report.report_id}")
        lines.append(f"Transaction ID: {report.transaction_id}")
        lines.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Generated By: {report.generated_by}")
        lines.append("=" * 80)
        lines.append("")

        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(report.executive_summary)
        lines.append("")

        for section in report.sections:
            lines.append(f"\n{section.title.upper()}")
            lines.append("-" * 80)
            if section.severity:
                lines.append(f"Severity: {section.severity}")
            lines.append(section.content)
            if section.highlights:
                lines.append("\nKey Highlights:")
                for highlight in section.highlights:
                    lines.append(f"  • {highlight}")
            lines.append("")

        if report.key_issues:
            lines.append("\nKEY ISSUES")
            lines.append("-" * 80)
            for issue in report.key_issues:
                lines.append(f"⚠️  {issue}")
            lines.append("")

        if report.recommendations:
            lines.append("\nRECOMMENDATIONS")
            lines.append("-" * 80)
            for rec in report.recommendations:
                lines.append(f"✅ {rec}")
            lines.append("")

        if report.final_decision:
            lines.append(f"\nFINAL DECISION: {report.final_decision}")

        if report.approval_status:
            lines.append(f"APPROVAL STATUS: {report.approval_status.upper()}")
            if report.approver_name:
                lines.append(f"Approved By: {report.approver_name}")

        lines.append("\n" + "=" * 80)
        lines.append(f"END OF REPORT - {report.report_id}")
        lines.append("=" * 80)

        return "\n".join(lines)

    def export_report_to_json(self, report: ComplianceReport) -> str:
        """Export report as JSON"""
        return report.model_dump_json(indent=2)

    def save_report(
        self,
        report: ComplianceReport,
        format: str = "text",
        output_dir: str = "./reports",
    ) -> str:
        """Save report to file"""
        import os

        os.makedirs(output_dir, exist_ok=True)

        filename = f"{report.report_id}_{report.transaction_id}.{format}"
        filepath = os.path.join(output_dir, filename)

        if format == "json":
            content = self.export_report_to_json(report)
        else:
            content = self.export_report_to_text(report)

        with open(filepath, "w") as f:
            f.write(content)

        return filepath
