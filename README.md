# Compliance Multi-Agent System with Human-in-the-Loop

This project implements a multi-agent compliance workflow with human-in-the-loop for final decision making.

## Setup Instructions

1. Navigate to the project root folder (i.e. singhacks-404found).
2. Create a Python 3.11 environment.
3. Install the dependencies in requirements.txt.

```bash
pip install -r requirements.txt
```
4. Create a .env file with the following credentials.

```
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=<your groq api key>
GROQ_API_KEY=<your groq api key>
GOOGLE_API_KEY=<your google api key>
GOOGLE_CX=<your google search engine id>
GOOGLE_SEARCH_ENDPOINT=https://www.googleapis.com/customsearch/v1
GOOGLE_APPLICATION_CREDENTIALS=<path to your google cloud credentials json>
```
5. Load transactions csv file into sqlite database.

```bash
python etl.py
```

6. Run regulatory ingestion engine

```bash
python regulatory_ingestion_engine.py
```

7. Run transaction analysis engine REST API. Navigate to http://localhost:8000/docs to access the SwaggerUI for the REST API.

```bash
fastapi run app.py --port 8000
```

8. Run document analysis engine.

```bash
python document_analysis/pipeline.py
```

9. Run integrated solution UI dashboard. Navigate to http://localhost:8100/dashboard to access the dashboard and http://localhost:8100/documents/analyze to access the document analysis engine.

```bash
cd ui
fastapi run app.py --port 8100
```

## System Workflow

The platform operates through two coordinated functions:

1. Real-Time AML Monitoring
Automatically triggered upon new transactions.
Analyzes behavioral and profile anomalies, assigns a risk score, and flags regulation breaches.
Uses LLM-driven routing for departmental triage and supports human-in-the-loop validation.
Aggregates insights into a unified decision JSON and visualizes historical cases on a dashboard.

2. Document Corroboration
Handles ad-hoc verification requests from Relationship Managers.
Processes uploaded PDFs, text, or image documents for consistency and authenticity.
Detects formatting or content inconsistencies and runs forensic image checks.
Returns real-time risk assessments and recommendations.

### Strategic Benefits

By combining these modules, banks can accelerate investigation workflows, reduce manual review effort, and strengthen trust with high-value clients. The system enhances regulatory compliance, ensures early fraud detection, and improves client experience through faster and more transparent risk validation.

## Tech Stack & Architecture

Core components include:
LLMs – Meta-Llama-3.3-70B-Versatile, Meta-Llama-4-Maverick-17B (Vision-Language)
Frameworks – openai-agents-python SDK for orchestration and reasoning
Modules – DeepSearch for document retrieval, reverse image search and deepfake detection for image integrity validation
