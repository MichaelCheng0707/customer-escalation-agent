import statistics


def safe_mean(values: list[float | int]) -> float:
    if not values:
        return 0.0
    return float(statistics.mean(values))


def filter_by_target(records: list[dict], target_outcome: str) -> list[dict]:
    return [
        record
        for record in records
        if record["target_outcome"] == target_outcome
    ]


def user_actions(record: dict) -> list[str]:
    return [
        step["action"]
        for step in record["trace"]
        if step["speaker"] == "user_agent"
    ]


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
    target_records = [
        r for r in records
        if r["target_outcome"] in {"continue_self_serve", "request_more_info"}
    ]
    if not target_records:
        return 0.0
    errors = sum(1 for r in target_records if r["over_escalated"])
    return errors / len(target_records)


def missing_info_violation_rate(records: list[dict]) -> float:
    target_records = filter_by_target(records, "request_more_info")
    if not target_records:
        return 0.0
    violations = sum(1 for r in target_records if r["missing_info_violation"])
    return violations / len(target_records)


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


def handoff_reached_rate(records: list[dict]) -> float:
    target_records = filter_by_target(records, "confirmed_handoff")
    if not target_records:
        return 0.0
    reached = sum(1 for r in target_records if r["human_signal_detected"])
    return reached / len(target_records)


def handoff_takeover_rate(records: list[dict]) -> float:
    target_records = filter_by_target(records, "confirmed_handoff")
    if not target_records:
        return 0.0
    takeover = sum(1 for r in target_records if r["user_alerted"])
    return takeover / len(target_records)


def self_serve_accuracy(records: list[dict]) -> float:
    target_records = filter_by_target(records, "continue_self_serve")
    if not target_records:
        return 0.0
    correct = sum(1 for r in target_records if r["outcome_correct"])
    return correct / len(target_records)


def self_serve_critical_action_accuracy(records: list[dict]) -> float:
    target_records = filter_by_target(records, "continue_self_serve")
    if not target_records:
        return 0.0
    correct = sum(1 for r in target_records if r["critical_action_correct"])
    return correct / len(target_records)


def missing_info_accuracy(records: list[dict]) -> float:
    target_records = filter_by_target(records, "request_more_info")
    if not target_records:
        return 0.0
    correct = sum(1 for r in target_records if r["critical_action_correct"])
    return correct / len(target_records)


def dead_end_stop_rate(records: list[dict]) -> float:
    target_records = filter_by_target(records, "stop_dead_end")
    if not target_records:
        return 0.0
    stopped = sum(
        1
        for r in target_records
        if "stop_dead_end" in user_actions(r)
    )
    return stopped / len(target_records)


def target_case_counts(records: list[dict]) -> dict:
    targets = sorted({record["target_outcome"] for record in records})
    return {
        target: len(filter_by_target(records, target))
        for target in targets
    }


def summarize_metrics(records: list[dict]) -> dict:
    return {
        "num_cases": len(records),
        "target_case_counts": target_case_counts(records),
        "outcome_accuracy": outcome_accuracy(records),
        "critical_action_accuracy": critical_action_accuracy(records),
        "handoff_reached_rate": handoff_reached_rate(records),
        "handoff_takeover_rate": handoff_takeover_rate(records),
        "self_serve_accuracy": self_serve_accuracy(records),
        "self_serve_critical_action_accuracy": self_serve_critical_action_accuracy(records),
        "missing_info_accuracy": missing_info_accuracy(records),
        "dead_end_stop_rate": dead_end_stop_rate(records),
        "over_escalation_rate": over_escalation_rate(records),
        "missing_info_violation_rate": missing_info_violation_rate(records),
        "premature_takeover_rate": premature_takeover_rate(records),
        "loop_dead_end_accuracy": loop_dead_end_accuracy(records),
        "average_turns": average_turns(records),
    }
