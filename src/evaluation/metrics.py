import statistics


def safe_mean(values: list[float | int]) -> float:
    if not values:
        return 0.0
    return float(statistics.mean(values))


def escalation_success_rate(records: list[dict]) -> float:
    if not records:
        return 0.0
    success_count = sum(1 for r in records if r["escalation_success"])
    return success_count / len(records)


def average_turns_to_escalation(records: list[dict]) -> float:
    turns = [r["turn_count"] for r in records if r["escalation_success"]]
    return safe_mean(turns)


def unnecessary_user_intervention_rate(records: list[dict]) -> float:
    """
    A simple proxy:
    user takeover is considered unnecessary if:
    - user_alerted is True
    - but human_signal_detected is False
    """
    if not records:
        return 0.0

    unnecessary = sum(
        1
        for r in records
        if r["user_alerted"] and not r["human_signal_detected"]
    )
    return unnecessary / len(records)


def failed_escalation_rate_on_severe_cases(records: list[dict]) -> float:
    severe_records = [r for r in records if r["severity"] == "high"]
    if not severe_records:
        return 0.0

    failed = sum(1 for r in severe_records if not r["escalation_success"])
    return failed / len(severe_records)


def average_escalation_attempts(records: list[dict]) -> float:
    attempts = [r["escalation_attempts"] for r in records]
    return safe_mean(attempts)


def summarize_metrics(records: list[dict]) -> dict:
    return {
        "num_cases": len(records),
        "escalation_success_rate": escalation_success_rate(records),
        "average_turns_to_escalation": average_turns_to_escalation(records),
        "unnecessary_user_intervention_rate": unnecessary_user_intervention_rate(records),
        "failed_escalation_rate_on_severe_cases": failed_escalation_rate_on_severe_cases(records),
        "average_escalation_attempts": average_escalation_attempts(records),
    }