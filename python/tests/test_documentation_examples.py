"""Execute public-module doctests and documented Python/example snippets."""

from __future__ import annotations

import doctest
from pathlib import Path
import re
import subprocess
import sys
import unittest

import jautomata
from jautomata import model, regex, simulation, subsets, thompson


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
EXAMPLE = ROOT / "python" / "examples" / "regex_pipeline.py"


class DocumentationExamplesTests(unittest.TestCase):
    """Regression coverage for examples presented to users."""

    def test_public_module_doctests(self) -> None:
        for module in (jautomata, model, regex, thompson, simulation, subsets):
            with self.subTest(module=module.__name__):
                result = doctest.testmod(module, optionflags=doctest.ELLIPSIS)
                self.assertEqual(result.failed, 0)

    def test_documented_python_fences(self) -> None:
        for filename in ("getting-started.md", "tutorial.md", "python-api.md"):
            namespace: dict[str, object] = {}
            document = (DOCS / filename).read_text()
            blocks = re.findall(r"~~~python\n(.*?)~~~", document, flags=re.DOTALL)
            for block in blocks:
                with self.subTest(document=filename, block=block.splitlines()[0]):
                    exec(compile(block, filename, "exec"), namespace)

    def test_regex_pipeline_example(self) -> None:
        result = subprocess.run(
            [sys.executable, str(EXAMPLE)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("expression: (a.b|a*.c)+", result.stdout)
        self.assertIn("''" + ": NFA=False DFA=False", result.stdout)
        self.assertIn("'ab': NFA=True DFA=True", result.stdout)
        self.assertIn("'a': NFA=False DFA=False", result.stdout)


if __name__ == "__main__":
    unittest.main()
