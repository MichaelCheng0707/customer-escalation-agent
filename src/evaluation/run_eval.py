import json
from pathlib import Path

from src.core.schemas import Case
from src.core.state import (
    init_state_from_case,
    append_user_agent_turn,
    append_bot_turn,
)
from src.simulator.simulator import CustomerServiceSimulator

from src.agents.baseline_static import BaselineStaticAgent
from src.agents.stateful_agent import StatefulAgentWithoutVerification
from src.agents.verified_agent import VerifiedAgent

from src.tools.response_classifier import classify_bot_response
from src.tools.handoff_detector import detect_handoff_offer, detect_handoff_signal
from src.tools.loop_detector import detect_loop_from_history

from src.evaluation.metrics import summarize_metrics


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_cases(path: str) -> list[Case]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Case(**item) for item in raw]


def build_agents() -> dict:
    return {
        "static": BaselineStaticAgent(),
        "stateful": StatefulAgentWithoutVerification(),
        "verified": VerifiedAgent(),
    }


def update_state_for_verified_agent(state, bot_message: str) -> tuple[str, bool, bool, bool, float]:
    predicted_label = classify_bot_response(bot_message)
    handoff_offer = detect_handoff_offer(bot_message)
    handoff_signal = detect_handoff_signal(bot_message)

    append_bot_turn(state, bot_message, predicted_label)

    is_loop, loop_score = detect_loop_from_history(state.history)
    state.loop_score = loop_score

    if predicted_label == "handoff_signal" or handoff_signal:
        state.human_signal_detected = True

    return predicted_label, handoff_offer, handoff_signal, is_loop, loop_score


def update_state_for_non_verified_agent(state, bot_message: str, bot_gold_label: str, handoff_signal: bool) -> tuple[str, bool, bool, bool, float]:
    append_bot_turn(state, bot_message, bot_gold_label)

    if handoff_signal or bot_gold_label == "handoff_signal":
        state.human_signal_detected = True

    # non-verified agents do not use explicit loop reasoning
    state.loop_score = 0.0
    return bot_gold_label, False, handoff_signal, False, 0.0


def run_case_with_agent(case: Case, agent_name: str, agent) -> dict:
    simulator = CustomerServiceSimulator()
    state = init_state_from_case(case)

    trace = []
    done = False

    while not done and state.turn_count < case.max_turns:
        agent_message, action = agent.next_action(case, state)

        append_user_agent_turn(state, agent_message, action)

        if action == "push_for_human":
            state.escalation_attempts += 1

        trace.append(
            {
                "speaker": "user_agent",
                "message": agent_message,
                "action": action,
                "turn_count_before_bot": state.turn_count,
                "escalation_attempts": state.escalation_attempts,
                "loop_score": state.loop_score,
            }
        )

        if action == "alert_user_takeover":
            state.user_alerted = True
            done = True
            break

        response = simulator.step(
            case=case,
            conversation_state=state,
            agent_message=agent_message,
        )

        if agent_name == "verified":
            predicted_label, handoff_offer, handoff_signal, is_loop, loop_score = update_state_for_verified_agent(
                state, response.bot_message
            )
        else:
            predicted_label, handoff_offer, handoff_signal, is_loop, loop_score = update_state_for_non_verified_agent(
                state, response.bot_message, response.bot_gold_label, response.handoff_signal
            )

        trace.append(
            {
                "speaker": "bot",
                "message": response.bot_message,
                "gold_label": response.bot_gold_label,
                "predicted_label": predicted_label,
                "handoff_offer": handoff_offer,
                "handoff_signal": handoff_signal,
                "loop": is_loop,
                "loop_score": loop_score,
            }
        )

        if response.done:
            done = True

    record = {
        "agent_name": agent_name,
        "case_id": case.case_id,
        "issue_type": case.issue_type,
        "severity": case.severity,
        "bot_profile": case.bot_profile,
        "turn_count": state.turn_count,
        "last_bot_label": state.last_bot_label,
        "human_signal_detected": state.human_signal_detected,
        "user_alerted": state.user_alerted,
        "escalation_attempts": state.escalation_attempts,
        "loop_score": state.loop_score,
        "escalation_success": state.human_signal_detected,
        "trace": trace,
    }

    return record


def save_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    cases = load_cases("data/cases.json")
    agents = build_agents()

    all_results = {}
    all_metrics = {}

    for agent_name, agent in agents.items():
        print("=" * 80)
        print(f"Running evaluation for agent: {agent_name}")
        print("=" * 80)

        records = []
        for case in cases:
            record = run_case_with_agent(case, agent_name, agent)
            records.append(record)

            print(
                f"{agent_name:>8} | case={record['case_id']} | "
                f"success={record['escalation_success']} | "
                f"turns={record['turn_count']} | "
                f"user_alerted={record['user_alerted']} | "
                f"human_signal_detected={record['human_signal_detected']}"
            )

        metrics = summarize_metrics(records)

        all_results[agent_name] = records
        all_metrics[agent_name] = metrics

        print("-" * 80)
        for key, value in metrics.items():
            print(f"{key}: {value}")
        print()

    save_json(RESULTS_DIR / "eval_results.json", all_results)
    save_json(RESULTS_DIR / "eval_metrics.json", all_metrics)

    print("=" * 80)
    print("Evaluation finished.")
    print("Saved:")
    print("- results/eval_results.json")
    print("- results/eval_metrics.json")
    print("=" * 80)


if __name__ == "__main__":
    main()