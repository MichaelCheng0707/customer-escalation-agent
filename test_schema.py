from src.core.schemas import Case

case = Case(
    case_id="B001",
    issue_type="billing_dispute",
    severity="high",
    user_goal="reach_human",
    initial_user_message="I was charged twice for the same purchase.",
    bot_profile="deflective",
    success_condition="handoff_signal_detected",
    max_turns=5
)

print(case)
print(case.model_dump())