# Practica 2: compile a compound expression

**Goal:** read the grouping in `((b.c.d)*|f+.a).f`, follow its postfix construction, and explain why the single-letter word `f` accepts.

**Prerequisites:** [regex syntax](../theory/regex.md), [parsing](../theory/parsing.md), [concatenation](../theory/concatenation.md), [union](../theory/union.md), [Kleene star](../theory/kleene-star.md) and [positive closure](../theory/positive-closure.md).

**Route:** split the expression → trace fragment construction → predict → run.

## Source and meaning

The active [Practica2 example](../../src/Practica2/Practica2.java#L9-L15) aims to generate an NFA from a regex and uses exactly `((b.c.d)*|f+.a).f`. This is source behavior. The language derivation and independent predicate below are supplemental explanations.

Read the expression in blocks:

~~~text
choose one prefix:       then append:
  (b c d), repeated zero or more times ─┐
                                       ├── f
  one or more f, followed by a ─────────┘
~~~

In mathematical shorthand, the words are `(bcd)^k f` for `k ≥ 0`, or `f^j a f` for `j ≥ 1`. An exponent means repetition count, not arithmetic multiplication. Both alternatives must still consume the final `f` outside the union.

The star permits a zero-length prefix, so `f` accepts. The plus requires at least one `f` before the `a` in the second alternative, so `af` rejects. The entire expression rejects empty input because of its final literal.

## Follow construction in postfix order

The parser produces `b c . d . * f + a . | f .`. Postfix places an operator after its operand fragments; each dot pops right then left and links them in that order.

| Tokens processed | Fragment meaning | New construction |
| --- | --- | --- |
| `b c .` | `bc` | Two literals and one epsilon concatenation link |
| `d .` | `bcd` | A third literal and one more link |
| `*` | zero or more `bcd` | Fresh entry/exit, bypass and repeat edges |
| `f +` | one or more `f` | Literal plus fresh entry/exit and repeat; no bypass |
| `a .` | `f+` followed by `a` | Literal and ordered link |
| `\|` | either prefix | Fresh entry/exit and four branch edges |
| `f .` | chosen prefix followed by `f` | Final literal and ordered link |

The delivered builder creates 18 states and 21 edges. State 14 is the union entry; final state 17 is the exit of the last literal. These IDs describe this Python construction, not an assumption about Java's printed numbering.

## Predict the competing paths

| Word | Relevant decomposition | Result |
| --- | --- | --- |
| `f` | zero `bcd` blocks, then `f` | accept |
| `bcdf` | one `bcd`, then `f` | accept |
| `faf` | one `f`, then `a`, then `f` | accept |
| `ffaf` | two `f` characters, then `a`, then `f` | accept |
| empty | final literal absent | reject |
| `bcd` | prefix complete, final `f` absent | reject |
| `fa` | second prefix complete, final `f` absent | reject |

After reading `f`, the NFA retains both a successful final path and unfinished paths in the `f+.a` branch. Acceptance at that point does not justify ignoring later input.

## Run the complete lab

Use [Getting started](../getting-started.md), save as `practica2_lab.py` in the repository root, then run:

~~~sh
uv run --project python python practica2_lab.py
~~~

~~~python
from itertools import product
from jautomata import accepts, compile_regex, epsilon_closure, to_dfa
from jautomata.regex import to_postfix

expression = "((b.c.d)*|f+.a).f"
postfix = to_postfix(expression)
assert "".join(postfix) == "bc.d.*f+a.|f."
nfa = compile_regex(expression)
dfa = to_dfa(nfa)
assert (len(nfa.states), len(nfa.transitions)) == (18, 21)
assert nfa.alphabet == frozenset("abcdf")

current = epsilon_closure(nfa, {nfa.start_state})
assert current == frozenset({0, 6, 7, 8, 10, 14, 15, 16})
moved = {edge.target for edge in nfa.transitions
         if edge.source in current and edge.symbol == "f"}
after_f = epsilon_closure(nfa, moved)
assert after_f == frozenset({8, 9, 11, 12, 17})
assert after_f & nfa.final_states

def described_language(word):
    if not word.endswith("f"):
        return False
    prefix = word[:-1]
    left = prefix == "bcd" * (len(prefix) // 3)
    right = (prefix.endswith("a") and len(prefix) >= 2
             and set(prefix[:-1]) == {"f"})
    return left or right

cases = (("f", True), ("bcdf", True), ("faf", True), ("ffaf", True),
         ("", False), ("bcd", False), ("fa", False), ("af", False))
print("postfix:", "".join(postfix))
print("NFA states/edges:", len(nfa.states), len(nfa.transitions))
for word, expected in cases:
    assert described_language(word) is expected
    assert accepts(nfa, word) is expected
    assert accepts(dfa, word) is expected
    print(repr(word) + ": " + str(expected))
assert accepts(nfa, "bcdbcdf")
assert not accepts(nfa, "bcdaf")
assert not accepts(nfa, "x")
assert not accepts(dfa, "x")

checked = 0
for length in range(5):
    for letters in product("abcdf", repeat=length):
        word = "".join(letters)
        expected = described_language(word)
        assert accepts(nfa, word) is expected
        assert accepts(dfa, word) is expected
        checked += 1
assert checked == 781
print("bounded words checked:", checked)
~~~

Expected output:

~~~text
postfix: bc.d.*f+a.|f.
NFA states/edges: 18 21
'f': True
'bcdf': True
'faf': True
'ffaf': True
'': False
'bcd': False
'fa': False
'af': False
bounded words checked: 781
~~~

## Interpret the checks

The code verifies the initial closure and the complete active set after `f`, including final state 17 and unfinished alternatives. The language predicate strips the mandatory last `f`, then checks the two possible prefix forms without graph traversal.

The 781 words cover all lengths 0–4 over five symbols; the extra `bcdbcdf` fixture illustrates a longer repetition. The finite checks support the reconstruction but are not a proof for arbitrary repetition counts. Such a proof follows the fragment-language rules: union chooses either prefix language, star and plus repeat their operand languages, and the final concatenation appends `f`.

<details>
<summary>Optional depth: account for all 21 edges</summary>

Six literal occurrences contribute six consuming edges: `b`, `c`, `d`, the first `f`, `a`, and the last `f`. Four dots add four epsilon links. Star adds four epsilon edges, plus adds three, and union adds four. The total is `6 + 4 + 4 + 3 + 4 = 21`. Literal occurrences are counted separately even when they carry the same symbol. The corresponding state total is twelve literal states plus two each for star, plus and union, giving eighteen.

</details>

## Exercise: move the final dot

Would `(b.c.d)*|f+.a.f` accept the same language? Predict empty input and `bcd`.

<details>
<summary>Answer and reason</summary>

No. Without grouping the union before the final concatenation, only the right alternative requires the last `f`. The left alternative is simply `(bcd)*`, which accepts both empty input and `bcd`. The original rejects both. Grouping changes the operand to which concatenation applies.

</details>

**Common mistake:** reading `f+` as “one extra `f`” rather than one or more repetitions. Another is allowing the final `f` to belong only to the right alternative despite the original parentheses.

## Source connection and stop point

**Commentary and active example:** [Practica 2's goal and expression](../../src/Practica2/Practica2.java#L9-L15). **Verified implementation:** [the ordered literal, dot, union and repetition constructors](../../python/src/jautomata/thompson.py#L56-L92). **Supplement:** the decomposition, count derivation and predicate above are added reasoning.

**Recap:** every accepted word ends in `f`; its prefix has one of two precisely grouped forms. **Stop here:** explain why `f` accepts and `ff` rejects. **Resume:** [Practica 3](practica3.md) follows a different expression through the complete subset table.
