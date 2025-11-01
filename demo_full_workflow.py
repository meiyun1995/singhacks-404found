#!/usr/bin/env python3
# demo_full_workflow.py
"""
Demonstration of the complete workflow with different approval scenarios
Shows how the workflow adapts to different management decisions
"""

print("\n" + "🎯" * 40)
print("COMPLIANCE WORKFLOW - INTERACTIVE DEMONSTRATION")
print("Showing dynamic execution branching based on approval decisions")
print("🎯" * 40 + "\n")

print(
    """
This demo shows how the workflow adapts based on management decisions:

1. ✅ APPROVED      - Standard execution as recommended
2. ❌ REJECTED      - Downgrade to monitoring only
3. 🔺 ESCALATED     - Route to higher authority with protective measures
4. 🔄 MODIFIED      - Adjust execution plan based on modified decision

Each scenario demonstrates different branching logic and outcomes.
"""
)

input("Press ENTER to start the demonstration...")

from human_in_loop import (
    HumanInLoopDecisionEngine,
    ActionExecutor,
    HumanApprovalRequest,
    HumanApprovalResponse,
    ApprovalStatus,
    ActionType,
)
from datetime import datetime


def demo_scenario(
    scenario_num, scenario_name, description, approval_status, decision, comments
):
    """Run a single scenario demonstration"""

    print("\n" + "=" * 80)
    print(f"SCENARIO {scenario_num}: {scenario_name}")
    print("=" * 80)
    print(f"Description: {description}\n")

    # Simulated department results
    department_results = {
        "FrontOffice": {
            "action_plan": "Block card immediately and contact customer",
            "customer_communication": "Suspicious activity detected, account review required",
            "escalation_needed": True,
            "notes": "High value cross-border transactions flagged",
        },
        "Legal": {
            "violation_assessment": "Potential breach of MAS Notice 626 13.14(b)",
            "required_disclosure": "MAS",
            "legal_risk_level": "High",
            "comments": "Multiple AML indicators present",
        },
        "Compliance": {
            "final_decision": "Block",
            "rationale": "Risk score exceeds threshold, regulatory violation suspected",
            "required_reporting": "MAS",
            "next_steps": "Compliance team to file STR within 24 hours",
        },
    }

    # Create approval request
    approval_request = HumanApprovalRequest(
        transaction_id=f"TXN-DEMO-{scenario_num}",
        risk_score=0.86,
        regulation="MAS Notice 626 13.14(b)",
        recommended_action="Block",
        department_results=department_results,
        requires_approval_reason="High risk score (0.86) exceeds critical threshold; MAS reporting required; High legal risk",
        approver_role="Senior Compliance Officer",
        urgency="High",
    )

    print("📊 INITIAL ASSESSMENT:")
    print(f"   Transaction ID: {approval_request.transaction_id}")
    print(f"   Risk Score: {approval_request.risk_score}")
    print(f"   Regulation: {approval_request.regulation}")
    print(f"   Department Recommendation: {approval_request.recommended_action}")
    print(f"   Urgency: {approval_request.urgency}")
    print(f"\n   Reason for Approval:")
    print(f"   {approval_request.requires_approval_reason}")

    print("\n🔍 MANAGEMENT DECISION:")

    # Create approval response
    approval_response = HumanApprovalResponse(
        transaction_id=approval_request.transaction_id,
        approver_name="Sarah Chen",
        approver_role="Senior Compliance Officer",
        status=approval_status,
        decision=decision,
        comments=comments,
    )

    status_icons = {
        ApprovalStatus.APPROVED: "✅",
        ApprovalStatus.REJECTED: "❌",
        ApprovalStatus.ESCALATED: "🔺",
    }

    print(
        f"   Status: {status_icons.get(approval_status, '❓')} {approval_status.value.upper()}"
    )
    print(
        f"   Approver: {approval_response.approver_name} ({approval_response.approver_role})"
    )
    print(f"   Decision: {approval_response.decision}")
    print(f"   Comments: {approval_response.comments}")

    # Create and execute plan
    print("\n⚙️  CREATING EXECUTION PLAN...")

    executor = ActionExecutor()
    execution_plan = executor.create_execution_plan(
        transaction_id=approval_request.transaction_id,
        final_decision="Block",
        department_results=department_results,
        approval_response=approval_response,
    )

    print(f"\n   📋 Planned Actions:")
    for i, action in enumerate(execution_plan.actions, 1):
        print(f"      {i}. {action.value}")

    print(f"\n   📧 Notification Plan:")
    print(
        f"      Channels: {', '.join([ch.value for ch in execution_plan.notification_channels])}"
    )
    print(f"      Recipients: {', '.join(execution_plan.notification_recipients)}")

    if execution_plan.rollback_plan:
        print(f"\n   📝 Decision Notes:")
        print(f"      {execution_plan.rollback_plan}")

    # Execute
    print("\n🚀 EXECUTING PLAN...")
    execution_results = executor.execute_plan(execution_plan)

    print("\n✅ EXECUTION RESULTS:")
    for result in execution_results:
        status_icon = "✅" if result.status == "success" else "❌"
        print(f"   {status_icon} {result.action.value}")
        print(f"      → {result.details}")

    # Summary
    print(f"\n📊 SCENARIO OUTCOME:")
    all_success = all(r.status == "success" for r in execution_results)
    outcome_icon = "✅" if all_success else "⚠️"
    print(
        f"   {outcome_icon} Actions Completed: {len(execution_results)}/{len(execution_plan.actions)}"
    )

    if approval_status == ApprovalStatus.APPROVED and "modify" not in decision.lower():
        print(f"   ✅ Original recommendation EXECUTED as approved")
    elif approval_status == ApprovalStatus.REJECTED:
        print(f"   ❌ Original recommendation REJECTED - monitoring only")
    elif approval_status == ApprovalStatus.ESCALATED:
        print(f"   🔺 Case ESCALATED to higher authority - protective measures applied")
    elif "modify" in decision.lower() or "change" in decision.lower():
        print(f"   🔄 Recommendation MODIFIED - execution plan adjusted")

    print("\n" + "-" * 80)
    input("\nPress ENTER to continue to next scenario...")


# Run demonstration scenarios
demo_scenario(
    scenario_num=1,
    scenario_name="APPROVED ✅ - Standard Approval",
    description="Management approves the recommendation to block the card",
    approval_status=ApprovalStatus.APPROVED,
    decision="Approved: Proceed with blocking the card and filing STR",
    comments="High risk case with clear regulatory breach. Multiple AML indicators present. Immediate action required to prevent potential money laundering activity.",
)

demo_scenario(
    scenario_num=2,
    scenario_name="REJECTED ❌ - False Positive",
    description="Management rejects the blocking recommendation after review",
    approval_status=ApprovalStatus.REJECTED,
    decision="Rejected: Do not block - identified as false positive",
    comments="After detailed review of customer transaction history and business profile, this appears to be legitimate import/export business activity. Customer has verified documentation. Add to monitoring watchlist but do not block.",
)

demo_scenario(
    scenario_num=3,
    scenario_name="ESCALATED 🔺 - VIP Customer Requires Executive Decision",
    description="Case escalated due to VIP customer status and business impact",
    approval_status=ApprovalStatus.ESCALATED,
    decision="Escalated: Requires CEO and legal counsel approval",
    comments="Customer is a high-net-worth VIP client with 15-year relationship and $50M AUM. Potential significant reputational and business impact. Freeze account temporarily pending executive committee decision within 24 hours.",
)

demo_scenario(
    scenario_num=4,
    scenario_name="MODIFIED 🔄 - Downgrade to Enhanced Monitoring",
    description="Management modifies recommendation from Block to Monitor with enhanced oversight",
    approval_status=ApprovalStatus.APPROVED,
    decision="Modified: Change from Block to Enhanced Monitor - insufficient conclusive evidence",
    comments="Risk indicators are elevated but not conclusive for immediate blocking. Implement enhanced monitoring for 7 days with daily review. Contact customer for transaction verification. Escalate if additional suspicious activity detected.",
)

# Final summary
print("\n" + "=" * 80)
print("🎉 DEMONSTRATION COMPLETE")
print("=" * 80)
print(
    """
Summary of Dynamic Branching Scenarios Demonstrated:

1. ✅ APPROVED
   → Standard execution: Block card, Contact customer, File STR, Notify MAS
   → Full departmental recommendations executed
   
2. ❌ REJECTED  
   → Downgraded to monitoring only
   → No customer-impacting actions
   → Enhanced audit trail and notifications
   
3. 🔺 ESCALATED
   → Temporary account freeze for protection
   → Escalation ticket created
   → Executive stakeholders notified (CEO, Legal Counsel)
   → Enhanced notification channels (Teams)
   
4. 🔄 MODIFIED
   → Original "Block" changed to "Monitor"
   → Execution plan automatically adjusted
   → Contact customer for verification
   → Audit trail captures modification

Key Benefits:
✅ Flexible human oversight
✅ Context-aware decision making
✅ Complete audit trail
✅ Regulatory compliance (MAS)
✅ Risk-appropriate actions
✅ Customer relationship protection

The system successfully adapts to different management decisions while
maintaining compliance, audit trails, and appropriate safeguards.
"""
)

print("=" * 80 + "\n")
