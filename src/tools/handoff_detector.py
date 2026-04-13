def normalize_text(text: str) -> str:
    # Normalize curly apostrophes and whitespace
    text = text.replace("’", "'").replace("‘", "'")
    return " ".join(text.lower().strip().split())


def detect_handoff_signal(bot_message: str) -> bool:
    """
    Returns True only for explicit transfer / connection signals
    that strongly indicate a human handoff is happening now.
    """
    text = normalize_text(bot_message)

    strict_signal_patterns = [
        "i'm transferring you to a live agent",
        "i am transferring you to a live agent",
        "i'm transferring you to a live representative",
        "i am transferring you to a live representative",
        "i'm transferring you to a live representative now",
        "i am transferring you to a live representative now",
        "transferring you to a representative now",
        "connecting you to a live representative now",
        "connecting you to a live agent now",
        "connecting you to a support specialist",
        "please wait while i connect you",
        "please wait while i connect you to",
        "a live agent will join shortly",
        "a support specialist will join shortly",
        "a representative will join shortly",
        "i'm transferring you now",
        "i am transferring you now",
    ]

    return any(pattern in text for pattern in strict_signal_patterns)


def detect_handoff_offer(bot_message: str) -> bool:
    """
    Returns True for softer phrases that suggest a handoff is possible,
    but not yet confirmed as happening now.
    """
    text = normalize_text(bot_message)

    if detect_handoff_signal(bot_message):
        return False

    offer_patterns = [
        "i can connect you to",
        "or connect you to",
        "connect you to a representative if needed",
        "connect you to a support representative",
        "if needed, i can connect you",
        "i can help or connect you to",
    ]

    return any(pattern in text for pattern in offer_patterns)