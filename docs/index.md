---
title: Learn finite automata without losing the thread
description: A calm, rigorous path from explicit regex syntax to complete DFAs.
template: splash
hero:
  title: Make every state visible.
  tagline: Learn the automata pipeline in short, connected steps — then inspect the formal details when you are ready.
  actions:
    - text: Start with foundations
      link: /JAutomata/learn/foundations/
    - text: Open the glossary
      link: /JAutomata/reference/glossary/
---

> **One idea at a time.** Choose one lesson, run its assertions, and pause at
> the worked trace. Formal definitions and complexity notes stay available, but
> never block the first pass.

# Documentation index

This is the canonical authored Markdown documentation. Start with one short
lesson, run its assertions, then continue; formal detail is signposted instead
of placed before the first working example.

## Start here

- [Getting started](getting-started.md) installs, runs, and tests the package.
- [Foundations](learn/foundations.md) defines the notation, prerequisites, and
  the acceptance rule through one two-state trace.

## Learn

1. [Regex syntax](learn/regex-syntax.md): explicit concatenation and precedence.
2. [Thompson construction](learn/thompson.md): compile postfix fragments.
3. [Epsilon closure and NFA evaluation](learn/epsilon-closure.md): safely retain
   all possible runs.
4. [Subset construction](learn/subset-construction.md): create a complete DFA
   and understand its empty-subset sink.
5. [Tutorial](tutorial.md): apply the pipeline to the existing compound example.

## Practice

- [Exercises](practice/exercises.md) progress from explicit dots to the compound
  NFA/DFA pipeline; every solution is revealable.

## Reference

- [Glossary](reference/glossary.md) is a compact notation and API lookup.
- [Python API](python-api.md) gives public contracts, invariants, and errors.
- [Algorithms](algorithms.md) gives complexity and Java correspondence.
- [Architecture](architecture.md) describes package and reference-tree boundaries.
- [Compatibility contract](compatibility.md) is the normative grammar and
  complete-DFA policy.
- [Java reference behavior](java-reference.md) inventories all eleven Java
  sources with exact source links.

The preserved Java tree is [source on GitHub](https://github.com/cri5Castro/JAutomata/tree/master/src). The installable package, examples,
and tests are [in the Python source on GitHub](https://github.com/cri5Castro/JAutomata/tree/master/python).
