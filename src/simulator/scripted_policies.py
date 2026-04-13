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
        if case.issue_type == "billing_dispute":
            return SimulatorResponse(
                bot_message="I understand the billing issue. I can review it, or connect you to a representative if needed.",
                bot_gold_label="understood_actionable",
                handoff_signal=False,
                done=False,
            )
        elif case.issue_type == "missing_order":
            return SimulatorResponse(
                bot_message="I’m sorry your order has not arrived. I can help check delivery issues, or connect you to a support representative.",
                bot_gold_label="understood_actionable",
                handoff_signal=False,
                done=False,
            )
        else:
            return SimulatorResponse(
                bot_message="I understand your account access problem. I can provide recovery guidance, or connect you to a representative.",
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


def false_progress_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    human_requested = contains_human_request(agent_message)

    if state.turn_count == 0:
        return SimulatorResponse(
            bot_message="I understand your concern and I will help guide you through some next steps.",
            bot_gold_label="understood_actionable",
            handoff_signal=False,
            done=False,
        )

    if state.turn_count == 1:
        return SimulatorResponse(
            bot_message="Let me help you with that by providing some troubleshooting steps first.",
            bot_gold_label="misunderstood_issue",
            handoff_signal=False,
            done=False,
        )

    if state.turn_count == 2 and not human_requested:
        return SimulatorResponse(
            bot_message="I can continue assisting you with standard support options.",
            bot_gold_label="misunderstood_issue",
            handoff_signal=False,
            done=False,
        )

    return SimulatorResponse(
        bot_message="I’m transferring you to a live representative now.",
        bot_gold_label="handoff_signal",
        handoff_signal=True,
        done=True,
    )


def delayed_handoff_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    human_requested = contains_human_request(agent_message)
    urgent = contains_strong_urgency(agent_message)

    if state.turn_count == 0:
        return SimulatorResponse(
            bot_message="Please review our help center for more information.",
            bot_gold_label="generic_template",
            handoff_signal=False,
            done=False,
        )

    if state.turn_count == 1:
        return SimulatorResponse(
            bot_message="Before I connect you to an agent, please review these troubleshooting steps.",
            bot_gold_label="misunderstood_issue",
            handoff_signal=False,
            done=False,
        )

    if state.turn_count == 2:
        if human_requested or urgent:
            return SimulatorResponse(
                bot_message="I’m transferring you to a live representative now.",
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

    return SimulatorResponse(
        bot_message="I’m transferring you to a live representative now.",
        bot_gold_label="handoff_signal",
        handoff_signal=True,
        done=True,
    )


def cooperative_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    return clean_handoff_policy(case, state, agent_message)


def deflective_policy(case: Case, state: ConversationState, agent_message: str) -> SimulatorResponse:
    tag = case.bot_behavior_tag

    if tag == "ambiguous_offer":
        return ambiguous_offer_policy(case, state, agent_message)
    if tag == "repeat_generic":
        return repeat_generic_policy(case, state, agent_message)
    if tag == "false_progress":
        return false_progress_policy(case, state, agent_message)
    if tag == "delayed_handoff":
        return delayed_handoff_policy(case, state, agent_message)

    return clean_handoff_policy(case, state, agent_message)