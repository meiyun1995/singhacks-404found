# human_in_loop.py
"""
Human-in-the-Loop (HITL) module for compliance workflow
Handles human approvals, notifications, and action execution
"""

import sys
from typing import Optional, List, Dict, Any, Tuple

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal
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

    transaction_id: str
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

    transaction_id: str
    approver_name: str
    approver_role: str
    status: ApprovalStatus
    decision: Optional[str] = None  # Override decision if any
    comments: Optional[str] = None
    approved_at: datetime = Field(default_factory=datetime.now)
    additional_actions: List[ActionType] = Field(default_factory=list)


class ActionExecutionPlan(BaseModel):
    """Plan for executing approved actions"""

    transaction_id: str
    actions: List[ActionType]
    execution_order: List[int]  # Order in which to execute actions
    notification_channels: List[NotificationChannel]
    notification_recipients: List[str]  # Email addresses, phone numbers, etc.
    sla_deadline: Optional[datetime] = None
    rollback_plan: Optional[str] = None


class ActionExecutionResult(BaseModel):
    """Result of action execution"""

    transaction_id: str
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
        transaction_id: str,
        risk_score: float,
        regulation: str,
        recommendation: str,
        department_results: Dict[str, Any],
        prior_alert_count: int = 0,
    ) -> Tuple[bool, Optional[HumanApprovalRequest]]:
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
                transaction_id=transaction_id,
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
        transaction_id: str,
        final_decision: str,
        department_results: Dict[str, Any],
        approval_response: Optional[HumanApprovalResponse] = None,
    ) -> ActionExecutionPlan:
        """
        Create an execution plan based on the final decision and approval status
        Branches logic based on approval response status
        """
        # Branch based on approval status
        if approval_response:
            if approval_response.status == ApprovalStatus.REJECTED:
                return self._create_rejection_plan(
                    transaction_id,
                    final_decision,
                    department_results,
                    approval_response,
                )
            elif approval_response.status == ApprovalStatus.ESCALATED:
                return self._create_escalation_plan(
                    transaction_id,
                    final_decision,
                    department_results,
                    approval_response,
                )
            elif (
                approval_response.status == ApprovalStatus.APPROVED
                and approval_response.decision
            ):
                # Check if management modified the decision
                if self._is_decision_modified(
                    final_decision, approval_response.decision
                ):
                    return self._create_modified_plan(
                        transaction_id,
                        final_decision,
                        department_results,
                        approval_response,
                    )

        # Default approved plan or no approval needed
        return self._create_standard_plan(
            transaction_id, final_decision, department_results, approval_response
        )

    def _is_decision_modified(
        self, original_decision: str, approval_decision: str
    ) -> bool:
        """Check if the management decision modifies the original recommendation"""
        # Look for override keywords in the approval decision
        approval_lower = approval_decision.lower()
        original_lower = original_decision.lower()

        # Explicit modification keywords take precedence
        override_keywords = [
            "modify",
            "modified",
            "change",
            "changed",
            "instead",
            "override",
            "downgrade",
            "upgrade",
        ]
        has_explicit_override = any(
            keyword in approval_lower for keyword in override_keywords
        )

        if has_explicit_override:
            return True

        # Check if decision mentions different action than original (but exclude approval keywords)
        decision_keywords = {
            "block": ["block", "freeze", "suspend", "blocking"],
            "monitor": ["monitor", "watch", "observe", "monitoring"],
            "allow": ["allow", "permit"],  # Removed 'approve' to avoid false positives
        }

        # Only flag as modified if a DIFFERENT action is explicitly mentioned
        for decision_type, keywords in decision_keywords.items():
            if decision_type != original_lower:
                # Check if this different action is mentioned with action verbs
                for keyword in keywords:
                    if keyword in approval_lower and any(
                        verb in approval_lower for verb in ["to ", "with ", "for "]
                    ):
                        return True

        return False

    def _create_standard_plan(
        self,
        transaction_id: str,
        final_decision: str,
        department_results: Dict[str, Any],
        approval_response: Optional[HumanApprovalResponse] = None,
    ) -> ActionExecutionPlan:
        """Create standard execution plan for approved decisions"""
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
        execution_order = self._calculate_execution_order(actions)

        return ActionExecutionPlan(
            transaction_id=transaction_id,
            actions=actions,
            execution_order=execution_order,
            notification_channels=notification_channels,
            notification_recipients=recipients,
        )

    def _create_rejection_plan(
        self,
        transaction_id: str,
        final_decision: str,
        department_results: Dict[str, Any],
        approval_response: HumanApprovalResponse,
    ) -> ActionExecutionPlan:
        """Create execution plan when management rejects the recommendation"""
        print(f"\n⚠️  Creating REJECTION plan - management rejected recommendation")

        # For rejection: log the rejection, notify teams, but don't execute blocking actions
        actions = [
            ActionType.MONITOR_ONLY,  # Downgrade to monitoring
        ]

        notification_channels = [
            NotificationChannel.EMAIL,
            NotificationChannel.DASHBOARD,
            NotificationChannel.SLACK,  # Extra notification for rejection
        ]

        recipients = [
            "compliance@bank.com.sg",
            "senior-manager@bank.com.sg",
            "audit-trail@bank.com.sg",  # Audit the rejection
        ]

        # Add any additional actions specified by approver
        if approval_response.additional_actions:
            actions.extend(approval_response.additional_actions)

        execution_order = self._calculate_execution_order(actions)

        return ActionExecutionPlan(
            transaction_id=transaction_id,
            actions=actions,
            execution_order=execution_order,
            notification_channels=notification_channels,
            notification_recipients=recipients,
            rollback_plan=f"Rejection by {approval_response.approver_name}: {approval_response.comments}",
        )

    def _create_escalation_plan(
        self,
        transaction_id: str,
        final_decision: str,
        department_results: Dict[str, Any],
        approval_response: HumanApprovalResponse,
    ) -> ActionExecutionPlan:
        """Create execution plan when case is escalated to higher authority"""
        print(f"\n🔺 Creating ESCALATION plan - case escalated to higher authority")

        # For escalation: notify senior management, create escalation ticket, monitor pending decision
        actions = [
            ActionType.ESCALATE_TO_SENIOR,
            ActionType.MONITOR_ONLY,  # Monitor while escalated
        ]

        # If high risk, add protective measures during escalation
        if department_results.get("Legal", {}).get("legal_risk_level") == "High":
            actions.insert(
                0, ActionType.FREEZE_ACCOUNT
            )  # Temporary freeze pending decision

        notification_channels = [
            NotificationChannel.EMAIL,
            NotificationChannel.DASHBOARD,
            NotificationChannel.TEAMS,  # Use Teams for escalation
        ]

        recipients = [
            "compliance@bank.com.sg",
            "head-of-compliance@bank.com.sg",
            "ceo@bank.com.sg",  # Escalate to executive level
            "legal-counsel@bank.com.sg",
        ]

        # Add any additional actions specified by approver
        if approval_response.additional_actions:
            actions.extend(approval_response.additional_actions)

        execution_order = self._calculate_execution_order(actions)

        return ActionExecutionPlan(
            transaction_id=transaction_id,
            actions=actions,
            execution_order=execution_order,
            notification_channels=notification_channels,
            notification_recipients=recipients,
            rollback_plan=f"Escalated by {approval_response.approver_name}: {approval_response.comments}",
        )

    def _create_modified_plan(
        self,
        transaction_id: str,
        final_decision: str,
        department_results: Dict[str, Any],
        approval_response: HumanApprovalResponse,
    ) -> ActionExecutionPlan:
        """Create execution plan when management modifies the recommendation"""
        print(f"\n🔄 Creating MODIFIED plan - management changed recommendation")

        # Parse the modified decision from approval response
        approval_text = approval_response.decision.lower()

        # Determine new decision from approval text
        if any(word in approval_text for word in ["allow", "approve", "permit"]):
            modified_decision = "Allow"
        elif any(word in approval_text for word in ["monitor", "watch", "observe"]):
            modified_decision = "Monitor"
        elif any(word in approval_text for word in ["block", "freeze", "suspend"]):
            modified_decision = "Block"
        else:
            # Default to monitor if unclear
            modified_decision = "Monitor"

        print(f"   Original: {final_decision} → Modified: {modified_decision}")

        # Create plan based on modified decision (reuse standard logic)
        actions = []
        notification_channels = [
            NotificationChannel.EMAIL,
            NotificationChannel.DASHBOARD,
        ]
        recipients = ["compliance@bank.com.sg"]

        if modified_decision == "Block":
            actions.extend(
                [
                    ActionType.BLOCK_CARD,
                    ActionType.CONTACT_CUSTOMER,
                    ActionType.FILE_STR,
                ]
            )
            notification_channels.append(NotificationChannel.SMS)
            recipients.extend(["fraud-team@bank.com.sg", "senior-manager@bank.com.sg"])
        elif modified_decision == "Monitor":
            actions.extend(
                [
                    ActionType.MONITOR_ONLY,
                    ActionType.CONTACT_CUSTOMER,
                ]
            )
        elif modified_decision == "Allow":
            actions.append(ActionType.ALLOW_TRANSACTION)

        # Add MAS notification if required
        compliance_result = department_results.get("Compliance", {})
        if isinstance(compliance_result, dict) and "MAS" in compliance_result.get(
            "required_reporting", ""
        ):
            actions.append(ActionType.NOTIFY_MAS)
            recipients.append("regulatory-reporting@bank.com.sg")

        # Add additional actions from approver
        if approval_response.additional_actions:
            actions.extend(approval_response.additional_actions)

        # Add notification about modification
        recipients.append("audit-trail@bank.com.sg")

        execution_order = self._calculate_execution_order(actions)

        return ActionExecutionPlan(
            transaction_id=transaction_id,
            actions=actions,
            execution_order=execution_order,
            notification_channels=notification_channels,
            notification_recipients=recipients,
            rollback_plan=f"Modified by {approval_response.approver_name} from '{final_decision}' to '{modified_decision}': {approval_response.comments}",
        )

    def _calculate_execution_order(self, actions: List[ActionType]) -> List[int]:
        """Calculate priority-based execution order for actions"""
        action_priority = {
            ActionType.FREEZE_ACCOUNT: 1,
            ActionType.BLOCK_CARD: 1,
            ActionType.FILE_STR: 2,
            ActionType.NOTIFY_MAS: 2,
            ActionType.ESCALATE_TO_SENIOR: 3,
            ActionType.CONTACT_CUSTOMER: 4,
            ActionType.MONITOR_ONLY: 5,
            ActionType.ALLOW_TRANSACTION: 6,
        }

        return sorted(
            range(len(actions)), key=lambda i: action_priority.get(actions[i], 99)
        )

    def execute_action(
        self, transaction_id: str, action: ActionType
    ) -> ActionExecutionResult:
        """
        Execute a single action (mock implementation)
        In production, this would call actual banking systems
        """
        print(f"\n🔧 Executing action: {action.value} for transaction {transaction_id}")

        # Mock execution - in real system, call actual APIs
        result = ActionExecutionResult(
            transaction_id=transaction_id,
            action=action,
            status="success",
            details=f"Action {action.value} executed successfully",
        )

        # Simulate different execution scenarios
        if action == ActionType.BLOCK_CARD:
            result.details = (
                "Card blocked in core banking system. Block ID: BLK-" + transaction_id
            )
        elif action == ActionType.FREEZE_ACCOUNT:
            result.details = (
                "Account frozen in core banking system. Freeze ID: FRZ-"
                + transaction_id
            )
        elif action == ActionType.CONTACT_CUSTOMER:
            result.details = (
                "Customer notification sent via SMS and email. Ticket ID: TKT-"
                + transaction_id
            )
        elif action == ActionType.FILE_STR:
            result.details = (
                "Suspicious Transaction Report filed with reference: STR-"
                + transaction_id
            )
        elif action == ActionType.NOTIFY_MAS:
            result.details = (
                "MAS notification submitted via regulatory portal. Ref: MAS-"
                + transaction_id
            )
        elif action == ActionType.ESCALATE_TO_SENIOR:
            result.details = (
                "Case escalated to senior management. Escalation ticket: ESC-"
                + transaction_id
            )
        elif action == ActionType.MONITOR_ONLY:
            result.details = (
                "Transaction added to monitoring watchlist. Monitor ID: MON-"
                + transaction_id
            )
        elif action == ActionType.ALLOW_TRANSACTION:
            result.details = (
                "Transaction approved and allowed to proceed. Approval ID: APV-"
                + transaction_id
            )

        self.execution_log.append(result)
        print(f"   ✅ {result.details}")

        return result

    def execute_plan(self, plan: ActionExecutionPlan) -> List[ActionExecutionResult]:
        """
        Execute all actions in the plan according to execution order
        """
        print(f"\n📋 Executing action plan for transaction: {plan.transaction_id}")
        print(f"   Actions to execute: {len(plan.actions)}")

        results = []

        for idx in plan.execution_order:
            action = plan.actions[idx]
            result = self.execute_action(plan.transaction_id, action)
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
    print(f"Transaction ID: {approval_request.transaction_id}")
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
        transaction_id=approval_request.transaction_id,
        approver_name="Sarah Chen",
        approver_role="Senior Compliance Officer",
        status=ApprovalStatus.APPROVED,
        decision="Approved: Proceed with blocking the card and filing STR",
        comments="High risk case with clear regulatory breach. Immediate action required.",
        additional_actions=[ActionType.ESCALATE_TO_SENIOR],
    )
