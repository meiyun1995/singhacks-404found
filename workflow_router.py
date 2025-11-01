# compliance_router.py
import os
import json
from dotenv import load_dotenv
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, conint, confloat
from agents import Agent, Runner, handoff
from agents.extensions import handoff_filters
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# Import human-in-the-loop components
from human_in_loop import (
    HumanInLoopDecisionEngine,
    ActionExecutor,
    simulate_human_approval,
)
from interactive_approval import interactive_approval_cli

# Import report generation and audit trail
from report_generator import ReportGenerator, ReportType
from audit_trail import AuditLogger, AuditEventType, AuditSeverity

# Load environment variables from .env file
load_dotenv()

# Verify API key is loaded (optional but recommended for debugging)
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. Please check your .env file."
    )

# The openai-agents library will automatically use OPENAI_BASE_URL and OPENAI_MODEL from environment
print(f"Using API Base URL: {os.getenv('OPENAI_BASE_URL', 'default OpenAI')}")
print(f"Using Model: {os.getenv('OPENAI_MODEL', 'default')}")
print("---")

# ---------- Shared Schemas ----------


class Department(str):
    FRONT = "FrontOffice"
    LEGAL = "Legal"
    COMPLIANCE = "Compliance"


class AnomalyReport(BaseModel):
    # Output of your Agent (2)
    transaction_id: str
    product: Literal["CASA", "Cards", "Loans", "Trade", "Wealth", "Others"]
    risk_score: confloat(ge=0.0, le=1.0)
    regulation: str  # e.g., "MAS Notice 626 13.14(b)"
    evidence: str  # concise, salient points / excerpts
    recommendation: Literal["Block", "Monitor", "Allow", "Escalate"]
    customer_segment: Optional[str] = None
    prior_alert_count_30d: Optional[conint(ge=0)] = 0


# Optional: input payload that gets passed during handoff
class DeptHandoffInput(BaseModel):
    transaction_id: str
    risk_score: float
    regulation: str
    evidence: str
    recommendation: str
    product: str
    customer_segment: Optional[str] = None
    prior_alert_count_30d: Optional[int] = 0


# ---------- Department Agent Prompts ----------

FRONT_PROMPT = f"""{RECOMMENDED_PROMPT_PREFIX}
You are the Front Office Response Agent for a regulated bank in Singapore.

Context:
- You receive alerts from an Anomaly Detecting Agent.
- Your priority is operational feasibility, customer handling, and near-term actions that reduce risk without creating legal exposure.

Given:
- risk_score: {{risk_score}}
- regulation: {{regulation}}
- evidence: {{evidence}}
- recommendation: {{recommendation}}
- product: {{product}}
- customer_segment: {{customer_segment}}
- prior_alert_count_30d: {{prior_alert_count_30d}}

Instructions:
- Decide whether to contact the customer, freeze the transaction/account temporarily, or escalate.
- Draft precise customer-facing wording (if any).
- Flag operational preconditions and SLAs for actioning.

Return STRICT JSON:
{{
  "action_plan": "…",
  "customer_communication": "…",
  "escalation_needed": true/false,
  "notes": "…"
}}
"""

LEGAL_PROMPT = f"""{RECOMMENDED_PROMPT_PREFIX}
You are the Legal Review Agent for a Singapore bank. Stay aligned with MAS requirements, AMLA, and contractual obligations.

Given:
- regulation: {{regulation}}
- evidence: {{evidence}}
- recommendation: {{recommendation}}
- product: {{product}}
- risk_score: {{risk_score}}

Tasks:
1) Assess potential breach of MAS/AMLA/internal policy.
2) State whether the preliminary recommendation is legally defensible.
3) List documentation/disclosure requirements.

Return STRICT JSON:
{{
  "violation_assessment": "…",
  "required_disclosure": "MAS|Customer|Counterparty|None",
  "legal_risk_level": "Low|Medium|High",
  "comments": "…"
}}
"""

COMPLIANCE_PROMPT = f"""{RECOMMENDED_PROMPT_PREFIX}
You are the Compliance Assessment Agent. Final arbiter of regulatory disposition.

Inputs:
- risk_score: {{risk_score}}
- regulation: {{regulation}}
- evidence: {{evidence}}
- recommendation: {{recommendation}}
- product: {{product}}
- prior_alert_count_30d: {{prior_alert_count_30d}}
- customer_segment: {{customer_segment}}
- departmental_feedback: "{{departmental_feedback}}"  # aggregated text from Front/Legal if available

Decide:
- Final outcome: Block | Monitor | Allow
- Whether a Suspicious Transaction Report (STR) or other reporting is required.
- Next steps with owners and timelines.

Return STRICT JSON:
{{
  "final_decision": "Block|Monitor|Allow",
  "rationale": "…",
  "required_reporting": "MAS|Internal|None",
  "next_steps": "Owner(s), concrete actions, SLA"
}}
"""

# ---------- Define Department Agents ----------

front_agent = Agent(
    name="FrontOffice",
    instructions=FRONT_PROMPT,
    model="llama-3.3-70b-versatile",
)

legal_agent = Agent(
    name="Legal",
    instructions=LEGAL_PROMPT,
    model="llama-3.3-70b-versatile",
)

compliance_agent = Agent(
    name="Compliance",
    instructions=COMPLIANCE_PROMPT,
    model="llama-3.3-70b-versatile",
)

# ---------- Coordinator / Router Agent (Item 3) ----------

COORDINATOR_PROMPT = f"""{RECOMMENDED_PROMPT_PREFIX}
You are the Compliance Coordination Agent.

You receive an AnomalyReport and must:
1) Choose which department agents to involve (FrontOffice, Legal, Compliance).
2) Provide each chosen agent with a tailored, minimal input payload.
3) Aggregate departmental responses and produce a unified Compliance Decision Report.

Routing guidance (strict):
- If risk_score >= 0.80 → always include Compliance and Legal.
- If regulation mentions "MAS Notice 626" → include Compliance (and FrontOffice if customer contact is likely).
- If recommendation == "Block" → include FrontOffice (operational feasibility).
- If prior_alert_count_30d >= 2 → include Compliance.
- Otherwise: at minimum FrontOffice.

You can call handoff tools to those agents. Pass a JSON payload matching DeptHandoffInput.

After receiving department outputs, produce STRICT JSON:

{{
  "routed_agents": ["FrontOffice","Legal","Compliance"],
  "department_prompts_echo": {{
    "FrontOffice": "short synopsis of the prompt you constructed",
    "Legal": "…",
    "Compliance": "…"
  }},
  "department_results": {{
    "FrontOffice": <verbatim JSON from FrontOffice or null>,
    "Legal": <verbatim JSON from Legal or null>,
    "Compliance": <verbatim JSON from Compliance or null>
  }},
  "final_summary_for_human_review": "crisp executive summary with recommended decision path and any residual risks"
}}
"""


def _handoff_payload_filter(input_data):
    """
    Limit what the next agent sees: strip prior tool calls & keep only the latest user/system content.
    """
    return handoff_filters.remove_all_tools(input_data)


def _on_handoff_front(ctx, input_data):
    # simple passthrough — the SDK just needs a callable
    return input_data


def _on_handoff_legal(ctx, input_data):
    return input_data


def _on_handoff_compliance(ctx, input_data):
    return input_data


front_handoff = handoff(
    agent=front_agent,
    input_type=DeptHandoffInput,
    input_filter=_handoff_payload_filter,
    on_handoff=_on_handoff_front,
    tool_name_override="transfer_to_front_office",
    tool_description_override="Route case to Front Office for operational response.",
)

legal_handoff = handoff(
    agent=legal_agent,
    input_type=DeptHandoffInput,
    input_filter=_handoff_payload_filter,
    on_handoff=_on_handoff_legal,
    tool_name_override="transfer_to_legal",
    tool_description_override="Route case to Legal for legal risk and disclosure assessment.",
)

compliance_handoff = handoff(
    agent=compliance_agent,
    input_type=DeptHandoffInput,
    input_filter=_handoff_payload_filter,
    on_handoff=_on_handoff_compliance,
    tool_name_override="transfer_to_compliance",
    tool_description_override="Route case to Compliance for final regulatory disposition.",
)


coordinator = Agent(
    name="Coordinator",
    instructions=COORDINATOR_PROMPT,
    handoffs=[front_handoff, legal_handoff, compliance_handoff],
    model="llama-3.3-70b-versatile",
)

# ---------- Example run with Human-in-the-Loop ----------

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🏦 COMPLIANCE WORKFLOW WITH HUMAN-IN-THE-LOOP")
    print("=" * 80 + "\n")

    # Initialize audit logger and report generator
    audit_logger = AuditLogger()
    report_generator = ReportGenerator()

    # Example anomaly report from Agent (2)
    report = AnomalyReport(
        transaction_id="TXN-2025-11-01-0001",
        product="Cards",
        risk_score=0.86,
        regulation="MAS Notice 626 13.14(b)",
        evidence="Multiple high-value cross-border card-not-present transactions in <24h; device fingerprint mismatch; MCC 4829; IP geolocation flag.",
        recommendation="Block",
        customer_segment="Retail",
        prior_alert_count_30d=2,
    )

    # Start audit trail
    audit_logger.start_audit_trail(
        transaction_id=report.transaction_id,
        tags=["compliance", report.product, "high_risk"],
    )

    print("📊 STEP 1: Anomaly Detection")
    print(f"   Transaction ID: {report.transaction_id}")
    print(f"   Risk Score: {report.risk_score}")
    print(f"   Recommendation: {report.recommendation}")
    print(f"   Prior Alerts (30d): {report.prior_alert_count_30d}")

    # Log anomaly detection
    audit_logger.log_anomaly_detection(
        transaction_id=report.transaction_id,
        risk_score=report.risk_score,
        regulation=report.regulation,
        recommendation=report.recommendation,
        evidence=report.evidence,
    )

    # STEP 1: Run multi-agent coordination
    print("\n🤖 STEP 2: Multi-Agent Coordination")
    print("   Running coordinator agent to route to departments...")

    # Log agent routing start
    audit_logger.log_event(
        transaction_id=report.transaction_id,
        event_type=AuditEventType.AGENT_ROUTING,
        description="Starting multi-agent coordination",
        actor="System",
        component="Coordinator",
        tags=["routing", "start"],
    )

    result = Runner.run_sync(
        coordinator,
        f"ANOMALY REPORT JSON:\n{report.model_dump_json(indent=2)}\n"
        "Decide routing, call relevant department handoff tools with DeptHandoffInput, "
        "then aggregate departmental JSON outputs and produce final JSON.",
    )

    print("\n📋 Coordinator Output:")
    coordinator_output = result.final_output
    print(coordinator_output)

    # Parse the coordinator output
    try:
        if isinstance(coordinator_output, str):
            # Try to extract JSON from markdown code blocks if present
            if "```json" in coordinator_output:
                json_start = coordinator_output.find("```json") + 7
                json_end = coordinator_output.find("```", json_start)
                coordinator_data = json.loads(coordinator_output[json_start:json_end])
            elif "```" in coordinator_output:
                json_start = coordinator_output.find("```") + 3
                json_end = coordinator_output.find("```", json_start)
                coordinator_data = json.loads(coordinator_output[json_start:json_end])
            else:
                # Try to find JSON object in the string
                start = coordinator_output.find("{")
                end = coordinator_output.rfind("}") + 1
                coordinator_data = json.loads(coordinator_output[start:end])
        else:
            coordinator_data = coordinator_output
    except Exception as e:
        print(f"\n⚠️  Warning: Could not parse coordinator output as JSON: {e}")
        print("   Proceeding with mock data for demonstration...")

        # Log error
        audit_logger.log_error(
            transaction_id=report.transaction_id,
            error_message=f"Failed to parse coordinator output: {str(e)}",
            component="Coordinator",
            error_details={"output": str(coordinator_output)[:200]},
        )

        coordinator_data = {
            "routed_agents": ["FrontOffice", "Legal", "Compliance"],
            "department_results": {
                "FrontOffice": {
                    "action_plan": "Block card immediately",
                    "escalation_needed": True,
                },
                "Legal": {"legal_risk_level": "High", "required_disclosure": "MAS"},
                "Compliance": {"final_decision": "Block", "required_reporting": "MAS"},
            },
        }

    # Log department analysis results
    routed_agents = coordinator_data.get("routed_agents", [])
    audit_logger.log_agent_routing(
        transaction_id=report.transaction_id,
        routed_agents=routed_agents,
        routing_logic=f"Risk score {report.risk_score} and regulation {report.regulation}",
    )

    for dept, result in coordinator_data.get("department_results", {}).items():
        audit_logger.log_department_analysis(
            transaction_id=report.transaction_id,
            department=dept,
            analysis_result=(
                result if isinstance(result, dict) else {"result": str(result)}
            ),
        )

    # STEP 2: Check if human approval is needed
    print("\n🔍 STEP 3: Human-in-the-Loop Decision Check")

    hitl_engine = HumanInLoopDecisionEngine()
    department_results = coordinator_data.get("department_results", {})

    needs_approval, approval_request = hitl_engine.requires_human_approval(
        transaction_id=report.transaction_id,
        risk_score=report.risk_score,
        regulation=report.regulation,
        recommendation=report.recommendation,
        department_results=department_results,
        prior_alert_count=report.prior_alert_count_30d,
    )

    approval_response = None

    if needs_approval and approval_request:
        print("   ⚠️  Human approval REQUIRED")

        # Log approval request
        audit_logger.log_approval_request(
            transaction_id=report.transaction_id, approval_request=approval_request
        )

        # Simulate human approval (in production, this would be interactive)
        # approval_response = simulate_human_approval(approval_request)
        # Use interactive CLI instead of simulation
        approval_response = interactive_approval_cli(approval_request)

        # Log approval response
        audit_logger.log_approval_response(
            transaction_id=report.transaction_id, approval_response=approval_response
        )

        # Log if decision was modified
        if approval_response.decision and any(
            kw in approval_response.decision.lower() for kw in ["modify", "change"]
        ):
            audit_logger.log_decision_modification(
                transaction_id=report.transaction_id,
                original_decision=report.recommendation,
                modified_decision=approval_response.decision,
                modifier=approval_response.approver_name,
                reason=approval_response.comments or "Management decision",
            )

        # Log if escalated
        if approval_response.status.value == "escalated":
            audit_logger.log_escalation(
                transaction_id=report.transaction_id,
                escalated_to="Senior Management / Executive Committee",
                reason=approval_response.comments
                or "Requires higher authority approval",
                escalated_by=approval_response.approver_name,
            )

        print(f"\n   Decision: {approval_response.status.value.upper()}")
        print(
            f"   Approved by: {approval_response.approver_name} ({approval_response.approver_role})"
        )
        if approval_response.comments:
            print(f"   Comments: {approval_response.comments}")
    else:
        print("   ✅ No human approval needed - proceeding with automated execution")

    # STEP 3: Create and execute action plan
    print("\n⚙️  STEP 4: Action Execution")

    executor = ActionExecutor()

    # Get final decision from compliance result or approval
    compliance_result = department_results.get("Compliance", {})
    final_decision = compliance_result.get("final_decision", report.recommendation)

    # Create execution plan
    execution_plan = executor.create_execution_plan(
        transaction_id=report.transaction_id,
        final_decision=final_decision,
        department_results=department_results,
        approval_response=approval_response,
    )

    # Determine plan type for logging
    plan_type = "standard"
    if approval_response:
        if approval_response.status.value == "rejected":
            plan_type = "rejection"
        elif approval_response.status.value == "escalated":
            plan_type = "escalation"
        elif (
            approval_response.decision
            and "modify" in approval_response.decision.lower()
        ):
            plan_type = "modified"

    # Log execution plan creation
    audit_logger.log_execution_plan_created(
        transaction_id=report.transaction_id,
        execution_plan=execution_plan,
        plan_type=plan_type,
    )

    print(
        f"\n   Actions planned: {[action.value for action in execution_plan.actions]}"
    )

    # Execute the plan
    execution_results = executor.execute_plan(execution_plan)

    # Log each action execution
    for result in execution_results:
        audit_logger.log_action_execution(
            transaction_id=report.transaction_id, action_result=result
        )

    # Log notifications
    audit_logger.log_notification_sent(
        transaction_id=report.transaction_id,
        channels=[ch.value for ch in execution_plan.notification_channels],
        recipients=execution_plan.notification_recipients,
    )

    # STEP 4: Summary
    print("\n" + "=" * 80)
    print("📊 WORKFLOW SUMMARY")
    print("=" * 80)
    print(f"Transaction ID: {report.transaction_id}")
    print(f"Risk Score: {report.risk_score}")
    print(f"Agents Involved: {', '.join(coordinator_data.get('routed_agents', []))}")

    # Enhanced approval status reporting
    if needs_approval and approval_response:
        approval_status_icon = {
            "approved": "✅",
            "rejected": "❌",
            "escalated": "🔺",
            "pending": "⏳",
        }.get(approval_response.status.value, "❓")

        print(
            f"Human Approval: {approval_status_icon} {approval_response.status.value.upper()}"
        )
        print(
            f"  Approved by: {approval_response.approver_name} ({approval_response.approver_role})"
        )

        if approval_response.status == "rejected":
            print(f"  ⚠️  Original recommendation REJECTED by management")
        elif approval_response.status == "escalated":
            print(f"  🔺 Case ESCALATED to higher authority")
        elif (
            approval_response.decision
            and "modify" in approval_response.decision.lower()
        ):
            print(f"  🔄 Recommendation MODIFIED by management")

        if approval_response.comments:
            print(f"  Comments: {approval_response.comments}")
    else:
        print(f"Human Approval: Not Required")

    print(f"Final Decision: {final_decision}")

    # Show execution plan details if modified
    if execution_plan.rollback_plan:
        print(f"Execution Notes: {execution_plan.rollback_plan}")

    print(f"Actions Executed: {len(execution_results)}/{len(execution_plan.actions)}")
    print(
        f"Status: {'✅ COMPLETED' if all(r.status == 'success' for r in execution_results) else '⚠️  PARTIAL'}"
    )
    print("=" * 80 + "\n")

    # Print detailed execution results
    print("📝 Execution Details:")
    for i, result in enumerate(execution_results, 1):
        status_icon = "✅" if result.status == "success" else "❌"
        print(f"   {i}. {status_icon} {result.action.value}: {result.details}")

    # STEP 5: Generate Reports
    print("\n📄 STEP 5: Report Generation")

    # Generate transaction analysis report
    analysis_report = report_generator.generate_transaction_analysis_report(
        transaction_id=report.transaction_id,
        anomaly_report=report,
        department_results=department_results,
    )
    print(f"   ✅ Transaction Analysis Report: {analysis_report.report_id}")

    # Generate compliance decision report
    decision_report = report_generator.generate_compliance_decision_report(
        transaction_id=report.transaction_id,
        anomaly_report=report,
        department_results=department_results,
        approval_response=approval_response,
        execution_plan=execution_plan,
        execution_results=execution_results,
    )
    print(f"   ✅ Compliance Decision Report: {decision_report.report_id}")

    # Generate executive summary
    exec_report = report_generator.generate_executive_summary_report(
        transaction_id=report.transaction_id,
        anomaly_report=report,
        department_results=department_results,
        approval_response=approval_response,
        execution_results=execution_results,
    )
    print(f"   ✅ Executive Summary Report: {exec_report.report_id}")

    # Log report generation
    for rpt in [analysis_report, decision_report, exec_report]:
        audit_logger.log_report_generated(
            transaction_id=report.transaction_id,
            report_id=rpt.report_id,
            report_type=rpt.report_type.value,
        )

    # Save reports
    print("\n💾 Saving Reports...")
    analysis_path = report_generator.save_report(analysis_report, format="text")
    decision_path = report_generator.save_report(decision_report, format="text")
    exec_path = report_generator.save_report(exec_report, format="text")

    decision_json_path = report_generator.save_report(decision_report, format="json")

    print(f"   ✅ Reports saved to ./reports/")

    # Complete audit trail
    audit_logger.complete_audit_trail(report.transaction_id)

    # Save audit trail
    print("\n📋 STEP 6: Audit Trail")
    audit_path = audit_logger.save_audit_trail(report.transaction_id, format="text")
    audit_json_path = audit_logger.save_audit_trail(
        report.transaction_id, format="json"
    )
    print(f"   ✅ Audit trail saved: {audit_path}")

    # Print audit summary
    print("\n" + audit_logger.generate_audit_summary(report.transaction_id))

    print("\n✨ Workflow completed successfully!\n")

    # Print file paths summary
    print("\n" + "=" * 80)
    print("📁 GENERATED FILES")
    print("=" * 80)
    print(f"Reports:")
    print(f"  • Transaction Analysis: {analysis_path}")
    print(f"  • Compliance Decision: {decision_path}")
    print(f"  • Executive Summary: {exec_path}")
    print(f"  • Decision (JSON): {decision_json_path}")
    print(f"\nAudit Logs:")
    print(f"  • Audit Trail (Text): {audit_path}")
    print(f"  • Audit Trail (JSON): {audit_json_path}")
    print("=" * 80 + "\n")
