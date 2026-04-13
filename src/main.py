import json

from src.core.schemas import Case
from src.core.state import (
    init_state_from_case,
    append_user_agent_turn,
    append_bot_turn,
)
from src.simulator.simulator import CustomerServiceSimulator
from src.agents.verified_agent import VerifiedAgent
from src.tools.response_classifier import classify_bot_response
from src.tools.handoff_detector import detect_handoff_offer, detect_handoff_signal
from src.tools.loop_detector import detect_loop_from_history


def load_cases(path: str) -> list[Case]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Case(**item) for item in raw]


def run_case(case: Case) -> None:
    print("=" * 80)
    print(f"Running case: {case.case_id}")
    print(f"Issue type: {case.issue_type}")
    print(f"Bot profile: {case.bot_profile}")
    print("-" * 80)

    simulator = CustomerServiceSimulator()
    agent = VerifiedAgent()
    state = init_state_from_case(case)

    done = False

    while not done and state.turn_count < case.max_turns:
        agent_message, action = agent.next_action(case, state)

        append_user_agent_turn(state, agent_message, action)

        print(f"[user_agent] {agent_message}")
        print(f"  action = {action}")
        print(f"  escalation_attempts = {state.escalation_attempts}")
        print(f"  loop_score = {state.loop_score}")

        if action == "alert_user_takeover":
            state.user_alerted = True
            done = True
            print()
            continue

        if action == "push_for_human":
            state.escalation_attempts += 1

        response = simulator.step(
            case=case,
            conversation_state=state,
            agent_message=agent_message,
        )

        predicted_label = classify_bot_response(response.bot_message)
        handoff_offer = detect_handoff_offer(response.bot_message)
        handoff_signal = detect_handoff_signal(response.bot_message)

        append_bot_turn(state, response.bot_message, predicted_label)

        is_loop, loop_score = detect_loop_from_history(state.history)
        state.loop_score = loop_score

        # Keep state consistent:
        # a predicted handoff_signal must always update human_signal_detected.
        if predicted_label == "handoff_signal" or handoff_signal:
            state.human_signal_detected = True

        print(f"[bot] {response.bot_message}")
        print(f"  gold_label = {response.bot_gold_label}")
        print(f"  predicted_label = {predicted_label}")
        print(f"  handoff_offer = {handoff_offer}")
        print(f"  handoff_signal = {handoff_signal}")
        print(f"  loop = {is_loop}, score = {loop_score}")
        print()

    print("-" * 80)
    print("Final state:")
    print(f"turn_count = {state.turn_count}")
    print(f"last_bot_label = {state.last_bot_label}")
    print(f"human_signal_detected = {state.human_signal_detected}")
    print(f"user_alerted = {state.user_alerted}")
    print(f"escalation_attempts = {state.escalation_attempts}")
    print(f"loop_score = {state.loop_score}")
    print("=" * 80)
    print()


def main():
    cases = load_cases("data/cases.json")
    for case in cases:
        run_case(case)


if __name__ == "__main__":
    main()