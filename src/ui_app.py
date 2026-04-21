import time

import streamlit as st

from src.evaluation.run_eval import build_agents, load_cases, run_case_with_agent


CASES_PATH = "data/cases.json"


@st.cache_data
def cached_cases():
    return load_cases(CASES_PATH)


@st.cache_data
def cached_record(agent_name: str, case_id: str) -> dict:
    cases = cached_cases()
    case = next(case for case in cases if case.case_id == case_id)
    agent = build_agents()[agent_name]
    return run_case_with_agent(case, agent_name, agent)


def init_session() -> None:
    defaults = {
        "step_index": 0,
        "playing": False,
        "last_agent": None,
        "last_case": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_replay(agent_name: str, case_id: str) -> None:
    st.session_state.step_index = 0
    st.session_state.playing = False
    st.session_state.last_agent = agent_name
    st.session_state.last_case = case_id


def visible_steps(trace: list[dict]) -> list[dict]:
    max_index = min(st.session_state.step_index, len(trace) - 1)
    if max_index < 0:
        return []
    return trace[: max_index + 1]


def current_step(trace: list[dict]) -> dict | None:
    if not trace:
        return None
    index = min(st.session_state.step_index, len(trace) - 1)
    return trace[index]


def state_at_current_step(trace: list[dict]) -> dict:
    steps = visible_steps(trace)
    escalation_attempts = sum(
        1
        for step in steps
        if step["speaker"] == "user_agent" and step.get("action") == "push_for_human"
    )
    human_signal_detected = any(
        step["speaker"] == "bot" and bool(step.get("handoff_signal"))
        for step in steps
    )
    user_alerted = any(
        step["speaker"] == "user_agent" and step.get("action") == "alert_user_takeover"
        for step in steps
    )
    loop_score = 0.0
    for step in steps:
        if "loop_score" in step:
            loop_score = step["loop_score"]

    return {
        "escalation_attempts": escalation_attempts,
        "human_signal_detected": human_signal_detected,
        "user_alerted": user_alerted,
        "loop_score": loop_score,
    }


def render_badge(label: str, value) -> None:
    st.markdown(f"**{label}**")
    st.code(str(value), language=None)


def render_case_header(record: dict) -> None:
    st.caption(
        " | ".join(
            [
                f"Case {record['case_id']}",
                record["issue_type"],
                f"severity={record['severity']}",
                f"difficulty={record['difficulty']}",
                f"target={record['target_outcome']}",
            ]
        )
    )


def render_chat(trace: list[dict]) -> None:
    for step in visible_steps(trace):
        if step["speaker"] == "user_agent":
            with st.chat_message("user"):
                st.markdown(step["message"])
                st.caption(f"action: `{step.get('action')}`")
        else:
            with st.chat_message("assistant"):
                st.markdown(step["message"])
                st.caption(
                    " | ".join(
                        [
                            f"predicted_label: `{step.get('predicted_label')}`",
                            f"gold_label: `{step.get('gold_label')}`",
                        ]
                    )
                )


def render_debug_panel(trace: list[dict], step: dict | None) -> None:
    st.subheader("Debug")
    if step is None:
        st.info("No step selected.")
        return

    current_state = state_at_current_step(trace)

    render_badge("speaker", step.get("speaker"))
    render_badge("action", step.get("action", "-"))
    render_badge("predicted_label", step.get("predicted_label", "-"))
    render_badge("gold_label", step.get("gold_label", "-"))
    render_badge("handoff_signal", step.get("handoff_signal", "-"))
    render_badge("handoff_offer", step.get("handoff_offer", "-"))
    render_badge("loop", step.get("loop", "-"))
    render_badge("loop_score", current_state["loop_score"])
    render_badge("human_signal_detected", current_state["human_signal_detected"])
    render_badge("user_alerted", current_state["user_alerted"])
    render_badge("escalation_attempts", current_state["escalation_attempts"])


def render_final_summary(record: dict) -> None:
    st.subheader("Final Summary")
    cols = st.columns(4)
    summary_items = [
        ("outcome_correct", record["outcome_correct"]),
        ("over_escalated", record["over_escalated"]),
        ("missing_info_violation", record["missing_info_violation"]),
        ("premature_takeover", record["premature_takeover"]),
    ]
    for col, (label, value) in zip(cols, summary_items):
        col.metric(label, str(value))


def main() -> None:
    st.set_page_config(
        page_title="Escalation Agent Replay",
        layout="wide",
    )
    init_session()

    st.title("Escalation Agent Replay")
    st.caption("Deterministic step-by-step simulation for the static, stateful, and verified agents.")

    cases = cached_cases()
    case_ids = [case.case_id for case in cases]
    agent_names = list(build_agents().keys())

    left, middle, right = st.columns([1.0, 2.2, 1.15], gap="large")

    with left:
        st.subheader("Settings")
        agent_name = st.selectbox("Agent", agent_names, index=2)
        case_id = st.selectbox("Case", case_ids)
        speed = st.slider("Playback speed", 0.25, 3.0, 1.25, 0.25, help="Seconds between steps.")

        if (
            st.session_state.last_agent != agent_name
            or st.session_state.last_case != case_id
        ):
            reset_replay(agent_name, case_id)

        record = cached_record(agent_name, case_id)
        trace = record["trace"]

        col_a, col_b = st.columns(2)
        if col_a.button("Play", use_container_width=True):
            st.session_state.playing = True
        if col_b.button("Pause", use_container_width=True):
            st.session_state.playing = False

        col_c, col_d = st.columns(2)
        if col_c.button("Next Step", use_container_width=True):
            st.session_state.playing = False
            st.session_state.step_index = min(st.session_state.step_index + 1, len(trace) - 1)
        if col_d.button("Reset", use_container_width=True):
            reset_replay(agent_name, case_id)

        st.progress((st.session_state.step_index + 1) / max(len(trace), 1))
        st.caption(f"Step {st.session_state.step_index + 1} of {len(trace)}")

    with middle:
        render_case_header(record)
        st.subheader("Conversation")
        render_chat(trace)

    with right:
        render_debug_panel(trace, current_step(trace))

    st.divider()
    render_final_summary(record)

    if st.session_state.playing:
        if st.session_state.step_index < len(trace) - 1:
            time.sleep(speed)
            st.session_state.step_index += 1
            st.rerun()
        else:
            st.session_state.playing = False


if __name__ == "__main__":
    main()
