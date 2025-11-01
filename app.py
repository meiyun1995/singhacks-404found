from etl import Transaction
from pydantic import BaseModel

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException


class Request(BaseModel):
    transaction_id: str


app = FastAPI()
engine = create_engine(f"sqlite:///data/singhacks.db")
Session = sessionmaker(bind=engine)


@app.post("/transactions/analyze")
def get_transaction(request: Request):
    # TODO: add agent pipeline here
    with Session() as session:
        transaction = session.query(Transaction).filter_by(transaction_id = request.transaction_id).first()
        if not transaction:
            raise HTTPException(status_code = 404, detail = f"Transaction {request.transaction_id} does not exist.")
        return transaction.to_dict()