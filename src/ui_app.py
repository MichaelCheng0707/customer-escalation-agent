import os
import time

import streamlit as st
from dotenv import load_dotenv

from src.evaluation.run_eval import build_agents, load_cases
from src.replay import load_case_by_id, run_case_replay


CASES_PATH = "data/cases.json"
GPT_BACKEND_MODES = ["scripted", "gpt"]
GPT_PERSONAS = ["cooperative", "cooperative_open"]

load_dotenv()


@st.cache_data
def cached_cases():
    return load_cases(CASES_PATH)


@st.cache_data
def cached_scripted_record(agent_name: str, case_id: str) -> dict:
    case = load_case_by_id(case_id)
    return run_case_replay(case=case, agent_name=agent_name, backend_mode="scripted")


def gpt_record_state_key(agent_name: str, case_id: str, persona: str, model: str) -> str:
    return f"gpt::{agent_name}::{case_id}::{persona}::{model}"


def init_session() -> None:
    defaults = {
        "step_index": 0,
        "playing": False,
        "last_agent": None,
        "last_case": None,
        "last_backend_mode": None,
        "last_persona": None,
        "last_model": None,
        "gpt_records": {},
        "gpt_active_record_key": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_replay(
    agent_name: str,
    case_id: str,
    backend_mode: str,
    persona: str | None,
    model: str | None,
) -> None:
    st.session_state.step_index = 0
    st.session_state.playing = False
    st.session_state.last_agent = agent_name
    st.session_state.last_case = case_id
    st.session_state.last_backend_mode = backend_mode
    st.session_state.last_persona = persona
    st.session_state.last_model = model


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
    details = [
        f"Case {record['case_id']}",
        record["issue_type"],
        f"severity={record['severity']}",
        f"difficulty={record['difficulty']}",
        f"target={record['target_outcome']}",
        f"backend={record.get('backend_mode', 'scripted')}",
    ]
    if record.get("gpt_persona"):
        details.append(f"persona={record['gpt_persona']}")
    if record.get("gpt_model"):
        details.append(f"model={record['gpt_model']}")
    st.caption(
        " | ".join(
            details
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


def render_initial_case_message(case_id: str) -> None:
    case = load_case_by_id(case_id)
    with st.chat_message("user"):
        st.markdown(case.initial_user_message)
        st.caption("initial case context")


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
    metadata = step.get("backend_metadata")
    if metadata:
        render_badge("backend_metadata", metadata)


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
    st.caption("Step-by-step replay for scripted and GPT customer-service backends.")

    cases = cached_cases()
    case_ids = [case.case_id for case in cases]
    agent_names = list(build_agents().keys())
    default_model = os.getenv("MODEL_NAME", "gpt-5-mini")

    left, middle, right = st.columns([1.0, 2.2, 1.15], gap="large")

    with left:
        st.subheader("Settings")
        backend_mode = st.selectbox("Customer Service Backend", GPT_BACKEND_MODES, index=0)
        agent_name = st.selectbox("Agent", agent_names, index=2)
        case_id = st.selectbox("Case", case_ids)
        gpt_persona = None
        gpt_model = None
        if backend_mode == "gpt":
            gpt_persona = st.selectbox("GPT Persona", GPT_PERSONAS, index=0)
            gpt_model = st.text_input("OpenAI Model", value=default_model)
        speed = st.slider("Playback speed", 0.25, 3.0, 1.25, 0.25, help="Seconds between steps.")

        if (
            st.session_state.last_agent != agent_name
            or st.session_state.last_case != case_id
            or st.session_state.last_backend_mode != backend_mode
            or st.session_state.last_persona != gpt_persona
            or st.session_state.last_model != gpt_model
        ):
            reset_replay(agent_name, case_id, backend_mode, gpt_persona, gpt_model)
            if backend_mode == "gpt":
                st.session_state.gpt_active_record_key = None

        if backend_mode == "scripted":
            record = cached_scripted_record(agent_name, case_id)
        else:
            record_key = gpt_record_state_key(agent_name, case_id, gpt_persona or "", gpt_model or "")
            record = None
            if st.button("Run the Case", use_container_width=True):
                with st.spinner("Generating GPT customer service replay..."):
                    record = run_case_replay(
                        case=load_case_by_id(case_id),
                        agent_name=agent_name,
                        backend_mode="gpt",
                        gpt_model=gpt_model,
                        gpt_persona=gpt_persona,
                    )
                    st.session_state.gpt_records[record_key] = record
                    st.session_state.gpt_active_record_key = record_key
                    st.session_state.step_index = 0
                    st.session_state.playing = False

            active_key = st.session_state.gpt_active_record_key
            if active_key == record_key and record_key in st.session_state.gpt_records:
                record = st.session_state.gpt_records[record_key]
        trace = record["trace"] if record else []

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
            reset_replay(agent_name, case_id, backend_mode, gpt_persona, gpt_model)

        if backend_mode == "gpt" and record and st.button("Regenerate GPT Replay", use_container_width=True):
            st.session_state.playing = False
            if record_key in st.session_state.gpt_records:
                del st.session_state.gpt_records[record_key]
            st.session_state.gpt_active_record_key = None
            reset_replay(agent_name, case_id, backend_mode, gpt_persona, gpt_model)
            st.rerun()

        st.progress((st.session_state.step_index + 1) / max(len(trace), 1) if trace else 0)
        st.caption(f"Step {min(st.session_state.step_index + 1, max(len(trace), 1))} of {len(trace)}")
        if backend_mode == "gpt":
            if record:
                st.info("GPT mode is non-deterministic. Replay is fixed only after a trace has been generated.")
            else:
                st.info("Adjust the GPT settings, then click `Run the Case` to generate a replay.")

    with middle:
        if record:
            render_case_header(record)
        else:
            case = load_case_by_id(case_id)
            st.caption(
                " | ".join(
                    [
                        f"Case {case.case_id}",
                        case.issue_type,
                        f"severity={case.severity}",
                        f"difficulty={case.difficulty}",
                        f"target={case.target_outcome}",
                        f"backend={backend_mode}",
                    ]
                )
            )
        st.subheader("Conversation")
        if record:
            render_chat(trace)
        else:
            render_initial_case_message(case_id)
            st.info("No GPT replay yet. Click `Run the Case` after choosing the backend, case, persona, and model.")

    with right:
        render_debug_panel(trace, current_step(trace))

    st.divider()
    if record:
        render_final_summary(record)

    if st.session_state.playing and record:
        if st.session_state.step_index < len(trace) - 1:
            time.sleep(speed)
            st.session_state.step_index += 1
            st.rerun()
        else:
            st.session_state.playing = False


if __name__ == "__main__":
    main()
