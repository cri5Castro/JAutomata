"""Keep the source-derived API reference deterministic and clearly delimited."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "docs" / "python-api.md"
GENERATOR = ROOT / "python" / "scripts" / "generate_api_docs.py"
START = "<!-- GENERATED API REFERENCE: START -->"
END = "<!-- GENERATED API REFERENCE: END -->"


class GeneratedDocumentationTests(unittest.TestCase):
    """Verify the generated boundary without treating generated text as authored prose."""

    def _run_generator(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(GENERATOR), *arguments],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_api_reference_is_current_and_keeps_authored_context(self) -> None:
        """The stale check passes and source-linked entries follow the authored intro."""
        self._run_generator("--check")
        document = API.read_text()
        self.assertEqual(document.count(START), 1)
        self.assertEqual(document.count(END), 1)
        self.assertLess(document.index("## Java correspondence"), document.index(START))
        self.assertIn("[Java reference behavior](java-reference.md)", document)
        self.assertIn("#### `compile_regex`", document)
        self.assertIn("**Source:** [jautomata](../python/src/jautomata/thompson.py#L", document)
        self.assertIn("#### `Automaton`", document)

    def test_generation_is_idempotent(self) -> None:
        """A second generation pass leaves the deterministic document byte-identical."""
        before = API.read_text()
        self._run_generator()
        self.assertEqual(API.read_text(), before)
        self._run_generator("--check")


if __name__ == "__main__":
    unittest.main()
