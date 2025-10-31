# human_in_loop.py
"""
Human-in-the-Loop (HITL) module for compliance workflow
Handles human approvals, notifications, and action execution
"""

from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    DASHBOARD = "dashboard"


class ActionType(str, Enum):
    BLOCK_CARD = "block_card"
    FREEZE_ACCOUNT = "freeze_account"
    CONTACT_CUSTOMER = "contact_customer"
    FILE_STR = "file_str"  # Suspicious Transaction Report
    NOTIFY_MAS = "notify_mas"
    ESCALATE_TO_SENIOR = "escalate_to_senior"
    MONITOR_ONLY = "monitor_only"
    ALLOW_TRANSACTION = "allow_transaction"


class HumanApprovalRequest(BaseModel):
    """Request for human approval on a compliance decision"""

    case_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    risk_score: float
    regulation: str
    recommended_action: str
    department_results: Dict[str, Any]
    requires_approval_reason: str  # Why human approval is needed
    approver_role: Literal[
        "Compliance Officer", "Senior Manager", "Head of Compliance", "Legal Counsel"
    ]
    urgency: Literal["Low", "Medium", "High", "Critical"]
    deadline: Optional[datetime] = None


class HumanApprovalResponse(BaseModel):
    """Human's response to approval request"""

    case_id: str
    approver_name: str
    approver_role: str
    status: ApprovalStatus
    decision: Optional[str] = None  # Override decision if any
    comments: Optional[str] = None
    approved_at: datetime = Field(default_factory=datetime.now)
    additional_actions: List[ActionType] = Field(default_factory=list)


class ActionExecutionPlan(BaseModel):
    """Plan for executing approved actions"""

    case_id: str
    actions: List[ActionType]
    execution_order: List[int]  # Order in which to execute actions
    notification_channels: List[NotificationChannel]
    notification_recipients: List[str]  # Email addresses, phone numbers, etc.
    sla_deadline: Optional[datetime] = None
    rollback_plan: Optional[str] = None


class ActionExecutionResult(BaseModel):
    """Result of action execution"""

    case_id: str
    action: ActionType
    status: Literal["success", "failed", "partial"]
    executed_at: datetime = Field(default_factory=datetime.now)
    details: str
    error_message: Optional[str] = None


class HumanInLoopDecisionEngine:
    """
    Decision engine that determines when human approval is needed
    """

    def __init__(self):
        self.approval_thresholds = {
            "risk_score": 0.75,
            "prior_alerts": 3,
            "high_value_threshold": 50000,  # SGD
        }

    def requires_human_approval(
        self,
        case_id: str,
        risk_score: float,
        regulation: str,
        recommendation: str,
        department_results: Dict[str, Any],
        prior_alert_count: int = 0,
    ) -> tuple[bool, Optional[HumanApprovalRequest]]:
        """
        Determine if human approval is required based on multiple criteria

        Returns:
            (needs_approval, approval_request)
        """
        reasons = []
        urgency = "Medium"
        approver_role = "Compliance Officer"

        # Rule 1: High risk score requires approval
        if risk_score >= 0.85:
            reasons.append(f"Risk score {risk_score} exceeds critical threshold (0.85)")
            urgency = "Critical"
            approver_role = "Head of Compliance"
        elif risk_score >= self.approval_thresholds["risk_score"]:
            reasons.append(
                f"Risk score {risk_score} exceeds approval threshold ({self.approval_thresholds['risk_score']})"
            )
            urgency = "High"

        # Rule 2: Block recommendation requires approval
        if recommendation == "Block":
            reasons.append(
                "Block action requires human verification to avoid customer disruption"
            )
            urgency = "High" if urgency == "Medium" else urgency

        # Rule 3: Repeated alerts require approval
        if prior_alert_count >= self.approval_thresholds["prior_alerts"]:
            reasons.append(f"Customer has {prior_alert_count} prior alerts in 30 days")
            approver_role = "Senior Manager"

        # Rule 4: Legal risk requires approval
        legal_result = department_results.get("Legal")
        if legal_result and isinstance(legal_result, dict):
            legal_risk = legal_result.get("legal_risk_level", "Low")
            if legal_risk == "High":
                reasons.append("High legal risk identified by Legal department")
                approver_role = "Legal Counsel"
                urgency = "Critical"

        # Rule 5: MAS reporting requires approval
        compliance_result = department_results.get("Compliance")
        if compliance_result and isinstance(compliance_result, dict):
            reporting = compliance_result.get("required_reporting", "None")
            if "MAS" in reporting:
                reasons.append(
                    "Requires MAS notification - regulatory submission needs approval"
                )
                approver_role = "Head of Compliance"
                urgency = "Critical"

        # Rule 6: Conflicting department recommendations
        if self._has_conflicting_recommendations(department_results):
            reasons.append(
                "Conflicting recommendations from departments require human arbitration"
            )
            urgency = "High"
            approver_role = "Senior Manager"

        if reasons:
            approval_request = HumanApprovalRequest(
                case_id=case_id,
                risk_score=risk_score,
                regulation=regulation,
                recommended_action=recommendation,
                department_results=department_results,
                requires_approval_reason="; ".join(reasons),
                approver_role=approver_role,
                urgency=urgency,
            )
            return True, approval_request

        return False, None

    def _has_conflicting_recommendations(
        self, department_results: Dict[str, Any]
    ) -> bool:
        """Check if departments have conflicting recommendations"""
        escalations = []

        front = department_results.get("FrontOffice", {})
        if isinstance(front, dict) and front.get("escalation_needed"):
            escalations.append("Front")

        legal = department_results.get("Legal", {})
        if isinstance(legal, dict) and legal.get("legal_risk_level") == "High":
            escalations.append("Legal")

        # If multiple departments are flagging concerns, might need human review
        return len(escalations) >= 2


class ActionExecutor:
    """
    Executes approved actions and handles notifications
    """

    def __init__(self):
        self.execution_log: List[ActionExecutionResult] = []

    def create_execution_plan(
        self,
        case_id: str,
        final_decision: str,
        department_results: Dict[str, Any],
        approval_response: Optional[HumanApprovalResponse] = None,
    ) -> ActionExecutionPlan:
        """
        Create an execution plan based on the final decision
        """
        actions = []
        notification_channels = [
            NotificationChannel.EMAIL,
            NotificationChannel.DASHBOARD,
        ]
        recipients = ["compliance@bank.com.sg"]

        # Map decision to actions
        if final_decision == "Block" or (
            approval_response and "block" in approval_response.decision.lower()
        ):
            actions.extend(
                [
                    ActionType.BLOCK_CARD,
                    ActionType.CONTACT_CUSTOMER,
                    ActionType.FILE_STR,
                ]
            )
            notification_channels.append(NotificationChannel.SMS)
            recipients.extend(["fraud-team@bank.com.sg", "senior-manager@bank.com.sg"])

        elif final_decision == "Monitor":
            actions.extend(
                [
                    ActionType.MONITOR_ONLY,
                    ActionType.CONTACT_CUSTOMER,
                ]
            )

        elif final_decision == "Allow":
            actions.append(ActionType.ALLOW_TRANSACTION)

        # Add MAS notification if required
        compliance_result = department_results.get("Compliance", {})
        if isinstance(compliance_result, dict) and "MAS" in compliance_result.get(
            "required_reporting", ""
        ):
            actions.append(ActionType.NOTIFY_MAS)
            recipients.append("regulatory-reporting@bank.com.sg")

        # Add any additional actions from human approval
        if approval_response and approval_response.additional_actions:
            actions.extend(approval_response.additional_actions)

        # Define execution order (priority-based)
        action_priority = {
            ActionType.BLOCK_CARD: 1,
            ActionType.FREEZE_ACCOUNT: 1,
            ActionType.FILE_STR: 2,
            ActionType.NOTIFY_MAS: 2,
            ActionType.CONTACT_CUSTOMER: 3,
            ActionType.ESCALATE_TO_SENIOR: 4,
            ActionType.MONITOR_ONLY: 5,
            ActionType.ALLOW_TRANSACTION: 6,
        }

        execution_order = sorted(
            range(len(actions)), key=lambda i: action_priority.get(actions[i], 99)
        )

        return ActionExecutionPlan(
            case_id=case_id,
            actions=actions,
            execution_order=execution_order,
            notification_channels=notification_channels,
            notification_recipients=recipients,
        )

    def execute_action(self, case_id: str, action: ActionType) -> ActionExecutionResult:
        """
        Execute a single action (mock implementation)
        In production, this would call actual banking systems
        """
        print(f"\n🔧 Executing action: {action.value} for case {case_id}")

        # Mock execution - in real system, call actual APIs
        result = ActionExecutionResult(
            case_id=case_id,
            action=action,
            status="success",
            details=f"Action {action.value} executed successfully",
        )

        # Simulate different execution scenarios
        if action == ActionType.BLOCK_CARD:
            result.details = (
                "Card blocked in core banking system. Block ID: BLK-" + case_id
            )
        elif action == ActionType.CONTACT_CUSTOMER:
            result.details = (
                "Customer notification sent via SMS and email. Ticket ID: TKT-"
                + case_id
            )
        elif action == ActionType.FILE_STR:
            result.details = (
                "Suspicious Transaction Report filed with reference: STR-" + case_id
            )
        elif action == ActionType.NOTIFY_MAS:
            result.details = (
                "MAS notification submitted via regulatory portal. Ref: MAS-" + case_id
            )

        self.execution_log.append(result)
        print(f"   ✅ {result.details}")

        return result

    def execute_plan(self, plan: ActionExecutionPlan) -> List[ActionExecutionResult]:
        """
        Execute all actions in the plan according to execution order
        """
        print(f"\n📋 Executing action plan for case: {plan.case_id}")
        print(f"   Actions to execute: {len(plan.actions)}")

        results = []

        for idx in plan.execution_order:
            action = plan.actions[idx]
            result = self.execute_action(plan.case_id, action)
            results.append(result)

        # Send notifications
        self._send_notifications(plan)

        return results

    def _send_notifications(self, plan: ActionExecutionPlan):
        """Send notifications to relevant parties"""
        print(
            f"\n📧 Sending notifications via: {[ch.value for ch in plan.notification_channels]}"
        )
        print(f"   Recipients: {plan.notification_recipients}")
        # In production, integrate with email/SMS/Slack APIs


def simulate_human_approval(
    approval_request: HumanApprovalRequest,
) -> HumanApprovalResponse:
    """
    Simulate human approval process
    In production, this would be an interactive UI or approval system
    """
    print("\n" + "=" * 80)
    print("🚨 HUMAN APPROVAL REQUIRED 🚨")
    print("=" * 80)
    print(f"Case ID: {approval_request.case_id}")
    print(f"Risk Score: {approval_request.risk_score}")
    print(f"Urgency: {approval_request.urgency}")
    print(f"Approver Required: {approval_request.approver_role}")
    print(f"\nReason for Approval:")
    print(f"  {approval_request.requires_approval_reason}")
    print(f"\nRecommended Action: {approval_request.recommended_action}")
    print("\nDepartment Results:")
    for dept, result in approval_request.department_results.items():
        print(f"  {dept}: {result}")
    print("=" * 80)

    # Auto-approve for demo purposes
    # In production, this would wait for actual human input
    print("\n⏳ Waiting for human approval...")
    print("✅ APPROVED by Senior Compliance Officer")

    return HumanApprovalResponse(
        case_id=approval_request.case_id,
        approver_name="Sarah Chen",
        approver_role="Senior Compliance Officer",
        status=ApprovalStatus.APPROVED,
        decision="Approved: Proceed with blocking the card and filing STR",
        comments="High risk case with clear regulatory breach. Immediate action required.",
        additional_actions=[ActionType.ESCALATE_TO_SENIOR],
    )
