# Main: turn historical experiments into explicit checks

**Goal:** distinguish active Java execution from commented probes, reconstruct selected experiments, and avoid treating scratch equality checks as an oracle.

**Prerequisites:** [identity](../theory/identity.md), [positive closure](../theory/positive-closure.md), [subset construction](../theory/subset-construction.md), and [Practica 3](practica3.md). [Practica 1](practica1.md) covers the earlier six-state graph; [Practica 2](practica2.md) covers the other compound expression mentioned here.

**Route:** classify the source → interpret one commented expression → check independent assertions → compare with the active conversion.

## First classify what actually executes

The historical `Main.java` mixes code, block comments and line comments. Reading every visible call as an executed demonstration would give the wrong account.

| Exact source span | Status | What it contains |
| --- | --- | --- |
| [Lines 17–63](../../src/com/company/Main.java#L17-L63) | Commented block | Six-state NFA and several evaluation probes; see Practica 1. |
| [Lines 64–86](../../src/com/company/Main.java#L64-L86) | Live setup, unused by the final demo | Two three-state odd-ones graphs named `b` and `c`. |
| [Lines 91–102](../../src/com/company/Main.java#L91-L102) | Commented probes | Thompson operators, three regex examples and an alphabet check. |
| [Lines 103–138](../../src/com/company/Main.java#L103-L138) | Commented block | Subset kernels/closures and container membership experiments. |
| [Lines 140–146](../../src/com/company/Main.java#L140-L146) | Active final conversion | Compile `(a.b\|a*.c)+`, print its NFA, then print its DFA. |

The expression `((a.a+)|(c+)|(b.c*))+` appears specifically in the **commented probe at line 99**. It is the new expression studied below. It is not the argument to the active final conversion, which repeats Practica 3. The source table establishes provenance; the language derivations and Python checks are added explanations.

## Read the selected expression as blocks

The outer plus requires one or more blocks. Inside it, choose one of three forms:

| Alternative | Meaning | Smallest examples |
| --- | --- | --- |
| `a.a+` | One `a`, then at least one more `a` | `aa`, `aaa` |
| `c+` | One or more `c` | `c`, `cc` |
| `b.c*` | One `b`, then zero or more `c` | `b`, `bc`, `bcc` |

Read the figure: choose a complete block, then finish or repeat. These boxes summarize the language, rather than individual NFA states.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Main: choose and repeat complete blocks, scrollable diagram" style="--diagram-width: 808px">
  <img class="diagram" src="/JAutomata/diagrams/main-blocks.svg" alt="Choose at least two a, at least one c, or b then zero or more c; finish after one complete block or repeat another block.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/main-blocks.svg">Open full-size diagram</a></p>

Thus `b` accepts even though the complete expression uses plus: its `b.c*` block consumes one character. Empty input rejects because none of the three block forms is empty. `a` rejects because an `a` block needs at least two.

Worked decomposition of `aabcc`:

| Prefix | Completed material | What remains |
| --- | --- | --- |
| `a` | No complete `a` block yet | At least one more `a` required |
| `aa` | One `a.a+` block | May finish or begin another block |
| `aab` | `aa` followed by a minimal `b.c*` block | May finish or add `c` characters |
| `aabcc` | `aa` followed by `bcc` | Accept |

Some words have several block decompositions. For example, `bcc` can be one `b.c*` block or `b` followed by a `c+` block. Nondeterminism preserves possibilities; it does not require a unique parse into blocks to accept.

## Revisit the unused graphs and subset probes

The live setup creates an odd-ones graph with states 3, 4 and 5 and a consistently relabeled version with states 6, 7 and 8. They are different graph values but both accept odd-length all-ones words. The final Java demo does not use either graph.

Read the figure: compare the two separately titled machines. Each start, final state and transition follows the renaming.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Main: the same odd-ones language after relabeling, scrollable diagram" style="--diagram-width: 633px">
  <img class="diagram" src="/JAutomata/diagrams/main-relabeling.svg" alt="Separate graphs: start 3 reaches 4 by epsilon, then 4 and final 5 alternate on 1; renaming 3, 4, 5 to 6, 7, 8 preserves the graph and language.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/main-relabeling.svg">Open full-size diagram</a></p>

The commented subset experiment gives differently named objects the same kernel and closure labels. Its scratch container checks do not establish language equivalence, and the block is not executed. The [active Java equality method](../../src/AFDtoAFDbySubsets/Subconjunto.java#L53-L67) compares kernels; the Python converter instead keys by the full closed subset.

A small real epsilon cycle makes the distinction visible: kernels `{0}` and `{1}` are different, but if `0` and `1` reach each other by epsilon, both closures are `{0, 1}`. Those closures represent one Python DFA subset. This is an added teaching graph, not a claim that Main's symbolic labels define that graph.

## Run the complete lab

Use [Getting started](../getting-started.md), save as `main_lab.py` in the repository root, then run:

~~~sh
uv run --project python python main_lab.py
~~~

~~~python
from itertools import product
from jautomata import accepts, compile_regex, epsilon_closure, to_dfa
from jautomata.model import Automaton, Transition
from jautomata.regex import to_postfix

# Reconstruct live-but-unused setup from Main.java lines 64-86.
left = Automaton(
    {3, 4, 5}, 3, {5},
    {Transition(3, None, 4), Transition(4, "1", 5), Transition(5, "1", 4)},
)
right = Automaton(
    {6, 7, 8}, 6, {8},
    {Transition(6, None, 7), Transition(7, "1", 8), Transition(8, "1", 7)},
)
assert left != right
setup_checks = 0
for length in range(5):
    for letters in product("01", repeat=length):
        word = "".join(letters)
        expected = len(word) % 2 == 1 and set(word) <= {"1"}
        assert accepts(left, word) is expected
        assert accepts(right, word) is expected
        setup_checks += 1
assert setup_checks == 31

# A supplemental graph explains full closed-set identity with real closures.
cycle = Automaton(
    {0, 1}, 0, {1}, {Transition(0, None, 1), Transition(1, None, 0)},
)
kernel_a, kernel_b = frozenset({0}), frozenset({1})
assert kernel_a != kernel_b
closure_a = epsilon_closure(cycle, kernel_a)
closure_b = epsilon_closure(cycle, kernel_b)
assert closure_a == closure_b == frozenset({0, 1})
assert len({closure_a, closure_b}) == 1

# This expression is COMMENTED at line 99; we now test it deliberately.
selected = "((a.a+)|(c+)|(b.c*))+"
nfa = compile_regex(selected)
dfa = to_dfa(nfa)
assert "".join(to_postfix(selected)) == "aa+.c+|bc*.|+"
assert (len(nfa.states), len(nfa.transitions)) == (22, 28)
assert (len(dfa.states), len(dfa.transitions)) == (8, 24)
assert None not in nfa.alphabet
assert nfa.alphabet == frozenset("abc")
cases = {"aa": True, "aaa": True, "c": True, "cc": True,
         "b": True, "bc": True, "bcc": True, "aabcc": True,
         "": False, "a": False, "ab": False, "ba": False,
         "aca": False, "aaca": False, "x": False}
for word, expected in cases.items():
    assert accepts(nfa, word) is expected
    assert accepts(dfa, word) is expected

# This is the DIFFERENT expression used by active lines 140-146.
active_expression = "(a.b|a*.c)+"
active_nfa = compile_regex(active_expression)
active_dfa = to_dfa(active_nfa)
for word, expected in (("ab", True), ("c", True), ("abc", True),
                       ("", False), ("a", False), ("b", False)):
    assert accepts(active_nfa, word) is expected
    assert accepts(active_dfa, word) is expected
assert accepts(nfa, "b") and not accepts(active_nfa, "b")
assert not accepts(nfa, "ab") and accepts(active_nfa, "ab")

checked = 0
for length in range(5):
    for letters in product("abc", repeat=length):
        word = "".join(letters)
        assert accepts(nfa, word) == accepts(dfa, word)
        assert accepts(active_nfa, word) == accepts(active_dfa, word)
        checked += 1
assert checked == 121
print("unused-setup words checked:", setup_checks)
print("different kernels, equal closures:", closure_a == closure_b)
print("selected probe postfix:", "".join(to_postfix(selected)))
print("selected NFA states/edges:", len(nfa.states), len(nfa.transitions))
print("selected DFA states/edges:", len(dfa.states), len(dfa.transitions))
print("active expression:", active_expression)
print("bounded comparisons per expression:", checked)
~~~

Expected output:

~~~text
unused-setup words checked: 31
different kernels, equal closures: True
selected probe postfix: aa+.c+|bc*.|+
selected NFA states/edges: 22 28
selected DFA states/edges: 8 24
active expression: (a.b|a*.c)+
bounded comparisons per expression: 121
~~~

## Interpret the evidence

The reconstructed setup agrees with its independent odd-ones predicate on 31 binary words. The selected commented expression and the active expression each agree with their own DFA on 121 words. They do **not** describe the same language: `b` and `ab` are explicit distinguishing words, checked in opposite directions.

The alphabet assertion translates the historical alphabet probe into Python's contract: internal `None` epsilon labels are excluded. It does not treat Java's empty string and Python's `None` as input symbols.

The equality demonstration checks actual closures of an actual graph. It does not infer correctness from scratch output, object names or container size. The bounded language checks likewise do not prove equivalence for all words; the subset-prefix invariant supplies the general reasoning.

<details>
<summary>Optional depth: a compact description of the selected language</summary>

For this expression, a word over `{a, b, c}` accepts exactly when it is nonempty and each maximal consecutive run of `a` has length at least two. Every such run can form an `a.a+` block; each `b` can form a `b.c*` block with zero trailing `c`, and each `c` can form a `c+` block. Conversely, none of the allowed blocks creates an isolated `a`. Adjacent `a` blocks can merge into longer runs but cannot shorten them. This characterization is a supplemental derivation, not a comment from Main or a result proved by the 121 tests.

</details>

## Exercise: active or merely visible?

A reader says “Main runs the large three-way expression, then tests subset equality.” Correct that statement using the source spans. Next, predict whether `caa` and `cac` belong to the selected three-way language.

<details>
<summary>Answer and reason</summary>

The three-way expression is commented at line 99, and the subset experiments are inside the comment at lines 103–138. The active conversion at lines 140–146 uses `(a.b|a*.c)+`. In the selected three-way language, `caa` accepts as `c` then `aa`. `cac` rejects because its single `a` cannot form an `a.a+` block.

</details>

**Common mistake:** treating commented examples as executed tests or treating equal kernels as a general language-equivalence test. A comment reveals an experiment's intent; the active source and explicit assertions determine what is actually demonstrated.

## Recap and stop point

You separated five source regions, reconstructed the unused setup, tested a commented expression deliberately, and kept it distinct from the active final conversion.

**Stop here:** identify one claim supported by source status, one supported by executed assertions, and one requiring a general argument. **Resume:** return to the [source curriculum map](../reference/source-curriculum.md) and choose a topic whose evidence you can now explain without running the program.
