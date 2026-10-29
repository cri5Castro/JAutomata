---
title: Complete learning map
description: Choose one paired topic at a time, then return here for the next small step.
---

# Complete learning map

This map is the front door to the full course: fifteen paired explanations and
runnable tutorials, followed by four historical source labs. Each pair has two
parts: read the **theory** for one idea, then run the matching **tutorial**.

> **Choose one topic, not the whole map.** Finish a tutorial's assertions before
> moving on. If you pause, bookmark the current tutorial or its stop point, then
> return here to choose the next topic.

## 1. Read the model and the regex language

| Pair | Read | Run |
| --- | --- | --- |
| 1 | [Finite automata and languages](theory/automata.md) | [Construct a small automaton](tutorials/automata.md) |
| 2 | [Regular expressions and language operations](theory/regex.md) | [Compile supported regexes](tutorials/regex.md) |
| 3 | [Parsing, postfix notation and syntax trees](theory/parsing.md) | [Trace parsing and errors](tutorials/parsing.md) |

## 2. Build Thompson fragments

| Pair | Read | Run |
| --- | --- | --- |
| 4 | [Literal fragments](theory/literal.md) | [Inspect one literal](tutorials/literal.md) |
| 5 | [Concatenation](theory/concatenation.md) | [Follow an epsilon link](tutorials/concatenation.md) |
| 6 | [Union](theory/union.md) | [Keep both alternatives](tutorials/union.md) |
| 7 | [Kleene star](theory/kleene-star.md) | [Test the bypass and cycle](tutorials/kleene-star.md) |
| 8 | [Positive closure](theory/positive-closure.md) | [Compare plus and star](tutorials/positive-closure.md) |

## 3. Recognize words and make a DFA

| Pair | Read | Run |
| --- | --- | --- |
| 9 | [Epsilon closure](theory/epsilon-closure.md) | [Trace reachability](tutorials/epsilon-closure.md) |
| 10 | [NFA simulation](theory/nfa-simulation.md) | [Retain every active state](tutorials/nfa-simulation.md) |
| 11 | [Subset construction](theory/subset-construction.md) | [Build full subsets](tutorials/subset-construction.md) |
| 12 | [Complete DFAs and sinks](theory/complete-dfa.md) | [Check total transitions](tutorials/complete-dfa.md) |

## 4. Explain the implementation choices

| Pair | Read | Run |
| --- | --- | --- |
| 13 | [Identity, equality and immutable graphs](theory/identity.md) | [Compare values and languages](tutorials/identity.md) |
| 14 | [Pure execution and work lists](theory/pure-execution.md) | [Repeat independent runs](tutorials/pure-execution.md) |
| 15 | [Validation and complexity](theory/validation-complexity.md) | [Measure the work that matters](tutorials/validation-complexity.md) |

## Capstone labs

Use these after the matching topics above. They preserve the historical Java
examples as source evidence while the Python programs provide the runnable
checks.

1. [Practica 1: reconstruct and recognize a hand-built NFA](labs/practica1.md)
2. [Practica 2: compile a compound expression](labs/practica2.md)
3. [Practica 3: follow regex through NFA and DFA](labs/practica3.md)
4. [Main: read and verify historical experiments](labs/main.md)

## Resume routes

- Need one fast refresher? Use the [short pipeline walkthrough](tutorial.md).
- Need syntax before construction? Resume at [regex](theory/regex.md).
- Need the NFA/DFA connection? Resume at [subset construction](theory/subset-construction.md).
- Need provenance for a claim? Open the [source curriculum map](reference/source-curriculum.md).
