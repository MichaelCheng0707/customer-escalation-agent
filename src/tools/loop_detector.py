from src.core.schemas import TurnRecord


NON_LOOP_LABELS = {
    "handoff_signal",
    "handoff_offer",
    "understood_actionable",
    "request_more_info",
    "human_present",
    "self_serve_solution",
    "dead_end",
}


LOOP_PRONE_LABELS = {
    "generic_template",
    "misunderstood_issue",
}


def detect_loop_from_history(history: list[TurnRecord]) -> tuple[bool, float]:
    """
    Detects whether the recent bot interaction has entered
    a repetitive non-productive loop.
    """

    bot_turns = [turn for turn in history if turn.speaker == "bot"]

    if len(bot_turns) < 2:
        return False, 0.0

    last_two = bot_turns[-2:]
    labels = [turn.predicted_label for turn in last_two]

    if any(label in NON_LOOP_LABELS for label in labels):
        return False, 0.0

    if all(label in LOOP_PRONE_LABELS for label in labels):
        return True, 1.0

    return False, 0.0