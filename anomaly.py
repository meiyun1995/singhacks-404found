from typing import Literal, Optional
from pydantic import BaseModel, confloat, conint
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


class AnomalyReport(BaseModel):
    # Output of your Agent (2)
    transaction_id: str
    product: Literal['fx_conversion', 'wire_transfer', 'fund_subscription', 'securities_trade', 'cash_deposit', 'cash_withdrawal']
    risk_score: confloat(ge=0.0, le=1.0)
    regulation: str  # e.g., "MAS Notice 626 13.14(b)"
    evidence: str  # concise, salient points / excerpts
    recommendation: Literal["Block", "Monitor", "Allow", "Escalate"]
    customer_segment: Optional[str] = None
    prior_alert_count_30d: Optional[conint(ge=0)] = 0


ANOMALY_PROMPT = f"""{RECOMMENDED_PROMPT_PREFIX}
You are a Financial Crime Monitoring Agent for a regulated bank in Singapore. 
Analyze the following transaction in real-time for suspicious activity and potential money laundering. 

Tasks:
- Evaluate the transaction against the provided regulatory rules and flag any violations or threshold breaches.
- Detect unusual patterns in transaction volume, frequency, counterparties, or geographies.
- Detect potential layering, structuring, or other complex money laundering schemes.
- Assign a risk_score between 0.0 and 1.0 to the transaction.
- Provide concise justification in evidence, highlighting the most salient points.
- Based on the analysis, provide one recommendation from "Block", "Monitor", "Allow", "Escalate".

Return STRICT JSON:
{{
  "transaction_id": "",
  "product": "fx_conversion|wire_transfer|fund_subscription|securities_trade|cash_deposit|cash_withdrawal",
  "risk_score": 0.0,
  "regulation": "",
  "evidence": "",
  "recommendation": "Block|Monitor|Allow|Escalate",
  "customer_segment": "",
  "prior_alert_count_30": 0,
}}
"""

INPUT_PROMPT = """
Transaction:
{transaction}

Regulatory Rules:
{rules}
"""