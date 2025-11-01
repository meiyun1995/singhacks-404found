# 🧠 Compliance Multi-Agent System with Human-in-the-Loop

TODO: brief project description

This project implements a **multi-agent compliance automation framework** with **dynamic human-in-the-loop (HITL) decision-making** using the [`openai-agents-python`](https://github.com/openai/openai-agents-python) SDK.

It models how compliance, legal, and front-office teams coordinate when an anomaly is detected in banking transactions — automatically routing alerts, generating department-specific assessments, and **adapting execution plans based on human management decisions**.

### Instructions

TODO: 
1. Create python environment and install the requirements.txt.
2. Create .env file with the credentials for . Add JSON for google search.
3. Entrypoints for each modules and what each module does (table) + sequence of running.
- ui folder: UI ---> app.py
- app.py --> REST API to run analysis on transaction given transaction id, 
- etl.py --> load csv file into sqlite db
- document analysis --> ...
- regulatory_ingestion_engine --> digest mas rules

### Workflow

TODO: story which will overlap with the video, "script"

System overview
| Layer                           | Description                                                                                                                                                          |
| :------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Regulation Miner**         | Crawls MAS/AMLA publications and extracts structured monitoring rules.                                                                                               |
| **2. Anomaly Detector**         | Ingests transactions, applies rules, generates a `Risk Score`, identifies violated regulation(s), and produces an `AnomalyReport`.                                   |
| **3. Compliance Coordinator**   | The controller agent in this repo — routes the anomaly report to the right departmental agents via LLM handoffs and aggregates all responses into one decision JSON. |
| **4. Human-in-the-Loop Engine** | **NEW**: Determines when human approval is needed, presents interactive CLI, and branches execution based on management decision.                                    |

Each department (Front Office, Legal, Compliance) is implemented as an **autonomous LLM agent** with its own specialized prompt and structured output schema.
---