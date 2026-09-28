"""Compare one captured task with its reviewed baseline using Maida 0.5.3.

The release names captures by session. This explicit task mapping retains all
source identities and delegates validation, evidence loading, and evaluation to
Maida. It never edits a trace, baseline, policy, budget, or verdict threshold.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument(
        "--same-task",
        action="store_true",
        help="Confirm same task, starting state and intended agent role",
    )
    parser.add_argument(
        "--format", choices=("text", "markdown", "json"), default="markdown"
    )
    args = parser.parse_args()
    if not args.same_task:
        parser.error(
            "Review task, starting state and role, then pass --same-task; session names alone cannot establish comparability"
        )
    if importlib.metadata.version("maida-ai") != "0.5.3":
        parser.error(
            'Run this release helper with uv run --no-project --with "maida-ai==0.5.3" python'
        )

    from maida.baseline import load_baseline
    from maida.config import load_config
    from maida.drift import NativeTraceWindowSource, run_drift
    from maida.policy import load_policy
    from maida.statistics import GateVerdict

    try:
        baseline_bytes = args.baseline.read_bytes()
        baseline = load_baseline(args.baseline)
        policy = load_policy(args.policy)
        config = load_config()
        native = NativeTraceWindowSource(args.window, config)
        traces = native.load_all()
        candidate_names = {trace.meta.get("run_name") for trace in traces}
        if len(candidate_names) != 1:
            raise ValueError(
                "Candidate window contains multiple sessions; select one task's fresh capture window"
            )
        baseline_name = baseline.get("source_run_name")
        candidate_name = next(iter(candidate_names))
        if not all(
            isinstance(name, str) and name.startswith("claude-code:")
            for name in (baseline_name, candidate_name)
        ):
            raise ValueError(
                "This helper compares captured coding sessions only; use maida drift for stable workflow names"
            )
        if not policy.metrics:
            raise ValueError(
                "Review an explicit v2 metrics policy before comparing captures"
            )

        class SameTaskSource:
            analysis_config = native.analysis_config

            def load_all(self):
                return traces

            def load(self, agent_name):
                if agent_name != baseline_name:
                    raise ValueError("Unexpected baseline task identity")
                return traces

        report = run_drift(
            args.window,
            baseline=baseline,
            policy=policy,
            config=config,
            source=SameTaskSource(),
        )
        mapping = {
            "same_task_confirmed": True,
            "baseline_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
            "baseline_source_run_name": baseline_name,
            "candidate_source_run_name": candidate_name,
            "scope": "one captured task; no population-level activation claim",
        }
        if args.format == "json":
            payload = json.loads(report.to_json())
            payload["capture_task_comparison"] = mapping
            print(json.dumps(payload, indent=2))
        else:
            rendered = (
                report.to_markdown(baseline_path=str(args.baseline))
                if args.format == "markdown"
                else report.to_text()
            )
            print(rendered)
            print("\nCompared one explicitly confirmed task across capture sessions.")
            print(f"Baseline SHA-256: {mapping['baseline_sha256']}")
            print(f"Source identities: {baseline_name} -> {candidate_name}")
        return 1 if report.verdict is GateVerdict.FAIL else 0
    except (OSError, ValueError) as error:
        print(
            f"Cannot compare capture: {error}. Keep the accepted baseline and fix the input.",
            file=sys.stderr,
        )
        return 2
    except Exception as error:
        print(
            f"Capture evaluation failed: {error}. Keep the evidence and investigate before accepting changes.",
            file=sys.stderr,
        )
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
