---
title: "Subset construction: make every choice explicit"
---

import TracePlayer from '../../../components/TracePlayer.astro';

**Objective:** convert an epsilon-NFA to an equivalent complete DFA and explain
when the empty-subset sink appears.

A DFA state represents an entire epsilon-closed set of NFA states. Start with
`closure({nfa.start_state})`. For every input symbol, move from all members,
close the result, and assign that resulting set a DFA ID. The subset is final
when *any* member is an NFA final.

## Worked trace: `a|b`

The Thompson NFA starts by epsilon-branching to an `a` fragment and a `b`
fragment. Its start subset contains both branch entries. On `a`, only the `a`
branch reaches its final-side state; on `b`, only the `b` branch does.

<img class="diagram" src="/JAutomata/diagrams/subset-construction.svg" alt="DFA for a|b: D0 goes on a to accepting D1 and on b to accepting D2; unmatched transitions lead to empty-set sink D-empty." />

| DFA state | Represents | On the matching symbol |
| --- | --- | --- |
| `D0` | the epsilon-closed NFA start set | reaches `D1` on `a`, `D2` on `b` |
| `D1`, `D2` | a set containing a final NFA state | accepts after one input character |
| `D∅` | the empty subset | remains a non-final sink |

<TracePlayer trace="subset-union" />

~~~python
from jautomata import accepts, compile_regex, to_dfa

nfa = compile_regex("a|b")
dfa = to_dfa(nfa)
assert [accepts(dfa, text) for text in ("", "a", "b", "ab")] == [False, True, True, False]
assert all(transition.symbol is not None for transition in dfa.transitions)
~~~

**Expected output:** the assertions succeed. The DFA has no epsilon edges and
recognizes the same language as the NFA.

### The sink is a real subset

If a discovered subset has no move on an alphabet symbol, its target is `{}`:
the empty set. The converter includes this subset as a reachable non-final sink
when needed and gives it one transition per source-alphabet symbol. This is why
the returned DFA is *complete* rather than merely deterministic.

### Common mistake

Do not mark a DFA state final only when a special “kernel” state is final. A
DFA subset is final whenever it intersects the input NFA's complete final set,
including the initial subset.

<details>
<summary>Exercise — why can <code>to_dfa</code> be much larger than its NFA?</summary>

An NFA with `N` states can have up to `2**N` reachable subsets. Most practical
examples are smaller, but the exponential worst case is real. The converter
does not minimize the result; it stops after reachable subsets are processed.

~~~python
from jautomata import accepts, compile_regex, to_dfa

source = compile_regex("a.b*")
converted = to_dfa(source)
for text in ("", "a", "ab", "abb", "b"):
    assert accepts(source, text) == accepts(converted, text)
~~~
</details>

## Deeper: stable breadth-first output and complexity

The converter processes the source alphabet in sorted order and discovers
subsets breadth first. Its numeric DFA IDs and transition set are therefore
repeatable for a fixed immutable input. For `N` NFA states and `A` symbols,
at most `2**N` subsets are reachable; every discovered subset processes all
`A` symbols. No minimization is requested or performed.

The Java converter describes the same work-list idea
([commentary](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L35-L79)),
but its recursive closure and inconsistent finality are defects. Python's
[`to_dfa`](../python-api.md#to_dfaautomaton) keeps full immutable subsets and
uses the complete-sink policy described in
[Compatibility](../compatibility.md#required-semantic-behavior).

**Next:** test your understanding in [Practice](../practice/exercises.md), or
look up notation in the [Glossary](../reference/glossary.md).
