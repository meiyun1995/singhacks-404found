import pandas as pd
import asyncio, json, random
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

db = pd.read_csv("../data/transactions_mock_1000_for_participants.csv").fillna("").replace({"": None})
live_transactions = db[db.transaction_id == "ad66338d-b17f-47fc-a966-1b4395351b41"].to_dict(orient= "records")
live_transactions[0]["ai_risk_score"] = 0.9
live_transactions[0]["transaction_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
pending_transactions = db[~(db.transaction_id == "ad66338d-b17f-47fc-a966-1b4395351b41")].to_dict(orient="records")


@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "total_transactions": len(live_transactions),
            "action_required": sum(1 for t in live_transactions if t["ai_risk_score"] > 0.75),
            "transactions": live_transactions,
        },
    )

@app.get("/transaction/{transaction_id}", name="transaction_detail")
async def transaction_detail(request: Request, transaction_id: str):
    # TODO: replace with DB
    transaction = {
        "transaction_id": transaction_id,
        "transaction_amount": 15000.50,
        "transaction_currency": "USD",
        "transaction_channel": "Online",
        "transaction_product_type": "FX",
        "beneficiary_country": "SG",
        "customer_type": "Corporate",
        "customer_risk_rating": "High",
        "client_risk_profile": "Aggressive",
        "ai_risk_score": 0.82,
    }
    return templates.TemplateResponse(
        "transaction_detail.html",
        {"request": request, "transaction": transaction},
    )

@app.get("/stream/transactions")
async def stream_transactions():
    """SSE endpoint that streams a new transaction every 5s"""
    async def event_generator():
        while pending_transactions:
            txn = pending_transactions.pop(0)
            txn["ai_risk_score"] = round(random.random(), 2)
            txn["transaction_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            live_transactions.append(txn)
            yield f"data: {json.dumps(txn)}\n\n"
            await asyncio.sleep(5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")