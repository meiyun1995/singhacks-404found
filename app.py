import os

from etl import Transaction
from pydantic import BaseModel
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException


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
engine = create_engine(f"sqlite:///data/singhacks.db")
Session = sessionmaker(bind=engine)


@app.post("/transactions/analyze")
def get_transaction(request: Request):
    # TODO: add agent pipeline here
    # TODO: specify model on agent level instead of project level
    with Session() as session:
        transaction = session.query(Transaction).filter_by(transaction_id = request.transaction_id).first()
        if not transaction:
            raise HTTPException(status_code = 404, detail = f"Transaction {request.transaction_id} does not exist.")
        return transaction.to_dict()