# 🧠 Compliance Multi-Agent System  
### Intelligent Regulatory Routing for Banking Workflows

This project implements a **multi-agent compliance automation framework** using the [`openai-agents-python`](https://github.com/openai/openai-agents-python) SDK.  
It models how compliance, legal, and front-office teams coordinate when an anomaly is detected in banking transactions — automatically routing alerts, generating department-specific assessments, and producing a consolidated compliance decision.

---

## 🏗️ System Overview

| Layer | Description |
|:------|:-------------|
| **1. Regulation Miner** | Crawls MAS/AMLA publications and extracts structured monitoring rules. |
| **2. Anomaly Detector** | Ingests transactions, applies rules, generates a `Risk Score`, identifies violated regulation(s), and produces an `AnomalyReport`. |
| **3. Compliance Coordinator** | The controller agent in this repo — routes the anomaly report to the right departmental agents via LLM handoffs and aggregates all responses into one decision JSON. |

Each department (Front Office, Legal, Compliance) is implemented as an **autonomous LLM agent** with its own specialized prompt and structured output schema.

---
### Part 1: Real-Time AML Monitoring & Alerts

**What it does**: Continuously monitors regulatory changes and client transactions to detect AML risks in real-time.

**Deliverables**:
- [ ] Working regulatory ingestion system
- [ ] Real-time transaction monitoring with configurable rules
- [ ] Alert system with role-based routing
- [ ] Remediation workflow engine
- [ ] Comprehensive audit trail functionality

### Part 2: Document & Image Corroboration

**What it does**: Automates the verification of client corroboration documents to detect inconsistencies and potential fraud.

**Deliverables**:
- [ ] Multi-format document processing system
- [ ] Advanced format validation with detailed error reporting
- [ ] Sophisticated image analysis capabilities
- [ ] Risk scoring and feedback system
- [ ] Comprehensive reporting functionality
