import os
import json

from groq import Groq
from pydantic import BaseModel
from dotenv import load_dotenv
from agents import Runner

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException

from etl import Transaction
from anomaly import INPUT_PROMPT, ANOMALY_PROMPT, AnomalyReport


load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. Please check your .env file."
    )

if not os.getenv("OPENAI_BASE_URL"):
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. Please check your .env file."
    )


class Request(BaseModel):
    transaction_id: str


app = FastAPI()
client = Groq()
engine = create_engine(f"sqlite:///data/singhacks.db")
Session = sessionmaker(bind=engine)

# TODO: load yuge output here

def run_analysis(transaction_id: str):
    with Session() as session:
        transaction = session.query(Transaction).filter_by(transaction_id = transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code = 404, detail = f"Transaction {transaction_id} does not exist.")
    
    transaction = transaction.to_dict()
    transaction["prior_alert_count_30d"] = 1 if transaction["str_filed_datetime"] is not None else 0

    # TODO: use yuge output
    rules = 'Financial institutions must do their due dilligence to monitor customer transactions.'
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=[
            {
                "role": "system",
                "content": ANOMALY_PROMPT
            },
            {
                "role": "user",
                "content": INPUT_PROMPT.format(transaction = transaction, rules = rules)
            }
        ],
        response_format={
            "type":"json_schema",
            "json_schema": {
                "name": "anomaly_report",
                "schema": AnomalyReport.model_json_schema()
            }
        }
    )
    return AnomalyReport(**json.loads(completion.choices[0].message.content))


@app.post("/transactions/analyze")
def analyze_transaction(request: Request):
    return run_analysis(request.transaction_id)