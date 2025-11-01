# Enhanced Compliance Workflow with Human-in-the-Loop

## Overview

This is an advanced multi-agent compliance workflow system for a Singapore bank that integrates **AI agents** with **Human-in-the-Loop (HITL)** capabilities to handle financial compliance cases with appropriate oversight and automated action execution.

## 🎯 Key Features

### 1. **Multi-Agent Coordination**

- **Coordinator Agent**: Routes cases to appropriate departments
- **Front Office Agent**: Handles operational responses and customer interactions
- **Legal Agent**: Assesses regulatory and legal risks
- **Compliance Agent**: Makes final regulatory decisions

### 2. **Human-in-the-Loop (HITL) Decision Engine**

Automatically determines when human approval is required based on:

- **Risk Score Thresholds**: Cases with risk ≥ 0.75 require approval
- **Action Type**: Blocking actions need human verification
- **Repeat Offenders**: Customers with ≥ 3 alerts in 30 days
- **Legal Risk**: High legal risk cases escalated to Legal Counsel
- **Regulatory Reporting**: MAS notifications require Head of Compliance approval
- **Conflicting Recommendations**: Department conflicts need human arbitration

### 3. **Automated Action Execution**

Supports various compliance actions:

- 🚫 **Block Card** - Immediate suspension
- 🔒 **Freeze Account** - Account level freeze
- 📞 **Contact Customer** - Automated notifications (SMS/Email)
- 📋 **File STR** - Suspicious Transaction Report submission
- 🏛️ **Notify MAS** - Regulatory authority notification
- ⬆️ **Escalate to Senior** - Management escalation
- 👀 **Monitor Only** - Enhanced surveillance
- ✅ **Allow Transaction** - Approval with monitoring

### 4. **Multi-Channel Notifications**

- Email notifications
- SMS alerts
- Slack/Teams integration (configurable)
- Dashboard updates

## 🏗️ Architecture

```
┌─────────────────┐
│ Anomaly Report  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Coordinator Agent      │  ◄── Routes to departments
│  (Multi-Agent Routing)  │
└────────┬────────────────┘
         │
         ├──► Front Office Agent ──► Operational Response
         ├──► Legal Agent       ──► Legal Assessment
         └──► Compliance Agent  ──► Final Decision
                │
                ▼
┌──────────────────────────────┐
│  HITL Decision Engine        │  ◄── Determines if human needed
│  (Rule-based Assessment)     │
└────────┬─────────────────────┘
         │
         ├──► Auto-Execute (Low Risk)
         │
         └──► Human Approval Required
                │
                ▼
         ┌──────────────────┐
         │  Human Approver  │  ◄── Compliance Officer/Manager
         └────────┬─────────┘
                  │
                  ▼
         ┌─────────────────────┐
         │  Action Executor    │  ◄── Executes approved actions
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Notifications      │  ◄── Multi-channel alerts
         └─────────────────────┘
```

## 🚀 Getting Started

### Prerequisites

1. **Python 3.11+**
2. **Conda environment** (recommended)

### Installation

```bash
# Create conda environment
conda create -n openai-agents python=3.11 -y
conda activate openai-agents

# Install dependencies
pip install openai-agents python-dotenv pydantic
```

### Configuration

Create a `.env` file:

```env
# Groq API Configuration (or use OpenAI)
OPENAI_API_KEY=your_groq_api_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile
```

### Running the Workflow

```bash
python workflow_router.py
```

## 📋 Workflow Steps

### Step 1: Anomaly Detection

The system receives an anomaly report with:

- Case ID
- Risk Score (0.0 - 1.0)
- Regulation reference (e.g., "MAS Notice 626 13.14(b)")
- Evidence
- Product type
- Customer segment
- Prior alert count

### Step 2: Multi-Agent Coordination

The Coordinator Agent:

1. Analyzes the anomaly report
2. Routes to appropriate department agents based on rules
3. Collects and aggregates department responses

**Routing Rules:**

- Risk Score ≥ 0.80 → Compliance + Legal
- MAS Notice 626 mentioned → Compliance + Front Office
- "Block" recommendation → Front Office
- Prior alerts ≥ 2 → Compliance

### Step 3: Human-in-the-Loop Decision

The HITL Decision Engine evaluates if human approval is needed:

| Condition     | Threshold | Approver Required  |
| ------------- | --------- | ------------------ |
| Risk Score    | ≥ 0.85    | Head of Compliance |
| Risk Score    | ≥ 0.75    | Compliance Officer |
| Block Action  | Any       | Compliance Officer |
| Prior Alerts  | ≥ 3       | Senior Manager     |
| Legal Risk    | High      | Legal Counsel      |
| MAS Reporting | Required  | Head of Compliance |

### Step 4: Action Execution

The Action Executor:

1. Creates an execution plan with prioritized actions
2. Executes actions in order
3. Sends multi-channel notifications
4. Logs all execution results

## 📊 Example Output

```
================================================================================
🏦 COMPLIANCE WORKFLOW WITH HUMAN-IN-THE-LOOP
================================================================================

📊 STEP 1: Anomaly Detection
   Case ID: C-2025-11-01-0001
   Risk Score: 0.86
   Recommendation: Block

🤖 STEP 2: Multi-Agent Coordination
   Running coordinator agent to route to departments...

🔍 STEP 3: Human-in-the-Loop Decision Check
   ⚠️  Human approval REQUIRED

   Reason: Risk score 0.86 exceeds critical threshold (0.85)
   Approver: Head of Compliance

   ✅ APPROVED by Sarah Chen (Senior Compliance Officer)

⚙️  STEP 4: Action Execution
   Actions: block_card, file_str, contact_customer, escalate_to_senior

   ✅ Card blocked in core banking system
   ✅ STR filed with reference: STR-C-2025-11-01-0001
   ✅ Customer notified via SMS and email
   ✅ Escalated to senior management

📊 WORKFLOW SUMMARY
   Status: ✅ COMPLETED
   Actions Executed: 4/4
================================================================================
```

## 🔧 Customization

### Adding New Actions

Edit `human_in_loop.py` and add to `ActionType` enum:

```python
class ActionType(str, Enum):
    YOUR_NEW_ACTION = "your_new_action"
```

Then implement in `ActionExecutor.execute_action()`:

```python
elif action == ActionType.YOUR_NEW_ACTION:
    result.details = "Your custom action executed"
```

### Modifying Approval Rules

Edit thresholds in `HumanInLoopDecisionEngine.__init__()`:

```python
self.approval_thresholds = {
    "risk_score": 0.75,  # Adjust threshold
    "prior_alerts": 3,   # Adjust count
}
```

### Adding Notification Channels

Add to `NotificationChannel` enum and implement in `ActionExecutor._send_notifications()`.

## 🔐 Production Considerations

### Security

- ✅ Store API keys in `.env` (never commit)
- ✅ Implement proper authentication for approval UI
- ✅ Encrypt sensitive data in logs
- ✅ Use role-based access control (RBAC)

### Integration

- 🔌 Connect to actual banking systems APIs
- 🔌 Integrate with real notification services (SendGrid, Twilio, etc.)
- 🔌 Connect to regulatory reporting portals
- 🔌 Implement approval workflow UI (web dashboard)

### Monitoring & Audit

- 📊 Log all decisions and actions
- 📊 Create audit trails for compliance
- 📊 Monitor approval turnaround times
- 📊 Track false positive rates

### Scalability

- 🚀 Use message queues (RabbitMQ, Kafka) for async processing
- 🚀 Implement caching for agent responses
- 🚀 Use database for state management
- 🚀 Deploy as microservices

## 📚 Files Structure

```
.
├── workflow_router.py          # Main workflow orchestration
├── human_in_loop.py           # HITL decision engine and action executor
├── .env                       # Configuration (API keys, model settings)
└── README.md                  # This file
```

## 🎓 Key Concepts

### Human-in-the-Loop (HITL)

A design pattern where AI automation is combined with human judgment for critical decisions. Ensures:

- **Accountability**: Humans approve high-risk actions
- **Compliance**: Regulatory requirements for human oversight
- **Safety**: Prevents automated errors in critical systems
- **Learning**: Human feedback improves AI over time

### Multi-Agent Systems

Multiple specialized AI agents work together:

- **Specialization**: Each agent focuses on domain expertise
- **Collaboration**: Agents share information
- **Robustness**: System continues if one agent fails
- **Scalability**: Easy to add new specialized agents

## 🤝 Contributing

This is a demonstration project. For production use:

1. Implement actual banking system integrations
2. Add comprehensive error handling
3. Create approval UI/dashboard
4. Implement proper logging and monitoring
5. Add unit and integration tests

## 📄 License

MIT License - See LICENSE file for details

## 🙋 Support

For questions or issues, please contact your compliance team lead or IT support.

---

**Built with ❤️ for Singapore Banking Compliance**
