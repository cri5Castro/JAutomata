"""Check diagram meaning against executable models, not rendered snapshots."""

from contextlib import redirect_stdout
from html.parser import HTMLParser
from io import StringIO
from itertools import product
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from jautomata import accepts, compile_regex, epsilon_closure, to_dfa
from jautomata.model import Automaton, Transition
from jautomata.regex import Alternation, Concatenation, KleeneStar, Literal, parse, to_postfix


ROOT = Path(__file__).resolve().parents[2]
CATALOG = json.loads((ROOT / ".omm/manifest.json").read_text())
FIGURES = {entry["id"]: entry for entry in CATALOG["figures"]}
NODE = re.compile(r'(\w+)(\(\(\(|\(\(|\[)"([^"\n]+)"(?:\)\)\)|\)\)|\])')
EDGE = re.compile(r'(\w+) -->(?:\|([^|]+)\|)? (\w+)')


def source(identifier):
    return (ROOT / FIGURES[identifier]["source"]).read_text()


def flowchart(text):
    """Read the catalog's explicit nodes/edges; refuse an unparsed arrow."""
    nodes = {}
    for name, shape, label in NODE.findall(text):
        if name in nodes and nodes[name] != (shape, label):
            raise ValueError(f"Conflicting node declaration: {name}")
        nodes[name] = (shape, label)
    edges = []
    for line in text.splitlines():
        statement = NODE.sub(lambda match: match[1], line.strip())
        if "-->" not in line:
            # Validate whole statements: a prefix match can hide a real Mermaid
            # edge after a semicolon (including dotted/thick edge syntax).
            control = re.fullmatch(
                r"(?:flowchart|graph|direction) (?:LR|RL|TB|BT|TD)|subgraph \w+|style \w+ fill:none,stroke:none",
                statement,
            )
            if statement and not (control or statement == "end" or statement in nodes):
                raise ValueError(f"Unsupported diagram statement: {line}")
            continue
        match = EDGE.fullmatch(statement)
        if not match:
            raise ValueError(f"Unsupported diagram edge: {line}")
        left, label, right = match.groups()
        if left not in nodes or right not in nodes:
            raise ValueError(f"Undeclared edge endpoint: {line}")
        edges.append((left, label, right))
    if len(edges) != len(set(edges)):
        raise ValueError("Duplicate diagram edge")
    return nodes, edges


def machine(identifier, prefix="", start="start", labels=None):
    nodes, edges = flowchart(source(identifier))
    # State numbers come from visible labels, not hidden Mermaid IDs.
    states = {name: (labels[label] if labels else int(label))
              for name, (shape, label) in nodes.items()
              if shape.startswith("((") and name.startswith(prefix)}
    starts = [right for left, label, right in edges if left == start and label is None]
    if len(starts) != 1:
        raise ValueError("Expected exactly one start arrow")
    transitions = []
    for left, label, right in edges:
        if left not in states:
            continue
        if right not in states or label is None:
            raise ValueError("Unlabelled or cross-machine transition")
        for symbol in label.split(":", 1)[0].split(","):
            symbol = symbol.strip()
            transitions.append(Transition(states[left], None if symbol == "ε" else symbol, states[right]))
    if len(transitions) != len(set(transitions)):
        raise ValueError("Duplicate semantic transition")
    return Automaton(set(states.values()), states[starts[0]],
                     {value for name, value in states.items() if nodes[name][0] == "((("},
                     set(transitions))


def lesson_namespace(path):
    namespace = {}
    for block in re.findall(r"~~~python\n(.*?)\n~~~", (ROOT / path).read_text(), re.S):
        with redirect_stdout(StringIO()):
            exec(compile(block, path, "exec"), namespace)
    return namespace


def block_acceptor(identifier):
    """Interpret diagram paths, consuming the regex written on each block node."""
    nodes, edges = flowchart(source(identifier))
    expressions = {}
    terminals = set()
    for name, (_, label) in nodes.items():
        if "<br/>" in label:
            expressions[name] = label.split("<br/>")[0].replace(".", "")
        elif label.startswith("Consume final "):
            expressions[name] = re.escape(label.removeprefix("Consume final "))
        elif label in {"May finish", "Whole word complete"}:
            terminals.add(name)
        elif label not in {"Choose one block", "Choose one prefix", "One block complete"}:
            raise ValueError(f"Unknown block meaning: {label}")

    def recognizes(word):
        pending, seen = [("choose", 0)], set()
        while pending:
            node, index = pending.pop()
            if (node, index) in seen:
                continue
            seen.add((node, index))
            ends = [end for end in range(index, len(word) + 1)
                    if re.fullmatch(expressions[node], word[index:end])] if node in expressions else [index]
            for end in ends:
                if node in terminals and end == len(word):
                    return True
                pending.extend((right, end) for left, _, right in edges if left == node)
        return False
    return recognizes


class DiagramImages(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == "img" and "/diagrams/" in attributes.get("src", ""):
            self.images.append(attributes)


class DiagramTests(unittest.TestCase):
    def test_unsupported_edges_cannot_hide_behind_control_statements(self):
        text = source("literal")
        self.assertEqual(flowchart(text)[1], [("start", None, "q0"), ("q0", "a", "q1")])
        for statement in (
            "style start fill:none,stroke:none; q0 -.->|b| q1",
            "flowchart LR; q0 -.->|b| q1",
            'subgraph extra["Extra"]; q0 -.->|b| q1',
            "direction LR; q0 ==>|b| q1",
            "q0 -.->|b| q1",
        ):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(ValueError, "Unsupported diagram"):
                    flowchart(text + statement + "\n")

    def test_thompson_figures_equal_compiled_graphs(self):
        for identifier, expression in {
            "literal": "a", "concatenation": "a.b", "union": "a|b",
            "kleene-star": "a*", "positive-closure": "a+", "nested-star": "(a*)*",
        }.items():
            with self.subTest(figure=identifier):
                self.assertEqual(machine(identifier), compile_regex(expression))
        self.assertEqual(epsilon_closure(machine("nested-star"), {4}), {0, 2, 3, 4, 5})

    def test_fixture_figures_equal_executable_lessons(self):
        fixtures = {
            "complete-alphabet": ("docs/tutorials/complete-dfa.md", {0, 1, 9}),
            "epsilon-closure": ("docs/tutorials/epsilon-closure.md", set(range(6))),
            "pure-execution": ("docs/tutorials/pure-execution.md", set(range(5))),
            "competing-paths": ("docs/tutorials/nfa-simulation.md", set(range(6))),
            "intro-epsilon-closure": ("docs/learn/epsilon-closure.md", set(range(3))),
            "practica1-language": ("docs/labs/practica1.md", set(range(1, 7))),
        }
        for identifier, (path, states) in fixtures.items():
            with self.subTest(figure=identifier):
                models = [value for value in lesson_namespace(path).values()
                          if isinstance(value, Automaton) and value.states == states]
                self.assertIn(machine(identifier), models)
        self.assertNotEqual(machine("epsilon-closure"), machine("intro-epsilon-closure"))

    def test_complete_dfa_has_every_state_symbol_transition(self):
        dfa = machine("subset-construction", prefix="", labels={"D0": 0, "D1": 1, "D2": 2, "D∅": 3})
        self.assertEqual(dfa, to_dfa(compile_regex("a|b")))
        self.assertEqual(len(dfa.transitions), 8)
        self.assertEqual({(edge.source, edge.symbol) for edge in dfa.transitions}, set(product(range(4), "ab")))
        self.assertEqual({edge for edge in dfa.transitions if edge.source in {1, 2, 3}},
                         {Transition(state, symbol, 3) for state, symbol in product((1, 2, 3), "ab")})

    def test_nullable_path_is_a_real_accepting_subgraph(self):
        path, full = machine("nullable-positive-path"), compile_regex("(a*)+")
        self.assertLess(path.states, full.states)
        self.assertLess(path.transitions, full.transitions)
        self.assertEqual((path.start_state, path.final_states), (full.start_state, full.final_states))
        self.assertTrue(accepts(path, ""))
        self.assertNotIn(Transition(4, None, 5), path.transitions, "positive closure has no outer bypass")

    def test_paired_machines_preserve_language_without_cross_edges(self):
        main = lesson_namespace("docs/labs/main.md")
        for prefix, start, name in [("a", "startA", "left"), ("b", "startB", "right")]:
            self.assertEqual(machine("main-relabeling", prefix, start), main[name])
        original = machine("relabeling", "a", "startA")
        renamed = machine("relabeling", "b", "startB")
        self.assertEqual(original, compile_regex("a"))
        self.assertEqual(renamed, Automaton({10, 11}, 10, {11}, {Transition(10, "a", 11)}))
        linked = machine("concatenation-seams", "a", "startA")
        fused = machine("concatenation-seams", "b", "startB", {"0": 0, "X": 1, "3": 3})
        self.assertEqual(linked, compile_regex("a.b"))
        self.assertEqual(fused, Automaton({0, 1, 3}, 0, {3}, {Transition(0, "a", 1), Transition(1, "b", 3)}))
        for word in ("", "a", "b", "ab", "aba", "aab"):
            self.assertEqual(accepts(linked, word), accepts(fused, word))

    def test_block_paths_match_model_and_independent_language_oracles(self):
        cases = [
            ("main-blocks", "((a.a+)|(c+)|(b.c*))+", r"(a{2,}|c+|bc*)+", "abc"),
            ("practica2-prefixes", "((b.c.d)*|f+.a).f", r"((bcd)*|f+a)f", "abcdf"),
            ("practica3-blocks", "(a.b|a*.c)+", r"(ab|a*c)+", "abc"),
        ]
        for identifier, expression, oracle, alphabet in cases:
            graph_accepts, model = block_acceptor(identifier), compile_regex(expression)
            with self.subTest(figure=identifier):
                for length in range(6):
                    for letters in product(alphabet, repeat=length):
                        word = "".join(letters)
                        expected = re.fullmatch(oracle, word) is not None
                        self.assertEqual(graph_accepts(word), expected, (identifier, word))
                        self.assertEqual(accepts(model, word), expected, (identifier, word))

    def test_parser_tree_and_pipeline_follow_executable_operations(self):
        nodes, edges = flowchart(source("parsing"))
        expression = nodes["infix"][1].removeprefix("Infix: ")
        self.assertEqual(tuple(nodes["postfix"][1].split("<br/>")[1].split()), to_postfix(expression))

        def tree(node):
            label = nodes[node][1]
            children = {role: target for parent, role, target in edges if parent == node}
            if label.startswith("Literal "):
                self.assertEqual(children, {})
                return Literal(label.removeprefix("Literal "))
            if label == "KleeneStar":
                self.assertEqual(set(children), {"operand"})
                return KleeneStar(tree(children["operand"]))
            self.assertEqual(set(children), {"left", "right"})
            kind = {"Concat (.)": Concatenation, "Alternation": Alternation}[label]
            return kind(tree(children["left"]), tree(children["right"]))

        self.assertEqual(tree("root"), parse(expression))
        nodes, edges = flowchart(source("regex-pipeline"))
        self.assertEqual(edges[0], ("expression", "compile_regex", "nfa"))
        word = edges[1][1].removeprefix("accepts with input ")
        self.assertEqual(str(accepts(compile_regex(nodes["expression"][1].removeprefix("Expression: ")), word)), nodes["result"][1])

    def test_inventory_accounts_for_every_source_asset_and_lesson_image(self):
        self.assertEqual(len(FIGURES), len(CATALOG["figures"]))
        inventory = CATALOG["inventory"]
        original = inventory["originalConceptualBlocks"]
        self.assertEqual(len(original), 27)
        self.assertEqual(len({item["figure"] for item in original}), 20)
        declared = {(entry["id"], placement["path"]): placement["alt"]
                    for entry in FIGURES.values() for placement in entry["placements"]}
        accounted = [(item["figure"], item["path"])
                     for item in original + inventory["additionalPlacements"]]
        self.assertEqual(len(accounted), len(set(accounted)))
        self.assertEqual(set(declared), set(accounted))
        self.assertEqual({str(path.relative_to(ROOT)) for path in (ROOT / ".omm").rglob("*.mmd")},
                         {entry["source"] for entry in FIGURES.values()})
        self.assertEqual({str(path.relative_to(ROOT)) for path in (ROOT / "site/public/diagrams").glob("*.svg")},
                         {entry["asset"] for entry in FIGURES.values()})
        by_url = {"/JAutomata/diagrams/" + Path(entry["asset"]).name: entry["id"] for entry in FIGURES.values()}
        actual = {}
        for path in (ROOT / "docs").rglob("*.md"):
            # Code samples illustrate markup; only actual lesson images count.
            document = re.sub(r"(?ms)^(```|~~~).*?^\1\s*$", "", path.read_text())
            parser = DiagramImages()
            parser.feed(document)
            for image in parser.images:
                self.assertIn(image["src"], by_url)
                self.assertIn("diagram", image.get("class", "").split())
                key = (by_url[image["src"]], str(path.relative_to(ROOT)))
                self.assertNotIn(key, actual, f"Duplicate lesson image: {key}")
                actual[key] = image.get("alt")
        self.assertEqual(actual, declared)
        self.assertFalse(inventory["exclusions"])

    def test_all_svgs_have_accessible_metadata_and_resolved_stable_ids(self):
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        for identifier, entry in FIGURES.items():
            with self.subTest(figure=identifier):
                text = (ROOT / entry["asset"]).read_text()
                svg = ET.fromstring(text)
                self.assertEqual(svg.attrib["role"], "img")
                self.assertEqual(svg.attrib["id"], identifier)
                self.assertEqual(svg.find("svg:title", namespace).text, entry["title"])
                self.assertEqual(svg.find("svg:desc", namespace).text, (ROOT / entry["description"]).read_text().strip())
                ids = [element.attrib["id"] for element in svg.iter() if "id" in element.attrib]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertTrue(all(value == identifier or value.startswith(identifier + "-") for value in ids))
                self.assertEqual(svg.attrib["aria-labelledby"].split(), [identifier + "-title", identifier + "-description"])
                # Check actual element references. Mermaid also emits unused theme
                # CSS (e.g. neo gradients) for shapes absent from sequence diagrams.
                for element in svg.iter():
                    for attribute, value in element.attrib.items():
                        for reference in re.findall(r"url\(#([^)]*)\)", value):
                            self.assertIn(reference, ids)
                        if attribute.endswith("href") and value.startswith("#"):
                            self.assertIn(value[1:], ids)
                self.assertNotRegex(text, r"<(?:script|foreignObject)\b|\bon\w+=")
                self.assertIn("data:font/woff2;base64,", text)


if __name__ == "__main__":
    unittest.main()
