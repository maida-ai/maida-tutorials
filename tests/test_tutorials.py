import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_NOTEBOOKS = (
    Path("LangChain/Mock LangGraph Agent.ipynb"),
    Path("OpenAI/Mock OpenAI Agent.ipynb"),
    Path("CrewAI/Mock CrewAI Agent.ipynb"),
)


def notebook_source(relative_path: Path) -> str:
    notebook = json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", [])) for cell in notebook.get("cells", [])
    )


class TutorialConformanceTests(unittest.TestCase):
    def test_supported_frameworks_share_the_offline_sales_scenario(self):
        for relative_path in FRAMEWORK_NOTEBOOKS:
            with self.subTest(notebook=str(relative_path)):
                source = notebook_source(relative_path)
                for expected in ("search", "calculator", "save_result", "6.5"):
                    self.assertIn(expected, source)
                self.assertRegex(source.lower(), r"(?:no|without) api keys?")

    def test_crewai_tutorial_documents_setup_privacy_and_limitations(self):
        source = notebook_source(Path("CrewAI/Mock CrewAI Agent.ipynb"))

        for expected in (
            "from maida.integrations import crewai",
            "LLMCallHookContext",
            "ToolCallHookContext",
            "CREWAI_STORAGE_DIR",
            "maida-ai[crewai]",
            "run_crewai_failure_path",
            "tutorial-secret",
            "Failure cases and limitations",
            "Missing dependency",
            "Hook ordering",
            "Redaction and truncation",
        ):
            self.assertIn(expected, source)

    def test_openai_tutorial_pins_adapter_conformance_contract(self):
        source = notebook_source(Path("OpenAI/Mock OpenAI Agent.ipynb"))

        for expected in (
            "set_trace_processors([openai_agents.PROCESSOR])",
            '"llm_calls": 4',
            '"tool_calls": 3',
            '"tool_call_sequence": ["search", "calculator", "save_result"]',
            '"event_type_sequence": [',
            "assert success_signature == EXPECTED_SUCCESS_SIGNATURE",
            'assert guarded_signature["final_status"] == "error"',
            'assert guarded_signature["event_type_sequence"][-3:] == [',
            '"LOOP_WARNING", "ERROR", "RUN_END"',
            'raise AssertionError("Expected the loop guardrail to abort the workflow")',
            "maida-ai[openai]",
            "No active Maida run",
            "standard `LLM_CALL` and `TOOL_CALL` events",
            "Redaction and truncation",
            "compatibility fallback for the SDK version locked by this tutorial",
            "PROCESSOR.abort_exception",
            "PROCESSOR.raise_if_aborted()",
        ):
            self.assertIn(expected, source)

    def test_langgraph_tutorial_pins_adapter_conformance_contract(self):
        source = notebook_source(Path("LangChain/Mock LangGraph Agent.ipynb"))

        for expected in (
            "handler = LangChainCallbackHandler()",
            'config = {"callbacks": [handler]}',
            '"llm_calls": 4',
            '"tool_calls": 3',
            '"tool_call_sequence": ["search", "calculator", "save_result"]',
            '"event_type_sequence": [',
            'assert success_signature == EXPECTED_SUCCESS_SIGNATURE',
            'assert guarded_signature["final_status"] == "error"',
            'assert guarded_signature["event_type_sequence"][-3:] == [',
            '"LOOP_WARNING", "ERROR", "RUN_END"',
            "maida-ai[langchain]",
            "No active Maida run",
            "standard `LLM_CALL` and `TOOL_CALL` events",
            "Redaction and truncation",
        ):
            self.assertIn(expected, source)

    def test_readme_lists_crewai_install_and_notebook(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("CrewAI/Mock CrewAI Agent.ipynb", readme)
        self.assertIn('uv pip install "maida-ai[crewai]"', readme)

    def test_readme_summarizes_openai_conformance_and_failure_paths(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        openai_section = readme.split(
            "### 3. Debug an OpenAI Agents Workflow (`OpenAI/`)", 1
        )[1].split("### 4. Debug a CrewAI Workflow (`CrewAI/`)", 1)[0]

        for expected in (
            "four LLM calls, three tool calls, and `search → calculator → save_result`",
            "`LOOP_WARNING → ERROR → RUN_END(status=error)`",
            "Missing dependencies, inactive-run behavior, normalized events, and Maida's storage redaction/truncation",
        ):
            self.assertIn(expected, openai_section)


if __name__ == "__main__":
    unittest.main()
