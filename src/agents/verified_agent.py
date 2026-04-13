from src.core.schemas import Case, ConversationState


class VerifiedAgent:
    """
    A verified agent that uses explicit tools to classify bot responses,
    detect human handoff signals, and identify non-productive loops.
    """

    def next_action(
        self,
        case: Case,
        state: ConversationState,
    ) -> tuple[str, str]:
        """
        Returns:
        - message_to_bot
        - action_name
        """

        # If a confirmed human handoff signal has been detected,
        # the system should stop and alert the user.
        if state.human_signal_detected or state.last_bot_label == "handoff_signal":
            return (
                "A human agent is joining now. Please take over the conversation.",
                "alert_user_takeover",
            )

        # First turn: present the original issue.
        if state.turn_count == 0:
            return case.initial_user_message, "continue"

        # If the bot only offered escalation but did not confirm it,
        # keep pushing for the handoff rather than alerting too early.
        if state.last_bot_label == "handoff_offer":
            return (
                "Yes, please connect me to a human representative now.",
                "push_for_human",
            )

        # If the bot is clearly generic or misunderstood the issue,
        # escalate more aggressively.
        if state.last_bot_label in {"generic_template", "misunderstood_issue"}:
            if state.loop_score >= 1.0:
                if state.escalation_attempts == 0:
                    return (
                        "The automated guidance is not solving the problem. "
                        "Please connect me to a human representative.",
                        "push_for_human",
                    )

                if state.escalation_attempts == 1:
                    return (
                        "This issue still has not been resolved. "
                        "I need a live human representative now.",
                        "push_for_human",
                    )

                return (
                    "The conversation is no longer progressing. "
                    "Please take over the conversation now.",
                    "alert_user_takeover",
                )

            if state.escalation_attempts == 0:
                return (
                    "The automated guidance is not solving the problem. "
                    "Please connect me to a human representative.",
                    "push_for_human",
                )

            return (
                "This issue still requires human assistance. "
                "Please connect me to a live support agent.",
                "rephrase",
            )

        # If the bot response is useful but not yet a confirmed handoff,
        # move the conversation one step closer to human escalation.
        if state.last_bot_label == "understood_actionable":
            return (
                "Thank you. Please connect me to a human representative now.",
                "push_for_human",
            )

        if state.last_bot_label == "request_more_info":
            return (
                "I can provide more information, but I still need to speak to a human representative.",
                "rephrase",
            )

        # Safe fallback.
        return (
            "Please connect me to a human representative.",
            "push_for_human",
        )