"""Generate the delimited public API section in docs/python-api.md.

The authored introduction stays outside the markers.  This script owns only the
section between them, which makes generated reference drift visible in review.
Run with ``--check`` to fail instead of rewriting stale output.
"""

from __future__ import annotations

import argparse
import inspect
from pathlib import Path
import sys
from typing import Any, Iterable

import jautomata
from jautomata import model


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "python-api.md"
START = "<!-- GENERATED API REFERENCE: START -->"
END = "<!-- GENERATED API REFERENCE: END -->"

PUBLIC_OBJECTS: tuple[tuple[str, Any, tuple[str, ...]], ...] = (
    (
        "jautomata",
        jautomata,
        ("RegexSyntaxError", "compile_regex", "epsilon_closure", "accepts", "to_dfa"),
    ),
    ("jautomata.model", model, ("Transition", "Automaton")),
)


def _source_link(value: Any) -> str:
    """Return a stable repository-relative link for an inspected public object."""
    source = Path(inspect.getsourcefile(value) or "")
    if not source:
        raise RuntimeError(f"cannot locate source for {value!r}")
    _, line = inspect.getsourcelines(value)
    relative = source.relative_to(ROOT).as_posix()
    return f"../{relative}#L{line}"


def _docstring(value: Any) -> str:
    """Format an explanatory docstring as readable Markdown without editing it."""
    text = inspect.getdoc(value)
    if not text:
        raise RuntimeError(f"public API {value!r} needs an explanatory docstring")
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines())


def _signature(name: str, value: Any) -> str:
    """Render a public signature with its name once and no environment-specific path."""
    return f"{name}{inspect.signature(value)}"


def render_reference() -> str:
    """Render deterministic Markdown from the declared public API boundary."""
    sections = [
        START,
        "## Generated API reference",
        "",
        "This section is generated from public Python signatures and explanatory",
        "docstrings. Do not edit inside these markers; run",
        "`uv run --project python python python/scripts/generate_api_docs.py` instead.",
    ]
    for module_name, module, names in PUBLIC_OBJECTS:
        sections.extend(("", f"### `{module_name}`"))
        for name in names:
            value = getattr(module, name)
            sections.extend(
                (
                    "",
                    f"#### `{name}`",
                    "",
                    f"**Signature:** `{_signature(name, value)}`",
                    "",
                    f"**Source:** [{module_name}]({_source_link(value)})",
                    "",
                    _docstring(value),
                )
            )
    sections.extend(("", END, ""))
    return "\n".join(sections)


def rendered_document(current: str) -> str:
    """Replace exactly the generated block while preserving all authored content."""
    if START not in current:
        if END in current:
            raise RuntimeError("API document has an end marker without a start marker")
        return current.rstrip() + "\n\n" + render_reference()
    prefix, remainder = current.split(START, 1)
    if END not in remainder:
        raise RuntimeError("API document has a generated start marker without an end marker")
    _, suffix = remainder.split(END, 1)
    return prefix.rstrip() + "\n\n" + render_reference() + suffix.lstrip("\n")


def main(arguments: Iterable[str] | None = None) -> int:
    """Generate the API reference, or return nonzero when ``--check`` finds drift."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when output is stale")
    options = parser.parse_args(arguments)
    expected = rendered_document(OUTPUT.read_text())
    actual = OUTPUT.read_text()
    if actual == expected:
        print(f"API reference is current: {OUTPUT.relative_to(ROOT)}")
        return 0
    if options.check:
        print(f"API reference is stale: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    OUTPUT.write_text(expected)
    print(f"Generated API reference: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
