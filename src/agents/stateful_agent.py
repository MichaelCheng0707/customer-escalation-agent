from src.core.schemas import Case, ConversationState


class StatefulAgentWithoutVerification:
    """
    A true middle baseline.

    This agent uses coarse dialogue state:
    - turn count
    - severity
    - escalation attempts
    - confirmed human handoff state
    - a small subset of coarse bot labels

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

        # First turn: present the original issue clearly.
        if state.turn_count == 0:
            return case.initial_user_message, "continue"

        # [MODIFIED]
        # Only react to a confirmed handoff signal.
        # This is a coarse and reasonable state cue.
        if state.human_signal_detected or state.last_bot_label == "handoff_signal":
            return (
                "A human agent is joining now. Please take over the conversation.",
                "alert_user_takeover",
            )

        # [MODIFIED]
        # Use only coarse bot categories for escalation behavior.
        if state.last_bot_label in {"generic_template", "misunderstood_issue"}:
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

        # [MODIFIED]
        # If the bot seems generally helpful, move one step toward escalation,
        # but do not try to interpret richer meanings like self-serve or missing-info.
        if state.last_bot_label == "understood_actionable":
            return (
                "Thank you. Please connect me to a human representative if this cannot be resolved here.",
                "push_for_human",
            )

        # [MODIFIED]
        # Deliberately do NOT special-case:
        # - request_more_info
        # - self_serve_solution
        # - dead_end
        # - handoff_offer
        #
        # Those richer distinctions belong to the verified agent.
        # This keeps the stateful baseline meaningfully weaker.

        # Safe fallback.
        return (
            "Please connect me to a human representative.",
            "push_for_human",
        )