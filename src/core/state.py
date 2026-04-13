from src.core.schemas import Case, ConversationState, TurnRecord, BotLabel, AgentAction


def init_state_from_case(case: Case) -> ConversationState:
    return ConversationState(
        case_id=case.case_id,
        issue_type=case.issue_type,
        severity=case.severity,
        goal=case.user_goal,
    )


def append_user_agent_turn(
    state: ConversationState,
    message: str,
    action_taken: AgentAction | None = None,
) -> None:
    state.history.append(
        TurnRecord(
            speaker="user_agent",
            message=message,
            action_taken=action_taken,
        )
    )


def append_bot_turn(
    state: ConversationState,
    message: str,
    label: BotLabel,
) -> None:
    state.history.append(
        TurnRecord(
            speaker="bot",
            message=message,
            predicted_label=label,
        )
    )
    state.last_bot_label = label
    state.turn_count += 1