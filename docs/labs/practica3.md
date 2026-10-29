# Practica 3: follow a regex through every DFA subset

**Goal:** connect `(a.b|a*.c)+` to its Thompson fragments, its reachable closed subsets and a complete DFA.

**Prerequisites:** [concatenation](../theory/concatenation.md), [union](../theory/union.md), [star](../theory/kleene-star.md), [plus](../theory/positive-closure.md), [subset construction](../theory/subset-construction.md) and [complete DFAs](../theory/complete-dfa.md).

The existing [regex-to-NFA-to-DFA tutorial](../tutorial.md) is the shorter starting point. This separate lab expands it with construction and subset traces; the original route remains available.

## Source and block meaning

The active [Practica3Main example](../../src/Practica3/Practica3Main.java#L10-L23) asks for an equivalent DFA, constructs `(a.b|a*.c)+`, and prints the NFA followed by its conversion. The block-language explanation here is supplemental reasoning from that expression.

Read the figure: each branch completes one block before finishing or repeating. The boxes show expression blocks, not individual NFA states.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Practica 3: repeat ab or an a-star-c block, scrollable diagram" style="--diagram-width: 768px">
  <img class="diagram" src="/JAutomata/diagrams/practica3-blocks.svg" alt="Choose ab or zero or more a followed by c; finish after one complete block or repeat another block. Every block consumes input.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/practica3-blocks.svg">Open full-size diagram</a></p>

Examples of single blocks are `ab`, `c`, `ac` and `aac`. `abc` splits into `ab` followed by `c`; `acab` splits into `ac` followed by `ab`. Every block consumes at least one character, so the outer plus cannot accept empty input. The nullable inner `a*` is only part of the second block and does not remove its required `c`.

## Build the NFA in small pieces

Postfix is `a b . a * c . | +`. The actual Python allocator produces these fragments:

| Construction | Entry → exit | What changes |
| --- | --- | --- |
| literal `a`, literal `b`, dot | `0 → 3` | `0 -a→ 1 -ε→ 2 -b→ 3` |
| second literal `a`, then star | `6 → 7` | Literal `4 -a→ 5`, with bypass and repeat epsilon edges |
| literal `c`, then dot | `6 → 9` | Connect 7 to 8 by epsilon; `8 -c→ 9` |
| union | `10 → 11` | Entry branches to 0 and 6; exits 3 and 9 join at 11 |
| outer plus | `12 → 13` | Enter at 10; from 11 repeat at 10 or exit at 13 |

There is no epsilon bypass from 12 to 13. The full graph has 14 states and 17 edges; only 13 is final. These IDs are the current Python construction's labels, not a claim that the historical Java graph uses identical numbering.

## Trace one word before constructing the table

Let `C(S)` mean epsilon closure of state set `S`. After each consumed character, take all matching moves, then apply `C`.

| Prefix of `abc` | Closed active set | Final? |
| --- | --- | --- |
| empty | `{0, 4, 6, 7, 8, 10, 12}` | no |
| `a` | `{1, 2, 4, 5, 7, 8}` | no |
| `ab` | `{0, 3, 4, 6, 7, 8, 10, 11, 13}` | yes |
| `abc` | `{0, 4, 6, 7, 8, 9, 10, 11, 13}` | yes |

After `ab`, the repeat edge has already reopened the next block. That is why `c` can begin immediately without an input separator.

## The full reachable subset table

Each row is one DFA state. Numbering follows breadth-first discovery with alphabet order `a`, `b`, `c`; numbers in the move columns refer to row IDs.

| DFA ID | Full NFA subset | `a` | `b` | `c` | Final? |
| --- | --- | --- | --- | --- | --- |
| 0 | `{0, 4, 6, 7, 8, 10, 12}` | 1 | 2 | 3 | no |
| 1 | `{1, 2, 4, 5, 7, 8}` | 4 | 5 | 3 | no |
| 2 | `{}` | 2 | 2 | 2 | no |
| 3 | `{0, 4, 6, 7, 8, 9, 10, 11, 13}` | 1 | 2 | 3 | yes |
| 4 | `{4, 5, 7, 8}` | 4 | 2 | 3 | no |
| 5 | `{0, 3, 4, 6, 7, 8, 10, 11, 13}` | 1 | 2 | 3 | yes |

Row 2 is the reachable empty-subset sink. It appears because, for example, the start subset has no `b` move. Every row has exactly one move on each of three symbols, so the complete DFA has 18 edges. A symbol outside `{a, b, c}` is outside this totality guarantee and rejects.

**Prediction:** row 1 represents reading `a`, and row 4 represents reading `aa`. Why does only row 1 allow a `b` move to a final state?

## Run the complete construction and table checks

Follow [Getting started](../getting-started.md), save as `practica3_lab.py` in the repository root, then run:

~~~sh
uv run --project python python practica3_lab.py
~~~

~~~python
from itertools import product
from jautomata import accepts, compile_regex, epsilon_closure, to_dfa
from jautomata.regex import to_postfix

expression = "(a.b|a*.c)+"
nfa = compile_regex(expression)
dfa = to_dfa(nfa)
assert "".join(to_postfix(expression)) == "ab.a*c.|+"
assert (len(nfa.states), len(nfa.transitions)) == (14, 17)
assert (len(dfa.states), len(dfa.transitions)) == (6, 18)
assert nfa.final_states == frozenset({13})
assert dfa.final_states == frozenset({3, 5})
alphabet = tuple(sorted(nfa.alphabet))
assert alphabet == ("a", "b", "c")

# These are the table's teaching data, checked against the actual NFA and DFA.
subsets = (
    frozenset({0, 4, 6, 7, 8, 10, 12}),
    frozenset({1, 2, 4, 5, 7, 8}),
    frozenset(),
    frozenset({0, 4, 6, 7, 8, 9, 10, 11, 13}),
    frozenset({4, 5, 7, 8}),
    frozenset({0, 3, 4, 6, 7, 8, 10, 11, 13}),
)
rows = ((1, 2, 3), (4, 5, 3), (2, 2, 2),
        (1, 2, 3), (4, 2, 3), (1, 2, 3))
assert dfa.states == frozenset(range(len(subsets)))
assert subsets[dfa.start_state] == epsilon_closure(nfa, {nfa.start_state})

print("postfix:", "".join(to_postfix(expression)))
print("NFA states/edges:", len(nfa.states), len(nfa.transitions))
print("DFA states/edges:", len(dfa.states), len(dfa.transitions))
print("state a b c final")
for state, subset in enumerate(subsets):
    assert epsilon_closure(nfa, subset) == subset
    assert (state in dfa.final_states) == bool(subset & nfa.final_states)
    for symbol, target in zip(alphabet, rows[state]):
        moved = {edge.target for edge in nfa.transitions
                 if edge.source in subset and edge.symbol == symbol}
        assert epsilon_closure(nfa, moved) == subsets[target]
        actual = [edge.target for edge in dfa.transitions
                  if edge.source == state and edge.symbol == symbol]
        assert actual == [target]  # One edge: both determinism and totality.
    print(state, *rows[state], state in dfa.final_states)

current = subsets[0]
for symbol, expected_id in zip("abc", (1, 5, 3)):
    moved = {edge.target for edge in nfa.transitions
             if edge.source in current and edge.symbol == symbol}
    current = epsilon_closure(nfa, moved)
    assert current == subsets[expected_id]

cases = {"": False, "ab": True, "c": True, "ac": True, "abc": True,
         "acab": True, "cc": True, "a": False, "b": False,
         "ca": False, "aab": False, "x": False}
for word, expected in cases.items():
    assert accepts(nfa, word) is expected
    assert accepts(dfa, word) is expected

checked = 0
for length in range(5):
    for letters in product(alphabet, repeat=length):
        word = "".join(letters)
        assert accepts(nfa, word) == accepts(dfa, word)
        checked += 1
assert checked == 121
print("bounded words checked:", checked)
~~~

Expected output:

~~~text
postfix: ab.a*c.|+
NFA states/edges: 14 17
DFA states/edges: 6 18
state a b c final
0 1 2 3 False
1 4 5 3 False
2 2 2 2 False
3 1 2 3 True
4 4 2 3 False
5 1 2 3 True
bounded words checked: 121
~~~

## Interpret what was established

The table checks more than selected words: every displayed subset is closed, every move agrees with the source NFA, finality agrees with membership of NFA final 13, and each DFA state has exactly one outgoing edge per source symbol. The program then tests NFA/DFA agreement on 121 words of lengths 0–4.

Bounded agreement alone is not a proof of general equivalence. The reason subset construction works is the prefix invariant: after any prefix, the DFA row represents exactly the NFA's closed active set. The table checks the initial correspondence and every row's one-character correspondence for this instance; the [theory lesson](../theory/subset-construction.md) explains the general argument.

<details>
<summary>Optional depth: distinct subsets can have the same future behavior</summary>

Rows 3 and 5 are different full subsets, but both are final and have the same outgoing target rows on all three symbols. For this table, they therefore accept the same suffixes: empty suffix succeeds in both, and a nonempty suffix takes the same first transition before continuing. Subset construction still keeps them separate because it identifies states by set membership. It does not claim to produce a smallest DFA; minimization is outside this lab.

</details>

## Exercise: distinguish `ab` from `aab`

Explain why row 1 reaches row 5 on `b`, while row 4 reaches the sink on `b`. Use the NFA state sets, not just the printed Boolean results.

<details>
<summary>Answer and reason</summary>

After one `a`, row 1 still contains state 2, the source of the `b` edge in the `a.b` alternative. After a second `a`, that branch has died; row 4 contains only states from the `a*.c` branch. That branch can finish only with `c`. Consequently `ab` accepts while `aab` rejects. `aac` would accept.

</details>

**Common mistake:** treating the outer plus as permission to stop inside a block, or treating the inner star as making the entire expression nullable. Complete blocks still need `ab` or a final `c`.

## Source connection and stop point

**Commentary and active example:** [Practica 3's equivalence goal and expression](../../src/Practica3/Practica3Main.java#L10-L23). **Verified implementation:** [Thompson fragment construction](../../python/src/jautomata/thompson.py#L56-L92) and [closed-subset discovery, finality and transitions](../../python/src/jautomata/subsets.py#L91-L124). **Supplement:** the block interpretation and displayed table explain that behavior and are verified by this program.

**Recap:** a whole block returns to an accepting subset ready for another block; invalid prefixes reach the empty-subset sink. **Stop here:** trace `aca` through table rows. **Resume:** the [Main lab](main.md) separates active demonstrations from commented experiments and revisits equality.
