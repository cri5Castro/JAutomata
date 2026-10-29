# JAutomata

JAutomata is a compact, documented implementation of regular-expression
compilation, epsilon-NFA recognition, and deterministic subset construction.
The repository preserves the original Java coursework as source evidence and
provides a tested Python package with immutable automata values.

## What it does

- Compiles explicit-concatenation regexes into fresh Thompson epsilon-NFAs.
- Recognizes text with complete, cycle-safe epsilon closure.
- Converts NFAs to complete deterministic DFAs with a reachable empty-subset
  sink when needed.
- Keeps model values immutable: recognition and conversion never store mutable
  visited or acceptance flags.

The supported regex operators are explicit . concatenation, | union, postfix
* and +, and parentheses. Literals are one Unicode character except . | * + ( ).
There are no escapes, classes, wildcard, implicit concatenation, or regex-level
epsilon token.

## Start here

Python 3.10 or newer is required. The project environment is verified with
Python 3.13.14; final wheel verification also records its tested clean-runtime
version in the verification report.

~~~sh
uv sync --project python
uv run --project python python
uv run --project python python python/examples/regex_pipeline.py
uv run --project python python -m unittest discover -s python/tests -v
~~~

The second command starts an interactive Python session with the packaged
project available. The example prints NFA and DFA acceptance for accepting,
rejecting, and empty inputs. The package has no runtime dependencies.

New to automata? Follow the short, source-linked learning path:

1. [Foundations](docs/learn/foundations.md) defines the notation and a run.
2. [Regex syntax](docs/learn/regex-syntax.md) explains the required explicit
   dot before you compile anything.
3. [Thompson construction](docs/learn/thompson.md),
   [epsilon closure](docs/learn/epsilon-closure.md), and
   [subset construction](docs/learn/subset-construction.md) build the pipeline
   one trace at a time.
4. [Practice](docs/practice/exercises.md) has revealable solutions; use the
   [glossary](docs/reference/glossary.md) as a quick reference.

The published learning site is served at
[cri5castro.github.io/JAutomata](https://cri5castro.github.io/JAutomata/). Its
production build, browser checks, and link checks are documented in
[site/README.md](site/README.md).

## Repository layout

- [src/](src/) is the preserved Java reference. Its
  [regex builder](src/ExpresionRegularToAFN/ConstructorDeAutomatas.java),
  [parser](src/ExpresionRegularToAFN/ShuntingYard.java), and
  [subset converter](src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java) explain the
  original educational design.
- [python/](python/) contains the installable jautomata package, executable
  example, and standard-library unittest suite.
- [docs/](docs/index.md) is the canonical Markdown source for the learning
  path, tutorial, API reference, algorithms, compatibility contract, and
  source-linked Java audit.

Java execution is unavailable in this environment because no usable Java runtime
is installed. The Java source remains unchanged and is documented as reference,
not used as the Python correctness oracle.
