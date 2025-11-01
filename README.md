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
