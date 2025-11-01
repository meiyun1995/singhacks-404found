from fastapi import FastAPI
from etl import Transaction

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


app = FastAPI()
engine = create_engine(f"sqlite:///data/singhacks.db")
Session = sessionmaker(bind=engine)


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id):
    # TODO: add agent pipeline here
    with Session() as session:
        transaction = session.query(Transaction).filter_by(transaction_id=transaction_id).first()
        return transaction.to_dict() if transaction else None