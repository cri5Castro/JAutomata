# Architecture

## Repository layers

The Java and Python trees have different roles.

- src/ is the preserved Java reference: mutable model objects, the explicit-dot
  shunting-yard parser, Thompson construction, subset conversion, and three
  practice programs. See [Automata](../src/Model/AutomataStructure/Automata.java),
  [ShuntingYard](../src/ExpresionRegularToAFN/ShuntingYard.java), and
  [ContructorAFNtoAFD](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java).
- python/ is the installable implementation with immutable model values,
  iterative parsing/construction, simulation, subset conversion, examples, and
  standard-library tests.

~~~text
python/
├── examples/regex_pipeline.py
├── src/jautomata/
│   ├── model.py
│   ├── regex.py
│   ├── thompson.py
│   ├── simulation.py
│   └── subsets.py
└── tests/
~~~

## Pipeline

~~~mermaid
flowchart LR
  R[Explicit regex] --> P[Iterative parser]
  P --> T[Thompson epsilon-NFA]
  T --> E[epsilon_closure and accepts]
  T --> S[BFS subset construction]
  S --> D[Complete DFA]
  D --> E
~~~

The parser validates explicit dots and produces postfix tokens without recursion.
Thompson construction assigns fresh integer state IDs for every compilation.
Simulation builds local adjacency maps and state sets. Subset conversion assigns
DFA IDs in breadth-first order over sorted input symbols.

## Model invariants

Automaton contains a non-empty immutable state set, a start state in that set,
a final-state subset, and immutable Transition values whose endpoints belong to
the set. A transition label is one Unicode character or None; None is internal
epsilon and does not appear in alphabet.

The DFA returned by to_dfa is epsilon-free and complete over the source NFA
alphabet. If a discovered subset has no destination for a symbol, the empty
subset is represented as a reachable sink. No DFA minimization is performed.

Read [algorithms](algorithms.md) for complexity and Java correspondence, and
[python-api](python-api.md) for callable contracts.
