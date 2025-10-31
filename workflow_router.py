# compliance_router.py
import os
from dotenv import load_dotenv
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, conint, confloat
from agents import Agent, Runner, handoff
from agents.extensions import handoff_filters
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# Load environment variables from .env file
load_dotenv()

# Verify API key is loaded (optional but recommended for debugging)
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. Please check your .env file."
    )

# ---------- Shared Schemas ----------


class Department(str):
    FRONT = "FrontOffice"
    LEGAL = "Legal"
    COMPLIANCE = "Compliance"


class AnomalyReport(BaseModel):
    # Output of your Agent (2)
    case_id: str
    product: Literal["CASA", "Cards", "Loans", "Trade", "Wealth", "Others"]
    risk_score: confloat(ge=0.0, le=1.0)
    regulation: str  # e.g., "MAS Notice 626 13.14(b)"
    evidence: str  # concise, salient points / excerpts
    recommendation: Literal["Block", "Monitor", "Allow", "Escalate"]
    customer_segment: Optional[str] = None
    prior_alert_count_30d: Optional[conint(ge=0)] = 0


# Optional: input payload that gets passed during handoff
class DeptHandoffInput(BaseModel):
    case_id: str
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
)

legal_agent = Agent(
    name="Legal",
    instructions=LEGAL_PROMPT,
)

compliance_agent = Agent(
    name="Compliance",
    instructions=COMPLIANCE_PROMPT,
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
)

# ---------- Example run ----------

if __name__ == "__main__":
    # Example anomaly report from Agent (2)
    report = AnomalyReport(
        case_id="C-2025-10-31-0001",
        product="Cards",
        risk_score=0.86,
        regulation="MAS Notice 626 13.14(b)",
        evidence="Multiple high-value cross-border card-not-present transactions in <24h; device fingerprint mismatch; MCC 4829; IP geolocation flag.",
        recommendation="Block",
        customer_segment="Retail",
        prior_alert_count_30d=2,
    )

    # Coordinator will decide which handoffs to invoke and aggregate results
    # You can pass the entire object; the model will decide what to forward.
    result = Runner.run_sync(
        coordinator,
        f"ANOMALY REPORT JSON:\n{report.model_dump_json(indent=2)}\n"
        "Decide routing, call relevant department handoff tools with DeptHandoffInput, "
        "then aggregate departmental JSON outputs and produce final JSON.",
    )

    print(
        result.final_output
    )  # Unified JSON with routed_agents, department_results, final_summary
