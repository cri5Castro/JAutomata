# Getting started

## Requirements

- Python 3.10 or newer.
- [uv](https://docs.astral.sh/uv/).
- No runtime Python dependencies.

The checked project environment uses Python 3.13.14. The package metadata
supports every compatible Python version from 3.10 onward; clean-wheel tested
versions are recorded in the verification report.

## Install and test

Run from the repository root:

~~~sh
uv sync --project python
uv run --project python python
uv run --project python python -m unittest discover -s python/tests -v
~~~

The second command starts an interactive Python session with jautomata
available through the project environment. The suite includes
model/parser/compiler/simulation/subset tests, doctests of public modules, and
executable documentation-example checks.

## Run the example

~~~sh
uv run --project python python python/examples/regex_pipeline.py
~~~

The script compiles (a.b|a*.c)+, converts it to a complete DFA, and prints
matching NFA/DFA outcomes for empty, accepting, and rejecting strings.

## First API use

~~~python
from jautomata import accepts, compile_regex, to_dfa

nfa = compile_regex("a.b*")
dfa = to_dfa(nfa)
assert accepts(nfa, "a")
assert accepts(dfa, "abb")
assert not accepts(dfa, "")
~~~

See [tutorial](tutorial.md) for a guided explanation and
[compatibility](compatibility.md) for grammar and error rules.

## Choose a next page

If finite automata are new, begin with [Foundations](learn/foundations.md).
It defines the notation before using it and introduces a one-character example
before the compound tutorial. If you already know the model, start at
[Regex syntax](learn/regex-syntax.md); use [Practice](practice/exercises.md)
after the subset-construction lesson.
