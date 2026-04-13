import statistics


def safe_mean(values: list[float | int]) -> float:
    if not values:
        return 0.0
    return float(statistics.mean(values))


def outcome_accuracy(records: list[dict]) -> float:
    if not records:
        return 0.0
    correct = sum(1 for r in records if r["outcome_correct"])
    return correct / len(records)


def critical_action_accuracy(records: list[dict]) -> float:
    if not records:
        return 0.0
    correct = sum(1 for r in records if r["critical_action_correct"])
    return correct / len(records)


def over_escalation_rate(records: list[dict]) -> float:
    if not records:
        return 0.0
    errors = sum(1 for r in records if r["over_escalated"])
    return errors / len(records)


def missing_info_violation_rate(records: list[dict]) -> float:
    if not records:
        return 0.0
    violations = sum(1 for r in records if r["missing_info_violation"])
    return violations / len(records)


def premature_takeover_rate(records: list[dict]) -> float:
    if not records:
        return 0.0
    premature = sum(1 for r in records if r["premature_takeover"])
    return premature / len(records)


def loop_dead_end_accuracy(records: list[dict]) -> float:
    target_records = [
        r for r in records
        if r["target_outcome"] in {"confirmed_handoff", "stop_dead_end"}
    ]
    if not target_records:
        return 0.0
    correct = sum(1 for r in target_records if r["outcome_correct"])
    return correct / len(target_records)


def average_turns(records: list[dict]) -> float:
    return safe_mean([r["turn_count"] for r in records])


def summarize_metrics(records: list[dict]) -> dict:
    return {
        "num_cases": len(records),
        "outcome_accuracy": outcome_accuracy(records),
        "critical_action_accuracy": critical_action_accuracy(records),
        "over_escalation_rate": over_escalation_rate(records),
        "missing_info_violation_rate": missing_info_violation_rate(records),
        "premature_takeover_rate": premature_takeover_rate(records),
        "loop_dead_end_accuracy": loop_dead_end_accuracy(records),
        "average_turns": average_turns(records),
    }