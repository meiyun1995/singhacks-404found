import asyncio, json, random, uuid
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def dashboard(request: Request):
    # TODO: load actual dataframe in javascript side
    transactions = [
        {
            "transaction_id": "TX123",
            "transaction_amount": 15000.50,
            "transaction_currency": "USD",
            "transaction_channel": "Online",
            "transaction_product_type": "FX",
            "beneficiary_country": "SG",
            "customer_type": "Corporate",
            "customer_risk_rating": "High",
            "client_risk_profile": "Aggressive",
            "ai_risk_score": 0.82,
        },
        {
            "transaction_id": "TX124",
            "transaction_amount": 2300.00,
            "transaction_currency": "USD",
            "transaction_channel": "Branch",
            "transaction_product_type": "Deposit",
            "beneficiary_country": "HK",
            "customer_type": "Individual",
            "customer_risk_rating": "Low",
            "client_risk_profile": "Conservative",
            "ai_risk_score": 0.42,
        },
    ]
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "total_transactions": len(transactions),
            "action_required": sum(1 for t in transactions if t["ai_risk_score"] > 0.75),
            "transactions": transactions,
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

def generate_transaction():
    """Simulate generating a random transaction"""
    return {
        "transaction_id": str(uuid.uuid4())[:8].upper(),
        "transaction_amount": round(random.uniform(100, 20000), 2),
        "transaction_currency": random.choice(["USD", "SGD", "HKD", "JPY"]),
        "transaction_channel": random.choice(["Online", "Branch", "Mobile"]),
        "transaction_product_type": random.choice(["FX", "Deposit", "Transfer"]),
        "beneficiary_country": random.choice(["SG", "HK", "US", "JP"]),
        "customer_type": random.choice(["Corporate", "Individual"]),
        "customer_risk_rating": random.choice(["Low", "Medium", "High"]),
        "client_risk_profile": random.choice(["Conservative", "Balanced", "Aggressive"]),
        "ai_risk_score": round(random.random(), 2),
        "transaction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/stream/transactions")
async def stream_transactions():
    """SSE endpoint that streams a new transaction every 1s"""

    async def event_generator():
        while True:
            txn = generate_transaction()
            yield f"data: {json.dumps(txn)}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")