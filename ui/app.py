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

live_transactions = []
initial_txn = db[db.transaction_id == "ad66338d-b17f-47fc-a966-1b4395351b41"].to_dict(orient= "records")[0]
initial_txn["ai_risk_score"] = 0.65
initial_txn["transaction_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
live_transactions.append(initial_txn)
pending_transactions = db[~(db.transaction_id == "ad66338d-b17f-47fc-a966-1b4395351b41")].to_dict(orient="records")

with open("../reports/RPT-20251101-0001_ad66338d-b17f-47fc-a966-1b4395351b41.text", "r") as f:
    cached_report = f.read()

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "total_transactions": len(live_transactions),
            "action_required": sum(1 for t in live_transactions if t["ai_risk_score"] >= 0.65),
            "transactions": live_transactions,
        },
    )

@app.get("/transaction/{transaction_id}", name="transaction_detail")
async def transaction_detail(request: Request, transaction_id: str):
    return templates.TemplateResponse(
        "transaction_detail.html",
        {"request": request, "transaction": initial_txn, "transaction_report_text": cached_report},
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