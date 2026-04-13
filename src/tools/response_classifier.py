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

    # Highest priority: confirmed human handoff
    if detect_handoff_signal(bot_message):
        return "handoff_signal"

    # Second priority: possible but not yet confirmed handoff
    if detect_handoff_offer(bot_message):
        return "handoff_offer"

    request_more_info_patterns = [
        "could you please provide",
        "please provide",
        "provide a little more detail",
        "provide more detail",
        "what is your",
        "can you share",
    ]
    if any(pattern in text for pattern in request_more_info_patterns):
        return "request_more_info"

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
    ]
    if any(pattern in text for pattern in generic_patterns):
        return "generic_template"

    understood_actionable_patterns = [
        "i can help review your billing issue",
        "i can help check common delivery issues",
        "i can provide account recovery steps",
        "i'm sorry your order has not arrived",
        "i'm sorry you are having trouble accessing your account",
    ]
    if any(pattern in text for pattern in understood_actionable_patterns):
        return "understood_actionable"

    return "generic_template"