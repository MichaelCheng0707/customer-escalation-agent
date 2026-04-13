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
    ]
    return any(keyword in text for keyword in keywords)


def cooperative_policy(
    case: Case,
    state: ConversationState,
    agent_message: str,
) -> SimulatorResponse:
    human_requested = contains_human_request(agent_message)
    urgent = contains_strong_urgency(agent_message)

    if state.turn_count == 0:
        if case.issue_type == "billing_dispute":
            return SimulatorResponse(
                bot_message=(
                    "I’m sorry to hear about the duplicate charge. "
                    "I can help review your billing issue, or connect you to a representative if needed."
                ),
                bot_gold_label="understood_actionable",
                handoff_signal=False,
                done=False,
            )
        elif case.issue_type == "missing_order":
            return SimulatorResponse(
                bot_message=(
                    "I’m sorry your order has not arrived. "
                    "I can help check common delivery issues, or connect you to a support representative."
                ),
                bot_gold_label="understood_actionable",
                handoff_signal=False,
                done=False,
            )
        else:
            return SimulatorResponse(
                bot_message=(
                    "I’m sorry you are having trouble accessing your account. "
                    "I can provide account recovery steps, or connect you to a support representative."
                ),
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
        bot_message=(
            "Could you please provide a little more detail so I can better assist you before escalation?"
        ),
        bot_gold_label="request_more_info",
        handoff_signal=False,
        done=False,
    )


def deflective_policy(
    case: Case,
    state: ConversationState,
    agent_message: str,
) -> SimulatorResponse:
    human_requested = contains_human_request(agent_message)
    urgent = contains_strong_urgency(agent_message)

    if state.turn_count == 0:
        if case.issue_type == "billing_dispute":
            return SimulatorResponse(
                bot_message=(
                    "For billing concerns, please review our billing FAQ page. "
                    "Many common payment questions are answered there."
                ),
                bot_gold_label="generic_template",
                handoff_signal=False,
                done=False,
            )
        elif case.issue_type == "missing_order":
            return SimulatorResponse(
                bot_message=(
                    "Delivery delays may happen due to logistics conditions. "
                    "Please review our delivery help center for more information."
                ),
                bot_gold_label="generic_template",
                handoff_signal=False,
                done=False,
            )
        else:
            return SimulatorResponse(
                bot_message=(
                    "For login issues, please try resetting your password through the help page."
                ),
                bot_gold_label="generic_template",
                handoff_signal=False,
                done=False,
            )

    if state.turn_count == 1:
        if human_requested and urgent:
            return SimulatorResponse(
                bot_message=(
                    "I understand this issue is important. "
                    "Please wait while I connect you to a support specialist."
                ),
                bot_gold_label="handoff_signal",
                handoff_signal=True,
                done=True,
            )
        elif human_requested:
            return SimulatorResponse(
                bot_message=(
                    "Before I connect you to an agent, please review these troubleshooting steps."
                ),
                bot_gold_label="misunderstood_issue",
                handoff_signal=False,
                done=False,
            )
        else:
            return SimulatorResponse(
                bot_message=(
                    "I’m sorry for the inconvenience. "
                    "Please refer to our help center for standard support options."
                ),
                bot_gold_label="generic_template",
                handoff_signal=False,
                done=False,
            )

    if state.turn_count >= 2:
        if human_requested:
            return SimulatorResponse(
                bot_message="I’m transferring you to a live representative now.",
                bot_gold_label="handoff_signal",
                handoff_signal=True,
                done=True,
            )

        return SimulatorResponse(
            bot_message=(
                "I understand your frustration. "
                "Please review our support resources for additional guidance."
            ),
            bot_gold_label="generic_template",
            handoff_signal=False,
            done=False,
        )