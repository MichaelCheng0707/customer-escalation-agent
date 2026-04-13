from src.core.schemas import Case, ConversationState


class VerifiedAgent:
    """
    A verified agent that uses explicit tools and structured state
    to make escalation decisions more carefully than the baselines.
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

        # Confirmed human handoff
        if state.human_signal_detected or state.last_bot_label == "handoff_signal":
            return (
                "A human agent is joining now. Please take over the conversation.",
                "alert_user_takeover",
            )

        # First turn
        if state.turn_count == 0:
            return case.initial_user_message, "continue"

        # [MODIFIED]
        # If the bot explicitly asks for more information,
        # the agent should request more information from the user.
        if state.last_bot_label == "request_more_info":
            return (
                "I need more information from the user before I can continue.",
                "request_more_info",
            )

        # [MODIFIED]
        # If the bot provides a valid self-serve path,
        # the agent should continue rather than escalate.
        if state.last_bot_label == "self_serve_solution":
            return (
                "The bot has already provided a workable path, so escalation is not necessary.",
                "continue",
            )

        # [MODIFIED]
        # A true dead-end signal should trigger stop_dead_end immediately.
        if state.last_bot_label == "dead_end":
            return (
                "This conversation has reached a dead end. Please stop this channel and take over manually if needed.",
                "stop_dead_end",
            )

        # [MODIFIED]
        # A generic loop should not be treated as dead-end too early.
        # Give confirmed_handoff-style cases more chances to escalate.
        if state.loop_score >= 1.0 and state.last_bot_label in {"generic_template", "misunderstood_issue"}:
            if state.escalation_attempts >= 3:
                return (
                    "This conversation has reached a dead end. Please stop this channel and take over manually if needed.",
                    "stop_dead_end",
                )
            return (
                "The automated guidance is not solving the problem. Please connect me to a human representative.",
                "push_for_human",
            )

        # If the bot only offers escalation, keep pushing.
        if state.last_bot_label == "handoff_offer":
            return (
                "Yes, please connect me to a human representative now.",
                "push_for_human",
            )

        # Generic or misunderstood responses should trigger escalation.
        if state.last_bot_label in {"generic_template", "misunderstood_issue"}:
            return (
                "The automated guidance is not solving the problem. Please connect me to a human representative.",
                "push_for_human",
            )

        # Useful but not yet escalated
        if state.last_bot_label == "understood_actionable":
            return (
                "Thank you. Please connect me to a human representative now.",
                "push_for_human",
            )

        # Safe fallback
        return (
            "Please connect me to a human representative.",
            "push_for_human",
        )