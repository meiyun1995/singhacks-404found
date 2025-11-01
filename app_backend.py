#!/usr/bin/env python3
"""
Compliance Workflow Web Application Backend
FastAPI server for transaction processing and approval management
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import json
import uuid
from pathlib import Path

# Import our compliance workflow components
from human_in_loop import (
    HumanApprovalRequest,
    HumanApprovalResponse,
    ApprovalStatus,
    ActionType,
    HumanInLoopDecisionEngine,
    ActionExecutor,
)
from report_generator import ReportGenerator
from audit_trail import AuditLogger, AuditEventType

# Import workflow components
try:
    from workflow_router import AnomalyReport
except ImportError:
    # Fallback if agents library not available
    from pydantic import BaseModel
    from typing import Optional

    class AnomalyReport(BaseModel):
        transaction_id: str
        product: str
        risk_score: float
        regulation: str
        evidence: str
        recommendation: str
        customer_segment: Optional[str] = None
        prior_alert_count_30d: Optional[int] = 0


# Initialize FastAPI app
app = FastAPI(
    title="Compliance Workflow System",
    description="Real-time transaction compliance monitoring and approval system",
    version="1.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
report_gen = ReportGenerator()
audit_logger = AuditLogger()
hitl_engine = HumanInLoopDecisionEngine()

# In-memory storage (use database in production)
active_transactions: Dict[str, dict] = {}
pending_approvals: Dict[str, dict] = {}
completed_workflows: List[dict] = []

# WebSocket connections for real-time updates
active_websockets: List[WebSocket] = []


# ============================================================================
# API Models
# ============================================================================


class TransactionRequest(BaseModel):
    """Request to process a new transaction"""

    transaction_id: str
    product: str = "Cards"
    amount: Optional[float] = None
    customer_id: Optional[str] = None
    simulate_high_risk: bool = False


class ApprovalDecisionRequest(BaseModel):
    """Approval decision from user"""

    approval_id: str
    approver_name: str
    approver_role: str
    decision_type: str  # "approve", "approve_modified", "reject", "escalate"
    comments: Optional[str] = None
    modified_action: Optional[str] = None
    additional_actions: Optional[List[str]] = []


class TransactionStatusResponse(BaseModel):
    """Transaction processing status"""

    transaction_id: str
    status: (
        str  # "processing", "awaiting_approval", "approved", "rejected", "completed"
    )
    risk_score: Optional[float] = None
    recommendation: Optional[str] = None
    current_step: str
    approval_needed: bool
    approval_id: Optional[str] = None


# ============================================================================
# WebSocket Manager
# ============================================================================


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(
            f"✅ WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(
            f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()


# ============================================================================
# Helper Functions
# ============================================================================


def simulate_transaction_analysis(
    transaction_id: str, simulate_high_risk: bool = False
) -> dict:
    """Simulate the multi-agent analysis of a transaction"""

    # Simulate risk score
    import random

    if simulate_high_risk:
        risk_score = random.uniform(0.80, 0.95)
    else:
        risk_score = random.uniform(0.60, 0.85)

    # Determine recommendation based on risk
    if risk_score >= 0.85:
        recommendation = "Block"
    elif risk_score >= 0.75:
        recommendation = "Monitor"
    else:
        recommendation = "Allow"

    # Simulate department analysis
    department_results = {
        "FrontOffice": {
            "action_plan": (
                "Freeze card and contact customer"
                if risk_score >= 0.85
                else "Monitor transaction"
            ),
            "customer_communication": "We have detected unusual activity on your account",
            "escalation_needed": risk_score >= 0.85,
            "notes": "Customer has history of international travel",
        },
        "Legal": {
            "violation_assessment": (
                "Potential breach of MAS regulations"
                if risk_score >= 0.80
                else "Low legal risk"
            ),
            "legal_risk_level": (
                "High"
                if risk_score >= 0.85
                else "Medium" if risk_score >= 0.75 else "Low"
            ),
            "required_disclosure": "MAS" if risk_score >= 0.85 else "None",
            "comments": (
                "Recommend immediate reporting"
                if risk_score >= 0.85
                else "Standard monitoring"
            ),
        },
        "Compliance": {
            "final_decision": recommendation,
            "rationale": f"Risk score {risk_score:.2f} - {'exceeds critical threshold' if risk_score >= 0.85 else 'requires attention'}",
            "required_reporting": (
                "MAS - Suspicious Transaction Report"
                if risk_score >= 0.85
                else "Internal only"
            ),
            "next_steps": (
                "File STR within 15 days"
                if risk_score >= 0.85
                else "Continue monitoring"
            ),
        },
    }

    # Create anomaly report
    anomaly_report = AnomalyReport(
        transaction_id=transaction_id,
        product="Cards",
        risk_score=risk_score,
        regulation="MAS Notice 626 13.14(b)",
        evidence=f"Multiple high-value transactions detected. Device fingerprint mismatch. Risk score: {risk_score:.2f}",
        recommendation=recommendation,
        customer_segment="Retail",
        prior_alert_count_30d=int(risk_score * 5),  # 0-4 alerts
    )

    return {
        "anomaly_report": anomaly_report,
        "department_results": department_results,
        "risk_score": risk_score,
        "recommendation": recommendation,
    }


async def notify_clients(event_type: str, data: dict):
    """Send real-time notification to all connected clients"""
    message = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": data,
    }
    await manager.broadcast(message)


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Compliance Workflow API",
        "version": "1.0.0",
        "endpoints": {
            "frontend": "GET /app",
            "process_transaction": "POST /api/transactions/process",
            "get_status": "GET /api/transactions/{transaction_id}",
            "get_pending_approvals": "GET /api/approvals/pending",
            "submit_approval": "POST /api/approvals/respond",
            "websocket": "WS /ws",
            "docs": "GET /docs",
            "download_report": "GET /api/reports/download",
            "audit_logs": "GET /api/audit-logs",
            "transaction_logs": "GET /api/transactions/logs",
        },
    }


@app.get("/app", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend application"""
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        with open(frontend_path, "r") as f:
            return f.read()
    return HTMLResponse("<h1>Frontend not found</h1>", status_code=404)


@app.post("/api/transactions/process")
async def process_transaction(request: TransactionRequest):
    """
    Process a new transaction through the compliance workflow
    """
    transaction_id = request.transaction_id

    # Check if already processing (but allow reprocessing of completed ones)
    if transaction_id in active_transactions:
        txn_status = active_transactions[transaction_id].get("status")
        if txn_status in ["processing", "awaiting_approval"]:
            raise HTTPException(
                status_code=400, detail=f"Transaction already {txn_status}"
            )
        else:
            # Remove completed transaction to allow reprocessing
            del active_transactions[transaction_id]

    # Initialize transaction tracking
    active_transactions[transaction_id] = {
        "transaction_id": transaction_id,
        "status": "processing",
        "current_step": "Anomaly Detection",
        "started_at": datetime.now().isoformat(),
        "approval_needed": False,
    }

    # Notify clients
    await notify_clients(
        "transaction_started",
        {"transaction_id": transaction_id, "status": "processing"},
    )

    # Start audit trail
    audit_logger.start_audit_trail(transaction_id, tags=["web_app", "real_time"])

    # Step 1: Analyze transaction
    await asyncio.sleep(1)  # Simulate processing time
    analysis_result = simulate_transaction_analysis(
        transaction_id, request.simulate_high_risk
    )

    anomaly_report = analysis_result["anomaly_report"]
    department_results = analysis_result["department_results"]

    # Log anomaly detection
    audit_logger.log_anomaly_detection(
        transaction_id=transaction_id,
        risk_score=anomaly_report.risk_score,
        regulation=anomaly_report.regulation,
        recommendation=anomaly_report.recommendation,
        evidence=anomaly_report.evidence,
    )

    # Update status
    active_transactions[transaction_id].update(
        {
            "current_step": "HITL Decision Check",
            "risk_score": anomaly_report.risk_score,
            "recommendation": anomaly_report.recommendation,
            "analysis_result": analysis_result,
        }
    )

    await notify_clients(
        "analysis_complete",
        {
            "transaction_id": transaction_id,
            "risk_score": anomaly_report.risk_score,
            "recommendation": anomaly_report.recommendation,
        },
    )

    # Step 2: Check if human approval needed
    await asyncio.sleep(0.5)
    needs_approval, approval_request = hitl_engine.requires_human_approval(
        transaction_id=transaction_id,
        risk_score=anomaly_report.risk_score,
        regulation=anomaly_report.regulation,
        recommendation=anomaly_report.recommendation,
        department_results=department_results,
        prior_alert_count=anomaly_report.prior_alert_count_30d,
    )

    if needs_approval and approval_request:
        # Create approval request
        approval_id = str(uuid.uuid4())

        pending_approvals[approval_id] = {
            "approval_id": approval_id,
            "transaction_id": transaction_id,
            "request": approval_request.model_dump(mode="json"),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }

        active_transactions[transaction_id].update(
            {
                "status": "awaiting_approval",
                "current_step": "Human Approval Required",
                "approval_needed": True,
                "approval_id": approval_id,
            }
        )

        # Log approval request
        audit_logger.log_approval_request(transaction_id, approval_request)

        await notify_clients(
            "approval_required",
            {
                "transaction_id": transaction_id,
                "approval_id": approval_id,
                "risk_score": anomaly_report.risk_score,
                "urgency": approval_request.urgency,
            },
        )

        return {
            "transaction_id": transaction_id,
            "status": "awaiting_approval",
            "approval_id": approval_id,
            "approval_required": True,
            "risk_score": anomaly_report.risk_score,
        }
    else:
        # Auto-approve and complete
        active_transactions[transaction_id].update(
            {"status": "completed", "current_step": "Completed (Auto-approved)"}
        )

        await notify_clients(
            "transaction_completed",
            {"transaction_id": transaction_id, "status": "auto_approved"},
        )

        return {
            "transaction_id": transaction_id,
            "status": "completed",
            "approval_required": False,
            "auto_approved": True,
        }


@app.get("/api/transactions/{transaction_id}")
async def get_transaction_status(transaction_id: str):
    """Get current status of a transaction"""

    if transaction_id in active_transactions:
        return active_transactions[transaction_id]

    # Check completed workflows
    for workflow in completed_workflows:
        if workflow["transaction_id"] == transaction_id:
            return workflow

    raise HTTPException(status_code=404, detail="Transaction not found")


@app.get("/api/approvals/pending")
async def get_pending_approvals():
    """Get all pending approval requests"""

    pending = [
        {
            **approval,
            "transaction_data": active_transactions.get(approval["transaction_id"], {}),
        }
        for approval in pending_approvals.values()
        if approval["status"] == "pending"
    ]

    return {"count": len(pending), "approvals": pending}


@app.post("/api/approvals/respond")
async def submit_approval_decision(decision: ApprovalDecisionRequest):
    """Submit an approval decision"""

    approval_id = decision.approval_id

    if approval_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Approval request not found")

    approval = pending_approvals[approval_id]

    if approval["status"] != "pending":
        raise HTTPException(status_code=400, detail="Approval already processed")

    transaction_id = approval["transaction_id"]

    # Map decision type to approval status
    status_map = {
        "approve": ApprovalStatus.APPROVED,
        "approve_modified": ApprovalStatus.APPROVED,
        "reject": ApprovalStatus.REJECTED,
        "escalate": ApprovalStatus.ESCALATED,
    }

    status = status_map.get(decision.decision_type, ApprovalStatus.APPROVED)

    # Build decision text
    if decision.decision_type == "approve_modified" and decision.modified_action:
        decision_text = f"Approved with modification: {decision.modified_action}"
    elif decision.decision_type == "reject":
        decision_text = f"Rejected: {decision.comments or 'No alternative provided'}"
    elif decision.decision_type == "escalate":
        decision_text = "Escalated to senior management"
    else:
        decision_text = f"Approved: Proceed with recommended action"

    # Parse additional actions
    additional_actions = []
    if decision.additional_actions:
        action_map = {
            "contact_customer": ActionType.CONTACT_CUSTOMER,
            "escalate": ActionType.ESCALATE_TO_SENIOR,
            "monitor": ActionType.MONITOR_ONLY,
        }
        additional_actions = [
            action_map[a] for a in decision.additional_actions if a in action_map
        ]

    # Create approval response
    approval_response = HumanApprovalResponse(
        transaction_id=transaction_id,
        approver_name=decision.approver_name,
        approver_role=decision.approver_role,
        status=status,
        decision=decision_text,
        comments=decision.comments,
        additional_actions=additional_actions,  # Don't pass None, pass empty list
    )

    # Update approval status
    approval["status"] = status.value
    approval["response"] = approval_response.model_dump(mode="json")
    approval["responded_at"] = datetime.now().isoformat()

    # Log approval response
    audit_logger.log_approval_response(transaction_id, approval_response)

    # Update transaction status
    if transaction_id in active_transactions:
        active_transactions[transaction_id].update(
            {
                "status": (
                    "approved" if status == ApprovalStatus.APPROVED else status.value
                ),
                "current_step": (
                    "Action Execution"
                    if status == ApprovalStatus.APPROVED
                    else f"Workflow {status.value}"
                ),
                "approval_response": approval_response.model_dump(mode="json"),
            }
        )

        # Execute actions if approved
        if status == ApprovalStatus.APPROVED:
            executor = ActionExecutor()
            analysis_result = active_transactions[transaction_id].get(
                "analysis_result", {}
            )
            department_results = analysis_result.get("department_results", {})
            final_decision = analysis_result.get("recommendation", "Monitor")

            execution_plan = executor.create_execution_plan(
                transaction_id=transaction_id,
                final_decision=final_decision,
                department_results=department_results,
                approval_response=approval_response,
            )

            execution_results = executor.execute_plan(execution_plan)

            active_transactions[transaction_id].update(
                {
                    "status": "completed",
                    "current_step": "Completed",
                    "execution_results": [r.model_dump() for r in execution_results],
                }
            )

            # Move to completed
            completed_workflows.append(active_transactions[transaction_id])

            # Complete audit trail
            audit_logger.complete_audit_trail(transaction_id)

    # Notify clients
    await notify_clients(
        "approval_submitted",
        {
            "transaction_id": transaction_id,
            "approval_id": approval_id,
            "status": status.value,
            "approver": decision.approver_name,
        },
    )

    return {
        "success": True,
        "approval_id": approval_id,
        "transaction_id": transaction_id,
        "status": status.value,
    }


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    total_transactions = len(active_transactions) + len(completed_workflows)

    pending_approvals_count = sum(
        1 for a in pending_approvals.values() if a["status"] == "pending"
    )

    completed_count = len(completed_workflows) + sum(
        1 for txn in active_transactions.values() if txn.get("status") == "completed"
    )

    # Calculate average risk score
    all_risks = []
    for txn in list(active_transactions.values()) + completed_workflows:
        if "risk_score" in txn:
            all_risks.append(txn["risk_score"])

    avg_risk = sum(all_risks) / len(all_risks) if all_risks else 0

    return {
        "total_transactions": total_transactions,
        "pending_approvals": pending_approvals_count,
        "completed": completed_count,
        "processing": len(active_transactions) - pending_approvals_count,
        "average_risk_score": round(avg_risk, 2),
    }


@app.get("/api/transactions/{transaction_id}/logs")
async def get_transaction_logs(transaction_id: str):
    """Get detailed logs for a specific transaction"""

    # Get audit trail if exists
    audit_trail = audit_logger.get_audit_trail(transaction_id)

    if not audit_trail:
        raise HTTPException(status_code=404, detail="Transaction logs not found")

    # Format events for display
    events = []
    for event in audit_trail.events:
        events.append(
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "description": event.description,
                "actor": event.actor,
                "component": event.component,
                "severity": (
                    event.severity.value
                    if hasattr(event, "severity") and event.severity
                    else "INFO"
                ),
                "metadata": event.metadata,
            }
        )

    return {
        "transaction_id": transaction_id,
        "status": audit_trail.status,
        "started_at": audit_trail.start_time.isoformat(),
        "completed_at": (
            audit_trail.end_time.isoformat() if audit_trail.end_time else None
        ),
        "total_events": len(events),
        "events": events,
    }


@app.get("/api/transactions/{transaction_id}/report/download")
async def download_transaction_report(transaction_id: str, format: str = "text"):
    """Download compliance decision report for a transaction"""

    # Check if transaction exists
    if transaction_id not in active_transactions and transaction_id not in [
        w["transaction_id"] for w in completed_workflows
    ]:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Find report file
    reports_dir = Path("./reports")

    if format == "text":
        # Find text report
        report_files = list(reports_dir.glob(f"*_{transaction_id}.text"))
        if not report_files:
            raise HTTPException(status_code=404, detail="Text report not found")

        return FileResponse(
            path=report_files[0],
            filename=f"{transaction_id}_report.md",
            media_type="text/markdown",
        )
    elif format == "json":
        # Find JSON report
        report_files = list(reports_dir.glob(f"*_{transaction_id}.json"))
        if not report_files:
            raise HTTPException(status_code=404, detail="JSON report not found")

        return FileResponse(
            path=report_files[0],
            filename=f"{transaction_id}_report.json",
            media_type="application/json",
        )
    else:
        raise HTTPException(
            status_code=400, detail="Invalid format. Use 'text' or 'json'"
        )


@app.get("/api/transactions/{transaction_id}/audit/download")
async def download_audit_log(transaction_id: str, format: str = "text"):
    """Download audit trail for a transaction"""

    # Find audit trail file
    audit_dir = Path("./audit_logs")

    if format == "text":
        # Find text audit log
        audit_files = list(audit_dir.glob(f"AUDIT_{transaction_id}.text"))
        if not audit_files:
            raise HTTPException(status_code=404, detail="Text audit log not found")

        return FileResponse(
            path=audit_files[0],
            filename=f"{transaction_id}_audit.txt",
            media_type="text/plain",
        )
    elif format == "json":
        # Find JSON audit log
        audit_files = list(audit_dir.glob(f"AUDIT_{transaction_id}.json"))
        if not audit_files:
            raise HTTPException(status_code=404, detail="JSON audit log not found")

        return FileResponse(
            path=audit_files[0],
            filename=f"{transaction_id}_audit.json",
            media_type="application/json",
        )
    else:
        raise HTTPException(
            status_code=400, detail="Invalid format. Use 'text' or 'json'"
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_json({"type": "pong", "message": "Connection alive"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# Run the server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 80)
    print("🚀 COMPLIANCE WORKFLOW WEB APPLICATION")
    print("=" * 80)
    print("\n📡 Starting FastAPI server...")
    print("   • Backend API: http://localhost:8000")
    print("   • API Docs: http://localhost:8000/docs")
    print("   • WebSocket: ws://localhost:8000/ws")
    print("\n" + "=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
