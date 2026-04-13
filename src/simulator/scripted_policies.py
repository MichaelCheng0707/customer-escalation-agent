from src.core.schemas import Case, ConversationState, SimulatorResponse


def contains_human_request(text: str) -> bool:
    text = text.lower()
    keywords = [
        "human",
        "representative",
        "real person",
        "live agent",
        "specialist",
        "agent",
    ]
    return any(keyword in text for keyword in keywords)


def contains_strong_urgency(text: str) -> bool:
    text = text.lower()
    keywords = [
        "urgent",
        "serious",
        "charged twice",
        "duplicate charge",
        "expensive",
        "high value",
        "locked",
        "cannot access",
        "missing order",
    ]
    return any(keyword in text for keyword in keywords)


def clean_handoff_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    human_requested = contains_human_request(agent_message)
    urgent = contains_strong_urgency(agent_message)

    if state.turn_count == 0:
        return SimulatorResponse(
            bot_message="I understand the issue. I can help, or connect you to a representative if needed.",
            bot_gold_label="understood_actionable",
            handoff_signal=False,
            done=False,
        )

    if human_requested or urgent:
        return SimulatorResponse(
            bot_message="I’m transferring you to a live agent now. Please wait while I connect you.",
            bot_gold_label="handoff_signal",
            handoff_signal=True,
            done=True,
        )

    return SimulatorResponse(
        bot_message="Could you share more detail so I can assist you better?",
        bot_gold_label="request_more_info",
        handoff_signal=False,
        done=False,
    )


def ambiguous_offer_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    human_requested = contains_human_request(agent_message)

    if state.turn_count == 0:
        return SimulatorResponse(
            bot_message="I can connect you to a support representative if needed, but first let me check what options are available.",
            bot_gold_label="understood_actionable",
            handoff_signal=False,
            done=False,
        )

    if state.turn_count == 1:
        return SimulatorResponse(
            bot_message="A representative may be able to assist further, but I need to gather more context first.",
            bot_gold_label="misunderstood_issue",
            handoff_signal=False,
            done=False,
        )

    if human_requested:
        return SimulatorResponse(
            bot_message="I’m transferring you to a live representative now.",
            bot_gold_label="handoff_signal",
            handoff_signal=True,
            done=True,
        )

    return SimulatorResponse(
        bot_message="Please review our help center for more information.",
        bot_gold_label="generic_template",
        handoff_signal=False,
        done=False,
    )


def repeat_generic_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    human_requested = contains_human_request(agent_message)

    if state.turn_count == 0:
        return SimulatorResponse(
            bot_message="Please review our support center for more information.",
            bot_gold_label="generic_template",
            handoff_signal=False,
            done=False,
        )

    if state.turn_count == 1:
        return SimulatorResponse(
            bot_message="Please review our help page for standard support options.",
            bot_gold_label="generic_template",
            handoff_signal=False,
            done=False,
        )

    if state.turn_count == 2:
        return SimulatorResponse(
            bot_message="Please review our support resources for additional guidance.",
            bot_gold_label="generic_template",
            handoff_signal=False,
            done=False,
        )

    if human_requested:
        return SimulatorResponse(
            bot_message="I’m transferring you to a live agent now.",
            bot_gold_label="handoff_signal",
            handoff_signal=True,
            done=True,
        )

    return SimulatorResponse(
        bot_message="Please review our support resources for additional guidance.",
        bot_gold_label="generic_template",
        handoff_signal=False,
        done=False,
    )


def self_serve_success_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    # First turn: provide a valid self-serve solution, but do not end immediately.
    # This gives the agent a chance to either accept the self-serve path
    # or over-escalate unnecessarily.
    if state.turn_count == 0:
        if case.issue_type == "billing_dispute":
            return SimulatorResponse(
                bot_message="You can review the full billing breakdown in the account billing page and compare the transaction details there.",
                bot_gold_label="self_serve_solution",
                handoff_signal=False,
                done=False,
            )

        if case.issue_type == "missing_order":
            return SimulatorResponse(
                bot_message="You can use the order tracking link and delivery status page to resolve this without escalation.",
                bot_gold_label="self_serve_solution",
                handoff_signal=False,
                done=False,
            )

        return SimulatorResponse(
            bot_message="You can reset your password through the secure recovery flow. That should resolve the issue without escalation.",
            bot_gold_label="self_serve_solution",
            handoff_signal=False,
            done=False,
        )

    # Second turn: if the agent still pushes for human, the bot keeps saying
    # self-serve is sufficient. This lets evaluation detect over-escalation.
    return SimulatorResponse(
        bot_message="The self-serve path I provided should be enough to resolve this issue.",
        bot_gold_label="self_serve_solution",
        handoff_signal=False,
        done=True,
    )


def missing_info_first_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    # First turn: request missing information, but do not end immediately.
    # This gives the agent a chance to choose request_more_info on the next turn.
    if state.turn_count == 0:
        if case.issue_type == "missing_order":
            return SimulatorResponse(
                bot_message="I can help, but I need the order number before I can proceed.",
                bot_gold_label="request_more_info",
                handoff_signal=False,
                done=False,
            )

        return SimulatorResponse(
            bot_message="I can help, but I need more account or identity details before I can proceed.",
            bot_gold_label="request_more_info",
            handoff_signal=False,
            done=False,
        )

    # Second turn: repeat the need for missing information.
    return SimulatorResponse(
        bot_message="I still need the missing information before I can continue.",
        bot_gold_label="request_more_info",
        handoff_signal=False,
        done=True,
    )


def dead_end_loop_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    if state.turn_count == 0:
        return SimulatorResponse(
            bot_message="Please review our help center for more information.",
            bot_gold_label="generic_template",
            handoff_signal=False,
            done=False,
        )

    if state.turn_count == 1:
        return SimulatorResponse(
            bot_message="Please review our support resources for additional guidance.",
            bot_gold_label="generic_template",
            handoff_signal=False,
            done=False,
        )

    if state.turn_count == 2:
        return SimulatorResponse(
            bot_message="At this time, no further escalation options are available through this channel.",
            bot_gold_label="dead_end",
            handoff_signal=False,
            done=False,
        )

    return SimulatorResponse(
        bot_message="No further progress can be made through this automated channel.",
        bot_gold_label="dead_end",
        handoff_signal=False,
        done=False,
    )


def cooperative_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    tag = case.bot_behavior_tag

    if tag == "clean_handoff":
        return clean_handoff_policy(case, state, agent_message)
    if tag == "self_serve_success":
        return self_serve_success_policy(case, state, agent_message)
    if tag == "missing_info_first":
        return missing_info_first_policy(case, state, agent_message)

    return clean_handoff_policy(case, state, agent_message)


def deflective_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    tag = case.bot_behavior_tag

    if tag == "ambiguous_offer":
        return ambiguous_offer_policy(case, state, agent_message)
    if tag == "repeat_generic":
        return repeat_generic_policy(case, state, agent_message)
    if tag == "dead_end_loop":
        return dead_end_loop_policy(case, state, agent_message)

    return clean_handoff_policy(case, state, agent_message)