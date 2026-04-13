from src.core.schemas import Case
from src.core.state import init_state_from_case
from src.agents.stateful_agent import StatefulAgentWithoutVerification


case_high = Case(
    case_id="B001",
    issue_type="billing_dispute",
    severity="high",
    user_goal="reach_human",
    initial_user_message="I was charged twice for the same purchase and need to speak to a human representative.",
    bot_profile="deflective",
    success_condition="handoff_signal_detected",
    max_turns=5,
)

agent = StatefulAgentWithoutVerification()
state = init_state_from_case(case_high)

message, action = agent.next_action(case_high, state)
print("turn 0")
print("message =", message)
print("action =", action)

state.turn_count = 1
state.escalation_attempts = 0
message, action = agent.next_action(case_high, state)
print("turn 1")
print("message =", message)
print("action =", action)

state.turn_count = 2
state.escalation_attempts = 1
message, action = agent.next_action(case_high, state)
print("turn 2")
print("message =", message)
print("action =", action)

state.turn_count = 3
state.escalation_attempts = 2
message, action = agent.next_action(case_high, state)
print("turn 3")
print("message =", message)
print("action =", action)