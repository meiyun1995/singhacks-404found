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

    print("📊 STEP 1: Anomaly Detection")
    print(f"   Transaction ID: {report.transaction_id}")
    print(f"   Risk Score: {report.risk_score}")
    print(f"   Recommendation: {report.recommendation}")
    print(f"   Prior Alerts (30d): {report.prior_alert_count_30d}")

    # STEP 1: Run multi-agent coordination
    print("\n🤖 STEP 2: Multi-Agent Coordination")
    print("   Running coordinator agent to route to departments...")

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

        # Simulate human approval (in production, this would be interactive)
        approval_response = simulate_human_approval(approval_request)

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

    print(
        f"\n   Actions planned: {[action.value for action in execution_plan.actions]}"
    )

    # Execute the plan
    execution_results = executor.execute_plan(execution_plan)

    # STEP 4: Summary
    print("\n" + "=" * 80)
    print("📊 WORKFLOW SUMMARY")
    print("=" * 80)
    print(f"Transaction ID: {report.transaction_id}")
    print(f"Risk Score: {report.risk_score}")
    print(f"Agents Involved: {', '.join(coordinator_data.get('routed_agents', []))}")
    print(
        f"Human Approval: {'Required and Obtained' if needs_approval else 'Not Required'}"
    )
    print(f"Final Decision: {final_decision}")
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

    print("\n✨ Workflow completed successfully!\n")
