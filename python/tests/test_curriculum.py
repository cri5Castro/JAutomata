"""Verify the complete source-grounded curriculum without relying on site output."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
TOPICS = (
    "automata",
    "regex",
    "parsing",
    "literal",
    "concatenation",
    "union",
    "kleene-star",
    "positive-closure",
    "epsilon-closure",
    "nfa-simulation",
    "subset-construction",
    "complete-dfa",
    "identity",
    "pure-execution",
    "validation-complexity",
)
LABS = ("practica1", "practica2", "practica3", "main")
FENCE = re.compile(r"^~~~(?P<language>[a-z0-9+-]*)\n(?P<body>.*?)^~~~\s*$", re.MULTILINE | re.DOTALL)
EXPECTED_OUTPUT = re.compile(r"^Expected output:\s*\n+~~~text\n(?P<body>.*?)^~~~\s*$", re.MULTILINE | re.DOTALL)
MARKDOWN_LINK = re.compile(r"\]\((?P<target>[^)#]+\.md)(?:#[^)]+)?\)")
SOURCE_LINK = re.compile(r"\]\((?P<target>[^)#]+)#L(?P<start>\d+)(?:-L(?P<end>\d+))?\)")


class CurriculumTests(unittest.TestCase):
    """Guard curriculum coverage, runnable programs, and source-grounded links."""

    def test_every_topic_has_a_theory_tutorial_pair_and_every_lab_exists(self) -> None:
        learning_map = (DOCS / "learning-map.md").read_text()
        source_map = (DOCS / "reference" / "source-curriculum.md").read_text()
        for topic in TOPICS:
            theory = DOCS / "theory" / f"{topic}.md"
            tutorial = DOCS / "tutorials" / f"{topic}.md"
            with self.subTest(topic=topic):
                self.assertTrue(theory.is_file())
                self.assertTrue(tutorial.is_file())
                self.assertIn(f"theory/{topic}.md", learning_map)
                self.assertIn(f"tutorials/{topic}.md", learning_map)
                self.assertIn(f"../theory/{topic}.md", source_map)
                self.assertIn(f"../tutorials/{topic}.md", source_map)
        for lab in LABS:
            with self.subTest(lab=lab):
                self.assertTrue((DOCS / "labs" / f"{lab}.md").is_file())
                self.assertIn(f"labs/{lab}.md", learning_map)

    def test_curriculum_links_and_source_line_ranges_resolve(self) -> None:
        documents = [DOCS / "index.md", DOCS / "learning-map.md", DOCS / "reference" / "source-curriculum.md"]
        documents.extend(DOCS / "theory" / f"{topic}.md" for topic in TOPICS)
        documents.extend(DOCS / "tutorials" / f"{topic}.md" for topic in TOPICS)
        documents.extend(DOCS / "labs" / f"{lab}.md" for lab in LABS)
        source_links = 0
        for document_path in documents:
            document = document_path.read_text()
            for match in MARKDOWN_LINK.finditer(document):
                target = (document_path.parent / match.group("target")).resolve()
                with self.subTest(document=document_path.relative_to(DOCS), target=match.group("target")):
                    self.assertTrue(target.is_file())
            for match in SOURCE_LINK.finditer(document):
                target = (document_path.parent / match.group("target")).resolve()
                with self.subTest(document=document_path.relative_to(DOCS), source=match.group("target")):
                    self.assertTrue(target.is_file())
                    self.assertTrue(target.is_relative_to(ROOT))
                    line_count = len(target.read_text().splitlines())
                    start = int(match.group("start"))
                    end = int(match.group("end") or start)
                    self.assertGreaterEqual(start, 1)
                    self.assertGreaterEqual(end, start)
                    self.assertLessEqual(end, line_count)
                source_links += 1
        self.assertGreaterEqual(source_links, 45)

    def test_new_tutorial_and_lab_programs_match_printed_output(self) -> None:
        documents = [DOCS / "tutorials" / f"{topic}.md" for topic in TOPICS]
        documents.extend(DOCS / "labs" / f"{lab}.md" for lab in LABS)
        expected_outputs = 0
        for document_path in documents:
            document = document_path.read_text()
            fences = list(FENCE.finditer(document))
            python_fences = [fence for fence in fences if fence.group("language") == "python"]
            with self.subTest(document=document_path.relative_to(DOCS), fence="presence"):
                self.assertGreaterEqual(len(python_fences), 1)
            for number, fence in enumerate(python_fences):
                namespace: dict[str, object] = {}
                output = StringIO()
                with self.subTest(document=document_path.relative_to(DOCS), fence=fence.start()):
                    with redirect_stdout(output):
                        exec(compile(fence.group("body"), str(document_path), "exec"), namespace)
                    next_python = python_fences[number + 1].start() if number + 1 < len(python_fences) else len(document)
                    expected = EXPECTED_OUTPUT.search(document, fence.end(), next_python)
                    if expected:
                        self.assertEqual(output.getvalue().strip(), expected.group("body").strip())
                        expected_outputs += 1
        self.assertEqual(expected_outputs, 19, "every paired tutorial and capstone prints checked output")

    def test_public_map_keeps_student_facing_main_provenance(self) -> None:
        source_map = (DOCS / "reference" / "source-curriculum.md").read_text()
        self.assertNotIn("Do not expand", source_map)
        self.assertNotIn("cross-link the other labs", source_map)
        self.assertIn("((a.a+)|(c+)|(b.c*))+", source_map)
        self.assertIn("commented probe", source_map)
        self.assertIn("(a.b|a*.c)+", source_map)
        self.assertIn("Main.java#L99", source_map)
        self.assertIn("Main.java#L140-L146", source_map)


if __name__ == "__main__":
    unittest.main()
