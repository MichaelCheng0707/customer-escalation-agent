from src.tools.handoff_detector import detect_handoff_offer, detect_handoff_signal


def normalize_text(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'")
    return " ".join(text.lower().strip().split())


def classify_bot_response(bot_message: str) -> str:
    """
    Classifies the current bot response into a structured label.
    The classifier is rule-based and intentionally conservative.
    """

    text = normalize_text(bot_message)

    # Confirmed human handoff
    if detect_handoff_signal(bot_message):
        return "handoff_signal"

    # Possible but not yet confirmed handoff
    if detect_handoff_offer(bot_message):
        return "handoff_offer"

    # Explicit self-serve solutions should be recognized as their own class.
    self_serve_solution_patterns = [
        "you can review the full billing breakdown",
        "you can use the order tracking link",
        "you can reset your password through the secure recovery flow",
        "the self-serve path i provided should be enough",
        "resolve this without escalation",
        "that should resolve the issue without escalation",
    ]
    if any(pattern in text for pattern in self_serve_solution_patterns):
        return "self_serve_solution"

    # Explicit requests for missing information should be recognized more broadly.
    request_more_info_patterns = [
        "could you please provide",
        "please provide",
        "provide a little more detail",
        "provide more detail",
        "what is your",
        "can you share",
        "i need the order number before i can proceed",
        "i need more account or identity details before i can proceed",
        "i still need the missing information before i can continue",
        "i need more information before i can proceed",
        "i need more details before i can proceed",
    ]
    if any(pattern in text for pattern in request_more_info_patterns):
        return "request_more_info"

    # Explicit dead-end signals should be recognized as their own class.
    dead_end_patterns = [
        "no further escalation options are available",
        "no further progress can be made through this automated channel",
        "no further progress can be made through this channel",
        "no further escalation options are available through this channel",
        "at this time, no further escalation options are available",
    ]
    if any(pattern in text for pattern in dead_end_patterns):
        return "dead_end"

    misunderstood_patterns = [
        "before i connect you to an agent",
        "before i connect you to a representative",
        "please review these troubleshooting steps",
        "please try resetting your password",
        "review these troubleshooting steps",
    ]
    if any(pattern in text for pattern in misunderstood_patterns):
        return "misunderstood_issue"

    generic_patterns = [
        "billing faq",
        "help center",
        "help page",
        "support resources",
        "standard support options",
        "review our delivery help center",
        "review our billing faq page",
        "support center",
        "help page for standard support options",
    ]
    if any(pattern in text for pattern in generic_patterns):
        return "generic_template"

    understood_actionable_patterns = [
        "i can help review your billing issue",
        "i can help check common delivery issues",
        "i can provide account recovery steps",
        "i'm sorry your order has not arrived",
        "i'm sorry you are having trouble accessing your account",
        "i understand the issue. i can help",
        "i understand the billing issue",
        "i understand your account access problem",
    ]
    if any(pattern in text for pattern in understood_actionable_patterns):
        return "understood_actionable"

    return "generic_template"