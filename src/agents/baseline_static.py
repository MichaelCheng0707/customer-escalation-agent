from src.core.schemas import Case, ConversationState


class BaselineStaticAgent:
    """
    The simplest baseline agent.
    It does not interpret the bot's response and does not use verification.
    It follows a fixed strategy based only on turn_count.
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

        if state.turn_count == 0:
            return case.initial_user_message, "continue"

        if state.turn_count == 1:
            return (
                "This is a serious issue and I need to speak to a human representative.",
                "push_for_human",
            )

        return (
            "Please connect me to a live agent now.",
            "push_for_human",
        )