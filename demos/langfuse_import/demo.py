"""Deterministic end-to-end demo for Maida's Langfuse trace importer."""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


DEMO_DIR = Path(__file__).resolve().parent
FIXTURE_PATH = DEMO_DIR / "observations.json"


class FixtureHandler(BaseHTTPRequestHandler):
    observations: list[dict[str, object]] = []

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        request = urlsplit(self.path)
        if request.path != "/api/public/v2/observations":
            self.send_error(404)
            return
        credentials = base64.b64encode(b"pk-fixture:sk-fixture").decode("ascii")
        if self.headers.get("Authorization") != f"Basic {credentials}":
            self.send_error(401)
            return

        trace_ids = parse_qs(request.query).get("traceId", [])
        if len(trace_ids) != 1:
            self.send_error(400)
            return
        rows = [
            row for row in self.observations if row.get("traceId") == trace_ids[0]
        ]
        payload = json.dumps({"data": rows, "meta": {}}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def run_cli(
    arguments: list[str], *, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "maida.cli", *arguments],
        cwd=DEMO_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def require_status(
    result: subprocess.CompletedProcess[str], expected: int, label: str
) -> None:
    if result.returncode != expected:
        detail = result.stderr.strip() or result.stdout.strip() or "no CLI output"
        raise RuntimeError(
            f"{label} returned {result.returncode}, expected {expected}: {detail}"
        )


def import_trace(
    trace_id: str, *, base_url: str, environment: dict[str, str]
) -> dict[str, object]:
    result = run_cli(
        [
            "import",
            "langfuse",
            "--trace-id",
            trace_id,
            "--base-url",
            base_url,
            "--json",
        ],
        environment=environment,
    )
    require_status(result, 0, f"import {trace_id}")
    return json.loads(result.stdout)


def run_demo(data_dir: Path, baseline: Path) -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    FixtureHandler.observations = fixture["data"]
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    environment = os.environ.copy()
    environment.update(
        {
            "LANGFUSE_PUBLIC_KEY": "pk-fixture",
            "LANGFUSE_SECRET_KEY": "sk-fixture",
            "MAIDA_DATA_DIR": str(data_dir),
        }
    )
    base_url = f"http://127.0.0.1:{server.server_port}"
    baseline.parent.mkdir(parents=True, exist_ok=True)

    try:
        first = import_trace(
            "fixture-good-trace", base_url=base_url, environment=environment
        )
        if len(first.get("imported", [])) != 1:
            raise RuntimeError("good trace was not installed exactly once")
        print("Good trace imported")

        duplicate = import_trace(
            "fixture-good-trace", base_url=base_url, environment=environment
        )
        skipped = duplicate.get("skipped", [])
        if not skipped or skipped[0].get("reason") != "already imported":
            raise RuntimeError("duplicate import was not reported as idempotent")
        print("Duplicate import skipped")

        baseline_result = run_cli(
            ["baseline", "--out", str(baseline)], environment=environment
        )
        require_status(baseline_result, 0, "baseline capture")

        assertion_args = [
            "assert",
            "--baseline",
            str(baseline),
            "--no-new-tools",
            "--no-loops",
            "--cost-tolerance",
            "0",
            "--format",
            "markdown",
        ]
        passing = run_cli(assertion_args, environment=environment)
        require_status(passing, 0, "good-trace assertion")
        print("Baseline assertion: PASS")

        regression = import_trace(
            "fixture-regression-trace", base_url=base_url, environment=environment
        )
        if len(regression.get("imported", [])) != 1:
            raise RuntimeError("regression trace was not installed exactly once")
        failing = run_cli(assertion_args, environment=environment)
        require_status(failing, 1, "regression assertion")
        print("Regression assertion: FAIL (expected)")
        print(failing.stdout.rstrip())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Isolated Maida storage used by the demo",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Temporary baseline written by the demo",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(argv)
    try:
        if arguments.data_dir is None:
            with tempfile.TemporaryDirectory(prefix="maida-langfuse-demo-") as temp:
                root = Path(temp)
                run_demo(root / "data", arguments.baseline or root / "baseline.json")
        else:
            baseline = arguments.baseline or arguments.data_dir.parent / "baseline.json"
            run_demo(arguments.data_dir, baseline)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
