import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PROJECT_ROOT / "results"


def main():
    metrics_path = RESULTS_DIR / "eval_metrics.json"

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    print("=" * 100)
    print("Evaluation Summary")
    print("=" * 100)

    for agent_name, values in metrics.items():
        print(f"\nAgent: {agent_name}")
        print("-" * 100)
        for key, value in values.items():
            print(f"{key:40s} : {value}")


if __name__ == "__main__":
    main()