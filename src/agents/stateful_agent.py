from src.core.schemas import Case, ConversationState


class StatefulAgentWithoutVerification:
    """
    A true middle baseline.

    This agent uses coarse dialogue state:
    - turn count
    - severity
    - escalation attempts
    - confirmed human handoff state
    - a coarse bot mode

    It does NOT rely on rich semantic labels such as:
    - self_serve_solution
    - request_more_info
    - dead_end
    - handoff_offer

    Those richer distinctions are reserved for the verified agent.
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

        # First turn
        if state.turn_count == 0:
            return case.initial_user_message, "continue"

        # [MODIFIED]
        # If a confirmed human handoff has already been detected,
        # let the user take over.
        if state.human_signal_detected or state.bot_mode == "handoff_confirmed":
            return (
                "A human agent is joining now. Please take over the conversation.",
                "alert_user_takeover",
            )

        # [MODIFIED]
        # Helpful bot mode means the bot is at least providing
        # something useful-looking. The stateful baseline becomes
        # slightly less aggressive than the static baseline here,
        # but it still does not know whether this is self-serve,
        # missing-info, or another finer-grained category.
        if state.bot_mode == "helpful":
            if state.escalation_attempts == 0:
                return (
                    "Thank you. Please continue helping with this issue, "
                    "or connect me to a human representative if needed.",
                    "rephrase",
                )

            return (
                "Please connect me to a human representative.",
                "push_for_human",
            )

        # [MODIFIED]
        # Blocking bot mode means the conversation is not productively moving.
        # Here the stateful baseline becomes more aggressive.
        if state.bot_mode == "blocking":
            if case.severity == "high":
                if state.escalation_attempts == 0:
                    return (
                        "This is a serious issue involving a high-impact problem. "
                        "I need to speak to a human representative.",
                        "push_for_human",
                    )

                if state.escalation_attempts == 1:
                    return (
                        "I still need a live human representative. "
                        "This issue has not been resolved through the automated responses.",
                        "rephrase",
                    )

                return (
                    "Please connect me to a live agent now.",
                    "alert_user_takeover",
                )

            if state.escalation_attempts == 0:
                return (
                    "I need help with this issue. "
                    "If it cannot be resolved here, please connect me to a human representative.",
                    "push_for_human",
                )

            if state.escalation_attempts == 1:
                return (
                    "This issue still requires human assistance. "
                    "Please connect me to a live support agent.",
                    "rephrase",
                )

            return (
                "Please connect me to a live agent now.",
                "alert_user_takeover",
            )

        # Safe fallback
        return (
            "Please connect me to a human representative.",
            "push_for_human",
        )