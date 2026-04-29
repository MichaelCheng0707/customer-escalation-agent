import argparse
import json
from pathlib import Path

from src.evaluation.metrics import summarize_metrics
from src.replay import load_case_by_id, run_case_replay
from src.evaluation.run_eval import load_cases


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def save_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default="verified")
    parser.add_argument("--persona", default="cooperative")
    parser.add_argument("--model", default="gpt-5-mini")
    parser.add_argument("--cases-path", default="data/cases.json")
    args = parser.parse_args()

    cases = load_cases(args.cases_path)
    records = []

    print("=" * 80)
    print(
        f"Running GPT evaluation | agent={args.agent} | "
        f"persona={args.persona} | model={args.model}"
    )
    print("=" * 80)

    for case in cases:
        record = run_case_replay(
            case=load_case_by_id(case.case_id),
            agent_name=args.agent,
            backend_mode="gpt",
            gpt_model=args.model,
            gpt_persona=args.persona,
        )
        records.append(record)
        print(
            f"{args.agent:>8} | case={record['case_id']} | "
            f"target={record['target_outcome']} | "
            f"outcome_correct={record['outcome_correct']} | "
            f"critical_action_correct={record['critical_action_correct']}"
        )

    metrics = summarize_metrics(records)
    result_payload = {
        "agent_name": args.agent,
        "backend_mode": "gpt",
        "gpt_persona": args.persona,
        "gpt_model": args.model,
        "records": records,
        "metrics": metrics,
    }

    slug = f"gpt_{args.persona}_{args.agent}".replace("-", "_")
    save_json(RESULTS_DIR / f"{slug}_results.json", result_payload)
    save_json(RESULTS_DIR / f"{slug}_metrics.json", metrics)

    print("-" * 80)
    for key, value in metrics.items():
        print(f"{key}: {value}")
    print()
    print("Saved:")
    print(f"- results/{slug}_results.json")
    print(f"- results/{slug}_metrics.json")


if __name__ == "__main__":
    main()
