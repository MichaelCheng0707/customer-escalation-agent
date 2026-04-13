from src.core.schemas import Case, ConversationState


class StatefulAgentWithoutVerification:
    """
    A stateful agent baseline.
    It uses conversation state such as turn count, severity,
    and escalation attempts, but it does not perform explicit verification.
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

        # First turn: present the original issue clearly.
        if state.turn_count == 0:
            return case.initial_user_message, "continue"

        # If the issue is high severity, escalate earlier.
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

        # For medium or low severity, be slightly less aggressive at first.
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