# Tutorial: check errors and count actual work products

**Goal:** verify error classes and positions, then relate measured graph sizes to linear construction and possible exponential subset growth.

**Prerequisites:** [validation and complexity theory](../theory/validation-complexity.md), [parsing](../theory/parsing.md) and [subset construction](../theory/subset-construction.md).

**Setup:** use [Getting started](../getting-started.md). Save this complete program as `validation_demo.py` in the repository root:

~~~sh
uv run --project python python validation_demo.py
~~~

## Predict before running

Positions start at zero. In `a|`, the missing operand is detected at position 2, just beyond the final character. In `ab`, the missing dot is detected at the second literal, position 1. Predict the positions for empty expression, `(a`, `()` and `*a`.

For a chain of `k` literal `a` fragments, predict `2k` states and `2k − 1` transitions. Each literal contributes one edge; each of the `k − 1` concatenations contributes an epsilon edge. These are structural counts, not elapsed-time measurements.

## Run the complete program

~~~python
from jautomata import (
    accepts, compile_regex, epsilon_closure, to_dfa,
)
from jautomata.model import Automaton, Transition
from jautomata.regex import RegexSyntaxError, to_postfix

syntax_cases = (("", 0), ("ab", 1), ("a|", 2),
                ("(a", 2), ("()", 1), ("*a", 0))
for expression, position in syntax_cases:
    try:
        compile_regex(expression)
    except RegexSyntaxError as error:
        assert error.expression == expression
        assert error.position == position
        assert isinstance(error, ValueError)
    else:
        raise AssertionError("Expected syntax error: " + repr(expression))

valid = Automaton({0}, 0, set(), set())
bad_calls = (
    (TypeError, lambda: compile_regex(12)),
    (TypeError, lambda: Transition(True, "a", 1)),
    (TypeError, lambda: Transition(0, 7, 1)),
    (ValueError, lambda: Transition(0, "", 1)),
    (ValueError, lambda: Transition(0, "ab", 1)),
    (ValueError, lambda: Automaton(set(), 0, set(), set())),
    (ValueError, lambda: Automaton({0}, 1, set(), set())),
    (ValueError, lambda: Automaton({0}, 0, {1}, set())),
    (ValueError, lambda: Automaton({0}, 0, set(), {Transition(0, "a", 1)})),
    (TypeError, lambda: Automaton({0}, 0, set(), {"edge"})),
    (ValueError, lambda: epsilon_closure(valid, {1})),
    (TypeError, lambda: epsilon_closure(valid, {True})),
    (TypeError, lambda: accepts(valid, 1)),
    (TypeError, lambda: to_dfa("a")),
)
for expected_type, operation in bad_calls:
    try:
        operation()
    except Exception as error:
        assert type(error) is expected_type, (expected_type, type(error))
    else:
        raise AssertionError("Expected " + expected_type.__name__)

# No final states and no edges form a valid machine for the empty language.
assert not accepts(valid, "")
assert not accepts(valid, "a")
assert epsilon_closure(valid, set()) == frozenset()
assert epsilon_closure(valid, {0}) == frozenset({0})
# Empty regex syntax differs from a valid regex that accepts empty input.
assert accepts(compile_regex("a*"), "")
assert not accepts(compile_regex("a"), "z")

print("syntax checks:", len(syntax_cases))
print("model/API checks:", len(bad_calls))
print("k tokens states transitions")
for count in (1, 2, 4):
    expression = ".".join("a" for _ in range(count))
    tokens = to_postfix(expression)
    machine = compile_regex(expression)
    assert len(tokens) == 2 * count - 1
    assert len(machine.states) == 2 * count
    assert len(machine.transitions) == 2 * count - 1
    assert accepts(machine, "a" * count)
    assert not accepts(machine, "a" * (count - 1))
    print(count, len(tokens), len(machine.states), len(machine.transitions))

nfa = compile_regex("(a.b|a*.c)+")
dfa = to_dfa(nfa)
v, d, alphabet_size = len(nfa.states), len(dfa.states), len(nfa.alphabet)
assert (v, d, alphabet_size) == (14, 6, 3)
assert d <= 2 ** v
assert len(dfa.transitions) == d * alphabet_size == 18
for state in dfa.states:
    for symbol in nfa.alphabet:
        matches = [edge for edge in dfa.transitions
                   if edge.source == state and edge.symbol == symbol]
        assert len(matches) == 1
print("DFA: states=", d, " edges=", len(dfa.transitions),
      " subset bound=", 2 ** v, sep="")
~~~

Expected output:

~~~text
syntax checks: 6
model/API checks: 14
k tokens states transitions
1 1 2 1
2 3 4 3
4 7 8 7
DFA: states=6 edges=18 subset bound=16384
~~~

## Interpret one failure at a time

The syntax checks verify both the error class and the stored position. The model/API checks distinguish a wrong **type** from a value that has the right broad type but violates a constraint. For example, `"ab"` is a string but cannot label one consuming edge; state 1 is an integer but cannot be the start of a machine whose only state is 0.

The valid one-state machine rejects every word because its final set is empty. Rejection is an ordinary result. The program's malformed expressions and graphs fail earlier, before they can describe a language to recognize.

## Interpret the measurements honestly

The chain counts match a per-token construction argument. The final DFA has 6 states, far below its subset upper bound of 16,384. That gap is normal: most mathematical subsets are not reachable. Totality explains its exact 18 edges, because every one of 6 states has one edge for each of 3 source symbols.

None of these counts measures closure edge visits or elapsed time. The library constructs adjacency maps once for each public `accepts` or `epsilon_closure` call; processing only a small reached portion does not erase that setup. The [theory lesson](../theory/validation-complexity.md#setup-is-work-even-when-little-is-reached) separates these costs explicitly.

## Exercise: count a different chain

For `a.a.a.a.a`, predict the postfix token, state and transition counts. Then decide whether a no-final-state graph should raise an error.

<details>
<summary>Answer and reason</summary>

Five literals and four dots give 9 postfix tokens, 10 states and 9 edges: five consuming and four epsilon. A graph with no final states is valid as long as its structural constraints hold. It represents the empty language and returns false for every word. The empty language is different from the language containing only the empty word.

</details>

**Common mistake:** treating `2^V` as the number of DFA states that must be allocated. The converter discovers reachable subsets. Another is describing one result's six states as a general complexity bound.

## Source connection

**Commentary:** [syntax error attributes](../../python/src/jautomata/regex.py#L21-L38), [postfix-builder linear-work rationale](../../python/src/jautomata/thompson.py#L48-L55) and [subset bound](../../python/src/jautomata/subsets.py#L78-L86).

**Verified implementation:** [position-aware checks](../../python/src/jautomata/regex.py#L99-L173), [Boolean-ID exclusion](../../python/src/jautomata/model.py#L27-L31), [graph constraints](../../python/src/jautomata/model.py#L101-L125), and [every-symbol DFA loop](../../python/src/jautomata/subsets.py#L106-L117). **Supplement:** the error matrix, count family and assertions are experiments designed for this lesson; they do not change runtime behavior.

## Recap and stop point

You checked six syntax failures, fourteen structural/type failures, a valid empty-language graph, exact construction sizes and complete-DFA counts.

**Stop here:** explain why `(a` reports its error at the end, and why six generated subsets do not contradict an exponential upper bound. **Resume:** use [Practica 1](../labs/practica1.md) to reconstruct a historical graph and compare it with an independent language predicate.
