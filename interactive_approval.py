# interactive_approval.py
"""
Interactive approval interface for human-in-the-loop compliance workflow
This demonstrates how a real approval UI would work
"""

from human_in_loop import (
    HumanApprovalRequest,
    HumanApprovalResponse,
    ApprovalStatus,
    ActionType,
)
from datetime import datetime
from typing import Optional


def interactive_approval_cli(
    approval_request: HumanApprovalRequest,
) -> HumanApprovalResponse:
    """
    Interactive CLI for human approval
    In production, this would be a web UI
    """
    print("\n" + "=" * 80)
    print("🚨 COMPLIANCE APPROVAL REQUEST 🚨")
    print("=" * 80)
    print(f"\n📋 Case Details:")
    print(f"   Case ID: {approval_request.case_id}")
    print(f"   Timestamp: {approval_request.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Urgency: {approval_request.urgency}")
    print(f"   Risk Score: {approval_request.risk_score:.2f}")

    print(f"\n📖 Regulatory Context:")
    print(f"   Regulation: {approval_request.regulation}")
    print(f"   Recommended Action: {approval_request.recommended_action}")

    print(f"\n⚠️  Reason for Human Approval:")
    print(f"   {approval_request.requires_approval_reason}")

    print(f"\n👤 Approver Required:")
    print(f"   Role: {approval_request.approver_role}")
    if approval_request.deadline:
        print(f"   Deadline: {approval_request.deadline.strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n📊 Department Analysis:")
    for dept, result in approval_request.department_results.items():
        print(f"\n   {dept}:")
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"      • {key}: {value}")
        else:
            print(f"      {result}")

    print("\n" + "=" * 80)
    print("⚡ DECISION REQUIRED")
    print("=" * 80)

    # Get user input
    print("\nOptions:")
    print("  1. ✅ APPROVE - Proceed with recommended action")
    print("  2. ✅ APPROVE WITH MODIFICATIONS - Approve but modify actions")
    print("  3. ❌ REJECT - Do not proceed")
    print("  4. ⬆️  ESCALATE - Send to higher authority")

    while True:
        choice = input("\nEnter your decision (1-4): ").strip()

        if choice == "1":
            # Approve as-is
            approver_name = input("Your name: ").strip() or "Demo Approver"
            comments = input("Comments (optional): ").strip()

            return HumanApprovalResponse(
                case_id=approval_request.case_id,
                approver_name=approver_name,
                approver_role=approval_request.approver_role,
                status=ApprovalStatus.APPROVED,
                decision=f"Approved: Proceed with {approval_request.recommended_action}",
                comments=comments
                or "Approved after review of department recommendations",
            )

        elif choice == "2":
            # Approve with modifications
            approver_name = input("Your name: ").strip() or "Demo Approver"
            print("\nAdditional actions to include:")
            print("  a. Contact customer immediately")
            print("  b. Escalate to senior management")
            print("  c. Enhanced monitoring for 30 days")
            print("  d. Request additional documentation")

            additional_input = input(
                "Select additional actions (comma-separated, e.g., a,b): "
            ).strip()

            additional_actions = []
            if "a" in additional_input:
                additional_actions.append(ActionType.CONTACT_CUSTOMER)
            if "b" in additional_input:
                additional_actions.append(ActionType.ESCALATE_TO_SENIOR)
            if "c" in additional_input:
                additional_actions.append(ActionType.MONITOR_ONLY)

            comments = input("Comments explaining modifications: ").strip()

            return HumanApprovalResponse(
                case_id=approval_request.case_id,
                approver_name=approver_name,
                approver_role=approval_request.approver_role,
                status=ApprovalStatus.APPROVED,
                decision=f"Approved with modifications: {approval_request.recommended_action}",
                comments=comments,
                additional_actions=additional_actions,
            )

        elif choice == "3":
            # Reject
            approver_name = input("Your name: ").strip() or "Demo Approver"
            reason = input("Reason for rejection: ").strip()
            alternative = input("Alternative recommendation: ").strip()

            return HumanApprovalResponse(
                case_id=approval_request.case_id,
                approver_name=approver_name,
                approver_role=approval_request.approver_role,
                status=ApprovalStatus.REJECTED,
                decision=f"Rejected: {alternative}",
                comments=f"Rejection reason: {reason}",
            )

        elif choice == "4":
            # Escalate
            approver_name = input("Your name: ").strip() or "Demo Approver"
            escalation_reason = input("Reason for escalation: ").strip()

            return HumanApprovalResponse(
                case_id=approval_request.case_id,
                approver_name=approver_name,
                approver_role=approval_request.approver_role,
                status=ApprovalStatus.ESCALATED,
                decision="Escalated to senior leadership",
                comments=f"Escalation reason: {escalation_reason}",
                additional_actions=[ActionType.ESCALATE_TO_SENIOR],
            )

        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")


def print_approval_dashboard(requests: list[HumanApprovalRequest]):
    """
    Display a dashboard of pending approval requests
    """
    print("\n" + "=" * 80)
    print("📊 COMPLIANCE APPROVAL DASHBOARD")
    print("=" * 80)

    if not requests:
        print("\n✅ No pending approvals")
        return

    print(f"\n📋 {len(requests)} Pending Approval(s)\n")

    # Sort by urgency
    urgency_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    sorted_requests = sorted(requests, key=lambda r: urgency_order.get(r.urgency, 4))

    for i, req in enumerate(sorted_requests, 1):
        urgency_icon = {
            "Critical": "🔴",
            "High": "🟠",
            "Medium": "🟡",
            "Low": "🟢",
        }.get(req.urgency, "⚪")

        print(f"{i}. {urgency_icon} {req.case_id}")
        print(
            f"   Risk: {req.risk_score:.2f} | Urgency: {req.urgency} | Approver: {req.approver_role}"
        )
        print(f"   Action: {req.recommended_action}")
        print(f"   Reason: {req.requires_approval_reason[:80]}...")
        print()


if __name__ == "__main__":
    # Example: Create sample approval requests for dashboard
    from human_in_loop import HumanApprovalRequest

    sample_requests = [
        HumanApprovalRequest(
            case_id="C-2025-11-01-0001",
            risk_score=0.92,
            regulation="MAS Notice 626 13.14(b)",
            recommended_action="Block",
            department_results={
                "FrontOffice": {"escalation_needed": True},
                "Legal": {"legal_risk_level": "High"},
            },
            requires_approval_reason="Risk score 0.92 exceeds critical threshold",
            approver_role="Head of Compliance",
            urgency="Critical",
        ),
        HumanApprovalRequest(
            case_id="C-2025-11-01-0002",
            risk_score=0.78,
            regulation="MAS TRM Guidelines",
            recommended_action="Monitor",
            department_results={
                "Compliance": {"final_decision": "Monitor"},
            },
            requires_approval_reason="Customer has 4 prior alerts in 30 days",
            approver_role="Senior Manager",
            urgency="High",
        ),
    ]

    print_approval_dashboard(sample_requests)

    # Demonstrate interactive approval
    print("\n" + "=" * 80)
    print("🎮 INTERACTIVE APPROVAL DEMO")
    print("=" * 80)
    print("\nProcessing first request...\n")

    response = interactive_approval_cli(sample_requests[0])

    print("\n" + "=" * 80)
    print("✅ APPROVAL RECORDED")
    print("=" * 80)
    print(f"Status: {response.status.value.upper()}")
    print(f"Approver: {response.approver_name}")
    print(f"Decision: {response.decision}")
    if response.comments:
        print(f"Comments: {response.comments}")
    if response.additional_actions:
        print(f"Additional Actions: {[a.value for a in response.additional_actions]}")
    print("=" * 80)
