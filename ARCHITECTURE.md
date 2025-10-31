# System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     COMPLIANCE WORKFLOW SYSTEM                               │
│                    with Human-in-the-Loop (HITL)                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────┐
│ Anomaly Report    │  ◄─── From fraud detection system
│ - Case ID         │
│ - Risk Score      │
│ - Evidence        │
│ - Regulation      │
└─────────┬─────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        🤖 MULTI-AGENT COORDINATION                          │
│                                                                             │
│  ┌─────────────────┐                                                       │
│  │  Coordinator    │  ◄─── Analyzes case & routes to departments          │
│  │     Agent       │                                                       │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ├────────────────┬────────────────┬─────────────────┐           │
│           ▼                ▼                ▼                 ▼           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │           │
│  │Front Office │  │   Legal     │  │ Compliance  │          │           │
│  │   Agent     │  │   Agent     │  │   Agent     │          │           │
│  └─────────────┘  └─────────────┘  └─────────────┘          │           │
│         │                │                │                   │           │
│         │                │                │                   │           │
│         ▼                ▼                ▼                   │           │
│  Operational       Legal Risk       Final Decision           │           │
│  Feasibility      Assessment        & Reporting              │           │
│                                                               │           │
└───────────────────────────────────────────────────────────────┼───────────┘
                                                                │
                                                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    🧠 HITL DECISION ENGINE                                  │
│                                                                             │
│  Rules Engine:                                                             │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │ ✓ Risk Score ≥ 0.85         → Head of Compliance       │              │
│  │ ✓ Block Action              → Compliance Officer        │              │
│  │ ✓ Prior Alerts ≥ 3          → Senior Manager           │              │
│  │ ✓ High Legal Risk           → Legal Counsel            │              │
│  │ ✓ MAS Reporting Required    → Head of Compliance       │              │
│  │ ✓ Department Conflicts      → Senior Manager           │              │
│  └─────────────────────────────────────────────────────────┘              │
│                           │                                                 │
│                           ▼                                                 │
│            ┌──────────────────────────────┐                                │
│            │  Needs Human Approval?       │                                │
│            └──────────┬───────────┬───────┘                                │
│                       │           │                                         │
│                   YES │           │ NO                                      │
└───────────────────────┼───────────┼─────────────────────────────────────────┘
                        │           │
                        ▼           │
              ┌──────────────────┐  │
              │ 👤 HUMAN         │  │
              │   APPROVER       │  │
              │                  │  │
              │ Options:         │  │
              │ • Approve        │  │
              │ • Modify         │  │
              │ • Reject         │  │
              │ • Escalate       │  │
              └────────┬─────────┘  │
                       │            │
                       │            │
                       ▼            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ⚙️ ACTION EXECUTOR                                   │
│                                                                             │
│  Execution Plan:                                                           │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │ Priority 1:  🚫 Block Card / 🔒 Freeze Account         │              │
│  │ Priority 2:  📋 File STR / 🏛️ Notify MAS               │              │
│  │ Priority 3:  📞 Contact Customer                        │              │
│  │ Priority 4:  ⬆️ Escalate to Senior                     │              │
│  │ Priority 5:  👀 Monitor / ✅ Allow                     │              │
│  └─────────────────────────────────────────────────────────┘              │
│                           │                                                 │
│                           ▼                                                 │
│            ┌──────────────────────────────┐                                │
│            │  Execute Actions in Order    │                                │
│            └──────────────┬───────────────┘                                │
│                           │                                                 │
└───────────────────────────┼─────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    📧 NOTIFICATIONS & LOGGING                               │
│                                                                             │
│  Multi-Channel Notifications:         Audit Trail:                         │
│  ┌─────────────────────────┐         ┌──────────────────────┐             │
│  │ • Email                 │         │ • All decisions      │             │
│  │ • SMS                   │         │ • Action executions  │             │
│  │ • Slack/Teams           │         │ • Approver identity  │             │
│  │ • Dashboard             │         │ • Timestamps         │             │
│  └─────────────────────────┘         │ • Compliance reports │             │
│                                       └──────────────────────┘             │
│  Recipients:                                                               │
│  • Compliance Team                                                         │
│  • Fraud Team                                                              │
│  • Senior Management                                                       │
│  • Customer (for actions affecting them)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         ✅ OUTCOME                                          │
│                                                                             │
│  • Fast response to fraud/compliance issues                                │
│  • Appropriate human oversight for high-risk cases                         │
│  • Automated execution of approved actions                                 │
│  • Full audit trail for regulatory compliance                              │
│  • Reduced false positives through AI analysis                             │
│  • Scalable workflow for growing transaction volumes                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Example

```
INPUT:
{
  "case_id": "C-2025-11-01-0001",
  "risk_score": 0.86,
  "regulation": "MAS Notice 626 13.14(b)",
  "evidence": "Multiple high-value cross-border CNP transactions...",
  "recommendation": "Block"
}

↓ STEP 1: Multi-Agent Analysis

FrontOffice → {
  "action_plan": "Block card immediately",
  "escalation_needed": true
}

Legal → {
  "legal_risk_level": "High",
  "required_disclosure": "MAS"
}

Compliance → {
  "final_decision": "Block",
  "required_reporting": "MAS"
}

↓ STEP 2: HITL Check

Trigger: Risk score 0.86 ≥ 0.85 (Critical threshold)
Action: Request approval from Head of Compliance

↓ STEP 3: Human Approval

Approver: Sarah Chen (Senior Compliance Officer)
Decision: APPROVED
Comments: "High risk case with clear regulatory breach"

↓ STEP 4: Execution

Actions:
1. ✅ Block card → BLK-C-2025-11-01-0001
2. ✅ File STR → STR-C-2025-11-01-0001
3. ✅ Contact customer → TKT-C-2025-11-01-0001
4. ✅ Escalate → ESC-C-2025-11-01-0001

Notifications sent to:
- compliance@bank.com.sg
- fraud-team@bank.com.sg
- senior-manager@bank.com.sg

OUTPUT:
{
  "status": "COMPLETED",
  "actions_executed": 4,
  "human_approved": true,
  "approver": "Sarah Chen"
}
```
