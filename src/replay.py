from __future__ import annotations

from src.backends.customer_service import (
    CustomerServiceBackend,
    GPTCustomerServiceBackend,
    ScriptedCustomerServiceBackend,
)
from src.core.schemas import Case
from src.core.state import append_bot_turn, append_user_agent_turn, init_state_from_case
from src.evaluation.run_eval import (
    build_agents,
    evaluate_case_outcome,
    load_cases,
    map_label_to_bot_mode,
)
from src.tools.handoff_detector import detect_handoff_offer, detect_handoff_signal
from src.tools.loop_detector import detect_loop_from_history
from src.tools.response_classifier import classify_bot_response


CASES_PATH = "data/cases.json"


def load_case_by_id(case_id: str) -> Case:
    cases = load_cases(CASES_PATH)
    return next(case for case in cases if case.case_id == case_id)


def build_backend(backend_mode: str, model: str | None = None, persona: str | None = None) -> CustomerServiceBackend:
    if backend_mode == "scripted":
        return ScriptedCustomerServiceBackend()
    if backend_mode == "gpt":
        if not model:
            raise ValueError("A GPT model name is required for GPT backend mode.")
        if not persona:
            raise ValueError("A GPT persona is required for GPT backend mode.")
        return GPTCustomerServiceBackend(model=model, persona=persona)
    raise ValueError(f"Unsupported backend mode: {backend_mode}")


def update_state_from_predicted_reply(state, bot_message: str) -> tuple[str, bool, bool, bool, float]:
    predicted_label = classify_bot_response(bot_message)
    handoff_offer = detect_handoff_offer(bot_message)
    handoff_signal = detect_handoff_signal(bot_message)

    append_bot_turn(state, bot_message, predicted_label)
    state.bot_mode = map_label_to_bot_mode(predicted_label)

    is_loop, loop_score = detect_loop_from_history(state.history)
    state.loop_score = loop_score

    if predicted_label == "handoff_signal" or handoff_signal:
        state.human_signal_detected = True

    return predicted_label, handoff_offer, handoff_signal, is_loop, loop_score


def run_case_replay(
    case: Case,
    agent_name: str,
    backend_mode: str = "scripted",
    gpt_model: str | None = None,
    gpt_persona: str | None = None,
) -> dict:
    agent = build_agents()[agent_name]
    backend = build_backend(backend_mode, model=gpt_model, persona=gpt_persona)
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

        if action in {"alert_user_takeover", "request_more_info", "stop_dead_end"}:
            if action == "alert_user_takeover":
                state.user_alerted = True
            done = True
            break

        if state.human_signal_detected:
            done = True
            break

        reply = backend.respond(case=case, state=state, agent_message=agent_message)
        predicted_label, handoff_offer, handoff_signal, is_loop, loop_score = update_state_from_predicted_reply(
            state, reply.bot_message
        )

        trace.append(
            {
                "speaker": "bot",
                "message": reply.bot_message,
                "gold_label": reply.bot_gold_label,
                "predicted_label": predicted_label,
                "handoff_offer": handoff_offer,
                "handoff_signal": handoff_signal,
                "loop": is_loop,
                "loop_score": loop_score,
                "backend_metadata": reply.metadata,
            }
        )

        if reply.done and not state.human_signal_detected:
            done = True

    eval_result = evaluate_case_outcome(case, state, trace)
    return {
        "agent_name": agent_name,
        "backend_mode": backend_mode,
        "gpt_model": gpt_model,
        "gpt_persona": gpt_persona,
        "case_id": case.case_id,
        "issue_type": case.issue_type,
        "severity": case.severity,
        "difficulty": case.difficulty,
        "bot_behavior_tag": case.bot_behavior_tag,
        "target_outcome": case.target_outcome,
        "turn_count": state.turn_count,
        "last_bot_label": state.last_bot_label,
        "human_signal_detected": state.human_signal_detected,
        "user_alerted": state.user_alerted,
        "escalation_attempts": state.escalation_attempts,
        "loop_score": state.loop_score,
        "trace": trace,
        **eval_result,
    }
