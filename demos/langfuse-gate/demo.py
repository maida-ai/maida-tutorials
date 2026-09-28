"""Stage-safe demo of Maida gating agent traces imported from Langfuse."""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


DEMO_DIR = Path(__file__).resolve().parent
FIXTURE_PATH = DEMO_DIR / "observations.json"
PUBLIC_KEY = "pk-fixture"
SECRET_KEY = "sk-fixture"


class FixtureHandler(BaseHTTPRequestHandler):
    """Serve synthetic observations through Langfuse's read-only API shape."""

    observations: list[dict[str, object]] = []

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        request = urlsplit(self.path)
        if request.path != "/api/public/v2/observations":
            self.send_error(404)
            return

        credentials = base64.b64encode(
            f"{PUBLIC_KEY}:{SECRET_KEY}".encode("ascii")
        ).decode("ascii")
        if self.headers.get("Authorization") != f"Basic {credentials}":
            self.send_error(401)
            return

        trace_ids = parse_qs(request.query).get("traceId", [])
        if len(trace_ids) != 1:
            self.send_error(400)
            return

        rows = [row for row in self.observations if row.get("traceId") == trace_ids[0]]
        payload = json.dumps({"data": rows, "meta": {}}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


@contextmanager
def fixture_server() -> Iterator[str]:
    """Start the authenticated loopback fixture server on an ephemeral port."""

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    FixtureHandler.observations = fixture["data"]
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


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


def sanitize(text: str, *, data_dir: Path, baseline: Path) -> str:
    return text.replace(str(baseline), "$DEMO_BASELINE").replace(
        str(data_dir), "$MAIDA_DATA_DIR"
    )


def emit_result(
    result: subprocess.CompletedProcess[str],
    *,
    data_dir: Path,
    baseline: Path,
    line_limit: int | None = None,
) -> None:
    for stream in (result.stderr, result.stdout):
        rendered = sanitize(stream, data_dir=data_dir, baseline=baseline).strip()
        if not rendered:
            continue
        if line_limit is not None:
            rendered = "\n".join(rendered.splitlines()[:line_limit])
        print(rendered)


def show_command(command: str) -> None:
    print(f"\n$ {command}")


def pause(enabled: bool, prompt: str) -> None:
    if enabled:
        input(f"\nPress Enter to {prompt}...")


def import_trace(
    trace_id: str,
    *,
    environment: dict[str, str],
    data_dir: Path,
    baseline: Path,
) -> None:
    show_command(f"maida import langfuse --trace-id {trace_id}")
    result = run_cli(
        ["import", "langfuse", "--trace-id", trace_id], environment=environment
    )
    require_status(result, 0, f"import {trace_id}")
    emit_result(result, data_dir=data_dir, baseline=baseline)


def assert_latest(
    expected: int,
    *,
    environment: dict[str, str],
    data_dir: Path,
    baseline: Path,
    concise: bool,
) -> None:
    show_command(
        'maida assert --baseline "$DEMO_BASELINE" --no-new-tools --no-loops '
        "--cost-tolerance 0 --format markdown"
    )
    result = run_cli(
        [
            "assert",
            "--baseline",
            str(baseline),
            "--no-new-tools",
            "--no-loops",
            "--cost-tolerance",
            "0",
            "--format",
            "markdown",
        ],
        environment=environment,
    )
    require_status(result, expected, "baseline assertion")
    emit_result(
        result,
        data_dir=data_dir,
        baseline=baseline,
        line_limit=3 if concise else None,
    )


def run_demo(*, recording: bool, data_dir: Path, baseline: Path) -> None:
    print("LANGFUSE → MAIDA: GATE WHAT YOU ALREADY TRACE")
    print("Synthetic support-agent traces; real importer and real regression gate.")
    print("No account, API key, LLM call, or external network request required.")

    with fixture_server() as base_url:
        environment = os.environ.copy()
        environment.update(
            {
                "LANGFUSE_PUBLIC_KEY": PUBLIC_KEY,
                "LANGFUSE_SECRET_KEY": SECRET_KEY,
                "LANGFUSE_BASE_URL": base_url,
                "MAIDA_DATA_DIR": str(data_dir),
                "NO_COLOR": "1",
            }
        )
        baseline.parent.mkdir(parents=True, exist_ok=True)

        pause(recording, "capture the known-good trace")
        print("\nACT 1 — Capture known-good behavior")
        print("The support agent looks up one account and returns the answer.")
        import_trace(
            "support-agent-baseline",
            environment=environment,
            data_dir=data_dir,
            baseline=baseline,
        )
        show_command('maida baseline --out "$DEMO_BASELINE"')
        captured = run_cli(
            ["baseline", "--out", str(baseline)], environment=environment
        )
        require_status(captured, 0, "baseline capture")
        emit_result(captured, data_dir=data_dir, baseline=baseline)

        pause(recording, "verify an unchanged candidate")
        print("\nACT 2 — Verify unchanged behavior")
        print("A later Langfuse trace follows the same one-tool path.")
        import_trace(
            "support-agent-candidate",
            environment=environment,
            data_dir=data_dir,
            baseline=baseline,
        )
        assert_latest(
            0,
            environment=environment,
            data_dir=data_dir,
            baseline=baseline,
            concise=True,
        )

        pause(recording, "import the regressed candidate")
        print("\nACT 3 — Catch the regression")
        print("The answer still looks fine, but the agent now escalates three times.")
        import_trace(
            "support-agent-regression",
            environment=environment,
            data_dir=data_dir,
            baseline=baseline,
        )
        assert_latest(
            1,
            environment=environment,
            data_dir=data_dir,
            baseline=baseline,
            concise=False,
        )

    print("\nPR BLOCKED")
    print("Langfuse recorded what happened. Maida caught what changed before merge.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recording",
        action="store_true",
        help="Pause before each act for presenter-controlled pacing",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="maida-langfuse-gate-") as temporary:
            root = Path(temporary)
            run_demo(
                recording=arguments.recording,
                data_dir=root / "runs",
                baseline=root / "baseline.json",
            )
    except (EOFError, OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
