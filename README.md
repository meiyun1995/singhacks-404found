# 🧠 Compliance Multi-Agent System with Human-in-the-Loop

### Intelligent Regulatory Routing for Banking Workflows with Dynamic Execution Branching

This project implements a **multi-agent compliance automation framework** with **dynamic human-in-the-loop (HITL) decision-making** using the [`openai-agents-python`](https://github.com/openai/openai-agents-python) SDK.

It models how compliance, legal, and front-office teams coordinate when an anomaly is detected in banking transactions — automatically routing alerts, generating department-specific assessments, and **adapting execution plans based on human management decisions**.

---

### 🎯 Dynamic Execution Branching

The system supports **four approval scenarios** with intelligent plan adaptation:

- **✅ APPROVED** - Execute standard actions as recommended
- **❌ REJECTED** - Downgrade to monitoring (override false positives)
- **🔺 ESCALATED** - Route to executive decision with protective measures
- **🔄 MODIFIED** - Automatically adjust plan based on modified decision

See **[QUICK_START.md](QUICK_START.md)** for complete details and examples.

---

## 🏗️ System Overview

| Layer                           | Description                                                                                                                                                          |
| :------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Regulation Miner**         | Crawls MAS/AMLA publications and extracts structured monitoring rules.                                                                                               |
| **2. Anomaly Detector**         | Ingests transactions, applies rules, generates a `Risk Score`, identifies violated regulation(s), and produces an `AnomalyReport`.                                   |
| **3. Compliance Coordinator**   | The controller agent in this repo — routes the anomaly report to the right departmental agents via LLM handoffs and aggregates all responses into one decision JSON. |
| **4. Human-in-the-Loop Engine** | **NEW**: Determines when human approval is needed, presents interactive CLI, and branches execution based on management decision.                                    |

Each department (Front Office, Legal, Compliance) is implemented as an **autonomous LLM agent** with its own specialized prompt and structured output schema.

---

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get started quickly with examples and validation
- **[BRANCHING_README.md](BRANCHING_README.md)** - Complete technical documentation
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Detailed code changes and architecture

---

## 🚀 Quick Start

### Run the Full Workflow

```bash
python workflow_router.py
```

### Test All Branching Scenarios

```bash
python simple_test.py
```

### Interactive Demo

```bash
python demo_full_workflow.py
```

### Validate Implementation

```bash
python validate_implementation.py
```

---

### Part 1: Real-Time AML Monitoring & Alerts ✅

**What it does**: Continuously monitors regulatory changes and client transactions to detect AML risks in real-time.

**Deliverables**:

- [ ] Working regulatory ingestion system
- [ ] Real-time transaction monitoring with configurable rules
- [ ] Alert system with role-based routing
- [ ] Remediation workflow engine with **dynamic branching**
- [ ] Comprehensive audit trail functionality
- [ ] **Human-in-the-Loop decision engine**
- [ ] **Interactive approval interface**
- [ ] **Dynamic execution plan adjustment**

### Part 2: Document & Image Corroboration

**What it does**: Automates the verification of client corroboration documents to detect inconsistencies and potential fraud.

**Deliverables**:

- [ ] Multi-format document processing system
- [ ] Advanced format validation with detailed error reporting
- [ ] Sophisticated image analysis capabilities
- [ ] Risk scoring and feedback system
- [ ] Comprehensive reporting functionality
