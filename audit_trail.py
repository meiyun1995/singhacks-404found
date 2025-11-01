# audit_trail.py
"""
Audit Trail Module
Maintains comprehensive logs of all analysis, decisions, and actions performed
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import json
import os


class AuditEventType(str, Enum):
    ANOMALY_DETECTED = "anomaly_detected"
    AGENT_ROUTING = "agent_routing"
    DEPARTMENT_ANALYSIS = "department_analysis"
    HITL_TRIGGERED = "hitl_triggered"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RECEIVED = "approval_received"
    EXECUTION_PLAN_CREATED = "execution_plan_created"
    ACTION_EXECUTED = "action_executed"
    NOTIFICATION_SENT = "notification_sent"
    REPORT_GENERATED = "report_generated"
    ERROR_OCCURRED = "error_occurred"
    DECISION_MODIFIED = "decision_modified"
    ESCALATION_CREATED = "escalation_created"


class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Individual audit event"""

    event_id: str
    transaction_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.INFO

    # Event details
    description: str
    actor: str  # System, Agent, User name
    component: str  # Which component triggered this event

    # Data
    event_data: Dict[str, Any] = Field(default_factory=dict)
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None

    # Context
    risk_score: Optional[float] = None
    decision: Optional[str] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    related_events: List[str] = Field(default_factory=list)


class AuditTrail(BaseModel):
    """Complete audit trail for a transaction"""

    transaction_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    events: List[AuditEvent] = Field(default_factory=list)

    # Summary statistics
    total_events: int = 0
    critical_events: int = 0
    warnings: int = 0
    errors: int = 0

    # Key milestones
    anomaly_detected_at: Optional[datetime] = None
    approval_requested_at: Optional[datetime] = None
    approval_received_at: Optional[datetime] = None
    execution_completed_at: Optional[datetime] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)


class AuditLogger:
    """
    Centralized audit logging system
    """

    def __init__(self, storage_dir: str = "./audit_logs"):
        self.storage_dir = storage_dir
        self.event_counter = 0
        self.active_trails: Dict[str, AuditTrail] = {}
        os.makedirs(storage_dir, exist_ok=True)

    def start_audit_trail(
        self, transaction_id: str, tags: List[str] = None
    ) -> AuditTrail:
        """Start a new audit trail for a transaction"""
        trail = AuditTrail(transaction_id=transaction_id, tags=tags or [])
        self.active_trails[transaction_id] = trail
        return trail

    def log_event(
        self,
        transaction_id: str,
        event_type: AuditEventType,
        description: str,
        actor: str = "System",
        component: str = "Unknown",
        severity: AuditSeverity = AuditSeverity.INFO,
        event_data: Dict[str, Any] = None,
        previous_state: Dict[str, Any] = None,
        new_state: Dict[str, Any] = None,
        risk_score: float = None,
        decision: str = None,
        tags: List[str] = None,
    ) -> AuditEvent:
        """Log an audit event"""

        self.event_counter += 1
        event_id = (
            f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.event_counter:05d}"
        )

        event = AuditEvent(
            event_id=event_id,
            transaction_id=transaction_id,
            event_type=event_type,
            severity=severity,
            description=description,
            actor=actor,
            component=component,
            event_data=event_data or {},
            previous_state=previous_state,
            new_state=new_state,
            risk_score=risk_score,
            decision=decision,
            tags=tags or [],
        )

        # Add to active trail if exists
        if transaction_id in self.active_trails:
            trail = self.active_trails[transaction_id]
            trail.events.append(event)
            trail.total_events += 1

            # Update statistics
            if severity == AuditSeverity.CRITICAL:
                trail.critical_events += 1
            elif severity == AuditSeverity.WARNING:
                trail.warnings += 1
            elif severity == AuditSeverity.ERROR:
                trail.errors += 1

            # Update milestones
            if event_type == AuditEventType.ANOMALY_DETECTED:
                trail.anomaly_detected_at = event.timestamp
            elif event_type == AuditEventType.APPROVAL_REQUESTED:
                trail.approval_requested_at = event.timestamp
            elif event_type == AuditEventType.APPROVAL_RECEIVED:
                trail.approval_received_at = event.timestamp

        return event

    def log_anomaly_detection(
        self,
        transaction_id: str,
        risk_score: float,
        regulation: str,
        recommendation: str,
        evidence: str,
    ) -> AuditEvent:
        """Log anomaly detection event"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.ANOMALY_DETECTED,
            description=f"Anomaly detected with risk score {risk_score:.2f}",
            actor="Anomaly Detection Agent",
            component="AnomalyDetector",
            severity=(
                AuditSeverity.CRITICAL if risk_score >= 0.85 else AuditSeverity.WARNING
            ),
            event_data={
                "risk_score": risk_score,
                "regulation": regulation,
                "recommendation": recommendation,
                "evidence": evidence,
            },
            risk_score=risk_score,
            decision=recommendation,
            tags=["anomaly", "detection"],
        )

    def log_agent_routing(
        self,
        transaction_id: str,
        routed_agents: List[str],
        routing_logic: str,
    ) -> AuditEvent:
        """Log multi-agent routing"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.AGENT_ROUTING,
            description=f"Transaction routed to {len(routed_agents)} department agents",
            actor="Coordinator Agent",
            component="AgentRouter",
            event_data={
                "routed_agents": routed_agents,
                "routing_logic": routing_logic,
            },
            tags=["routing", "multi-agent"],
        )

    def log_department_analysis(
        self,
        transaction_id: str,
        department: str,
        analysis_result: Dict[str, Any],
    ) -> AuditEvent:
        """Log department analysis results"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.DEPARTMENT_ANALYSIS,
            description=f"{department} department completed analysis",
            actor=f"{department} Agent",
            component=department,
            event_data={"analysis_result": analysis_result},
            tags=["analysis", department.lower()],
        )

    def log_hitl_trigger(
        self,
        transaction_id: str,
        reason: str,
        urgency: str,
        approver_role: str,
    ) -> AuditEvent:
        """Log HITL trigger"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.HITL_TRIGGERED,
            description=f"Human approval required: {reason}",
            actor="HITL Decision Engine",
            component="HumanInLoopEngine",
            severity=AuditSeverity.WARNING,
            event_data={
                "reason": reason,
                "urgency": urgency,
                "approver_role": approver_role,
            },
            tags=["hitl", "approval_required"],
        )

    def log_approval_request(
        self,
        transaction_id: str,
        approval_request: Any,
    ) -> AuditEvent:
        """Log approval request sent"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.APPROVAL_REQUESTED,
            description=f"Approval request sent to {approval_request.approver_role}",
            actor="HITL System",
            component="ApprovalInterface",
            event_data={
                "urgency": approval_request.urgency,
                "approver_role": approval_request.approver_role,
                "reason": approval_request.requires_approval_reason,
            },
            risk_score=approval_request.risk_score,
            tags=["approval", "request"],
        )

    def log_approval_response(
        self,
        transaction_id: str,
        approval_response: Any,
    ) -> AuditEvent:
        """Log approval response received"""
        severity = AuditSeverity.INFO
        if approval_response.status.value == "rejected":
            severity = AuditSeverity.WARNING
        elif approval_response.status.value == "escalated":
            severity = AuditSeverity.CRITICAL

        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.APPROVAL_RECEIVED,
            description=f"Approval {approval_response.status.value} by {approval_response.approver_name}",
            actor=approval_response.approver_name,
            component="ApprovalInterface",
            severity=severity,
            event_data={
                "status": approval_response.status.value,
                "approver_name": approval_response.approver_name,
                "approver_role": approval_response.approver_role,
                "decision": approval_response.decision,
                "comments": approval_response.comments,
            },
            decision=approval_response.decision,
            tags=["approval", "response", approval_response.status.value],
        )

    def log_execution_plan_created(
        self,
        transaction_id: str,
        execution_plan: Any,
        plan_type: str = "standard",
    ) -> AuditEvent:
        """Log execution plan creation"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.EXECUTION_PLAN_CREATED,
            description=f"Execution plan created ({plan_type}): {len(execution_plan.actions)} actions",
            actor="Action Executor",
            component="ExecutionPlanner",
            event_data={
                "plan_type": plan_type,
                "actions": [a.value for a in execution_plan.actions],
                "notification_channels": [
                    c.value for c in execution_plan.notification_channels
                ],
                "recipients": execution_plan.notification_recipients,
                "rollback_plan": execution_plan.rollback_plan,
            },
            tags=["execution", "planning", plan_type],
        )

    def log_action_execution(
        self,
        transaction_id: str,
        action_result: Any,
    ) -> AuditEvent:
        """Log action execution"""
        severity = (
            AuditSeverity.INFO
            if action_result.status == "success"
            else AuditSeverity.ERROR
        )

        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.ACTION_EXECUTED,
            description=f"Action {action_result.action.value}: {action_result.status}",
            actor="Action Executor",
            component="ActionExecutor",
            severity=severity,
            event_data={
                "action": action_result.action.value,
                "status": action_result.status,
                "details": action_result.details,
                "error_message": action_result.error_message,
            },
            tags=["execution", "action", action_result.action.value],
        )

    def log_notification_sent(
        self,
        transaction_id: str,
        channels: List[str],
        recipients: List[str],
    ) -> AuditEvent:
        """Log notification sent"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.NOTIFICATION_SENT,
            description=f"Notifications sent via {len(channels)} channels to {len(recipients)} recipients",
            actor="Notification System",
            component="NotificationHandler",
            event_data={
                "channels": channels,
                "recipients": recipients,
            },
            tags=["notification"],
        )

    def log_report_generated(
        self,
        transaction_id: str,
        report_id: str,
        report_type: str,
    ) -> AuditEvent:
        """Log report generation"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.REPORT_GENERATED,
            description=f"Report generated: {report_id} ({report_type})",
            actor="Report Generator",
            component="ReportGenerator",
            event_data={
                "report_id": report_id,
                "report_type": report_type,
            },
            tags=["report", report_type],
        )

    def log_error(
        self,
        transaction_id: str,
        error_message: str,
        component: str,
        error_details: Dict[str, Any] = None,
    ) -> AuditEvent:
        """Log error"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.ERROR_OCCURRED,
            description=f"Error in {component}: {error_message}",
            actor="System",
            component=component,
            severity=AuditSeverity.ERROR,
            event_data=error_details or {"error": error_message},
            tags=["error"],
        )

    def log_decision_modification(
        self,
        transaction_id: str,
        original_decision: str,
        modified_decision: str,
        modifier: str,
        reason: str,
    ) -> AuditEvent:
        """Log decision modification"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.DECISION_MODIFIED,
            description=f"Decision modified from '{original_decision}' to '{modified_decision}'",
            actor=modifier,
            component="DecisionModifier",
            severity=AuditSeverity.WARNING,
            event_data={
                "original_decision": original_decision,
                "modified_decision": modified_decision,
                "reason": reason,
            },
            previous_state={"decision": original_decision},
            new_state={"decision": modified_decision},
            decision=modified_decision,
            tags=["modification", "decision_change"],
        )

    def log_escalation(
        self,
        transaction_id: str,
        escalated_to: str,
        reason: str,
        escalated_by: str,
    ) -> AuditEvent:
        """Log escalation"""
        return self.log_event(
            transaction_id=transaction_id,
            event_type=AuditEventType.ESCALATION_CREATED,
            description=f"Case escalated to {escalated_to}",
            actor=escalated_by,
            component="EscalationHandler",
            severity=AuditSeverity.CRITICAL,
            event_data={
                "escalated_to": escalated_to,
                "reason": reason,
            },
            tags=["escalation", "critical"],
        )

    def complete_audit_trail(self, transaction_id: str) -> AuditTrail:
        """Mark audit trail as complete"""
        if transaction_id in self.active_trails:
            trail = self.active_trails[transaction_id]
            trail.completed_at = datetime.now()
            trail.execution_completed_at = datetime.now()
            return trail
        return None

    def get_audit_trail(self, transaction_id: str) -> Optional[AuditTrail]:
        """Get audit trail for a transaction"""
        return self.active_trails.get(transaction_id)

    def save_audit_trail(self, transaction_id: str, format: str = "json") -> str:
        """Save audit trail to file"""
        trail = self.active_trails.get(transaction_id)
        if not trail:
            return None

        filename = (
            f"audit_{transaction_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{format}"
        )
        filepath = os.path.join(self.storage_dir, filename)

        if format == "json":
            content = trail.model_dump_json(indent=2)
        else:
            content = self.export_trail_to_text(trail)

        with open(filepath, "w") as f:
            f.write(content)

        return filepath

    def export_trail_to_text(self, trail: AuditTrail) -> str:
        """Export audit trail as formatted text"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"AUDIT TRAIL: {trail.transaction_id}")
        lines.append("=" * 80)
        lines.append(f"Started: {trail.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if trail.completed_at:
            lines.append(
                f"Completed: {trail.completed_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            duration = (trail.completed_at - trail.started_at).total_seconds()
            lines.append(f"Duration: {duration:.2f} seconds")
        lines.append("")
        lines.append(f"Total Events: {trail.total_events}")
        lines.append(f"Critical Events: {trail.critical_events}")
        lines.append(f"Warnings: {trail.warnings}")
        lines.append(f"Errors: {trail.errors}")
        lines.append("=" * 80)
        lines.append("")

        lines.append("EVENT LOG")
        lines.append("-" * 80)

        for i, event in enumerate(trail.events, 1):
            severity_icon = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "critical": "🔴",
            }.get(event.severity.value, "•")

            lines.append(f"\n[{i}] {severity_icon} {event.event_type.value.upper()}")
            lines.append(f"    Time: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"    Actor: {event.actor}")
            lines.append(f"    Component: {event.component}")
            lines.append(f"    Description: {event.description}")

            if event.risk_score is not None:
                lines.append(f"    Risk Score: {event.risk_score:.2f}")

            if event.decision:
                lines.append(f"    Decision: {event.decision}")

            if event.event_data:
                lines.append(f"    Data: {json.dumps(event.event_data, indent=8)}")

            if event.tags:
                lines.append(f"    Tags: {', '.join(event.tags)}")

        lines.append("\n" + "=" * 80)
        lines.append(f"END OF AUDIT TRAIL - {trail.transaction_id}")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_audit_summary(self, transaction_id: str) -> str:
        """Generate audit summary"""
        trail = self.active_trails.get(transaction_id)
        if not trail:
            return "No audit trail found"

        summary = f"""
AUDIT SUMMARY - Transaction {transaction_id}

Timeline:
  Started: {trail.started_at.strftime('%Y-%m-%d %H:%M:%S')}
  Anomaly Detected: {trail.anomaly_detected_at.strftime('%H:%M:%S') if trail.anomaly_detected_at else 'N/A'}
  Approval Requested: {trail.approval_requested_at.strftime('%H:%M:%S') if trail.approval_requested_at else 'N/A'}
  Approval Received: {trail.approval_received_at.strftime('%H:%M:%S') if trail.approval_received_at else 'N/A'}
  Completed: {trail.completed_at.strftime('%Y-%m-%d %H:%M:%S') if trail.completed_at else 'In Progress'}

Statistics:
  Total Events: {trail.total_events}
  Critical Events: {trail.critical_events}
  Warnings: {trail.warnings}
  Errors: {trail.errors}

Event Breakdown:
"""
        # Count events by type
        event_counts = {}
        for event in trail.events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        for event_type, count in sorted(event_counts.items()):
            summary += f"  {event_type}: {count}\n"

        return summary.strip()

    def search_events(
        self,
        transaction_id: str,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        actor: Optional[str] = None,
        component: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Search for specific events in audit trail"""
        trail = self.active_trails.get(transaction_id)
        if not trail:
            return []

        results = trail.events

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if severity:
            results = [e for e in results if e.severity == severity]

        if actor:
            results = [e for e in results if actor.lower() in e.actor.lower()]

        if component:
            results = [e for e in results if component.lower() in e.component.lower()]

        return results
