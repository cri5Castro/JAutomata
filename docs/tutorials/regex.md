# Compile expressions and test their languages

**Goal:** test each supported operator, distinguish precedence from grouping, and investigate literal characters and nullable operands.

**Prerequisites:** [Regex theory](../theory/regex.md), basic Python dictionaries and assertions, and [Getting started](../getting-started.md). The [automata tutorial](automata.md) explains the graph that compilation produces.

## 1. Predict before running

You will compare `a|b.c*` with `(a|b).c*`. Both accept `a` and `bc`. Predict whether each accepts `ac`, then predict whether `(a*)+` accepts empty input.

<details>
<summary>Reveal the predictions</summary>

Only `(a|b).c*` accepts `ac`, because grouping allows the `a` branch to be followed by `c*`. `(a*)+` accepts empty input: one repetition of the inner `a*` may contain zero `a` characters.

</details>

## 2. Save a complete language-checking program

Save this block as `regex_lesson.py` in the repository root. Each fixture supplies an expression, words it must accept, and words it must reject. A fixture failure reports the expression and word that disagreed with the prediction.

~~~python
from jautomata import RegexSyntaxError, accepts, compile_regex

fixtures = [
    ("a", ["a"], ["", "aa", "b"]),
    ("a.b", ["ab"], ["", "a", "b", "ba", "aba"]),
    ("a|b", ["a", "b"], ["", "ab", "ba"]),
    ("a*", ["", "a", "aaa"], ["b", "ab"]),
    ("a+", ["a", "aaa"], ["", "b", "ab"]),
    ("(a|b).c", ["ac", "bc"], ["", "a", "abc"]),
    ("(a.b)*", ["", "ab", "abab"], ["a", "aba", "aabb"]),
    ("a|b.c*", ["a", "b", "bc", "bcc"], ["", "ac", "abc"]),
    ("(a|b).c*", ["a", "ac", "acc", "b", "bc"], ["", "ab", "abc"]),
    ("(a*)+", ["", "a", "aaa"], ["b", "ab"]),
]

checks = 0
for expression, accepted_words, rejected_words in fixtures:
    machine = compile_regex(expression)
    for word in accepted_words:
        assert accepts(machine, word), (expression, "should accept", word)
        checks += 1
    for word in rejected_words:
        assert not accepts(machine, word), (expression, "should reject", word)
        checks += 1
assert checks == 56
print(f"Operator and grouping checks: {checks}")

# Nonreserved Unicode, whitespace, and punctuation are literal characters.
for character in ["é", "λ", " ", "?", "[", "]", "\\", "ε"]:
    machine = compile_regex(character)
    assert machine.alphabet == frozenset({character})
    assert accepts(machine, character)
    assert not accepts(machine, "")
    assert not accepts(machine, character + character)

# Explicit dots also separate literal spaces and bracket characters.
assert accepts(compile_regex("a. .b"), "a b")
assert not accepts(compile_regex("a. .b"), "ab")
assert accepts(compile_regex("[.a.]"), "[a]")

# Python string escaping happens before the regex parser sees the string.
backslash = "\\"  # One literal backslash character in the expression.
assert len(backslash) == 1
assert accepts(compile_regex(backslash), backslash)
assert not accepts(compile_regex("é"), "e\u0301")  # No Unicode normalization.
print("Literal Unicode, whitespace, and punctuation checks passed.")

# Empty regex source is invalid; empty input can still be accepted.
invalid_expressions = ["", "()", "ab", "a(b)", "(a)(b)", "[ab]", "a . b"]
for expression in invalid_expressions:
    try:
        compile_regex(expression)
    except RegexSyntaxError as error:
        assert error.expression == expression
        assert 0 <= error.position <= len(expression)
    else:
        raise AssertionError(f"Expected invalid expression: {expression!r}")

assert accepts(compile_regex("a*"), "")
assert not accepts(compile_regex("a+"), "")
assert accepts(compile_regex("(a*)+"), "")
print("Syntax and empty-input checks passed.")
~~~

Run from the repository root:

~~~sh
uv run --project python python regex_lesson.py
~~~

Expected output:

~~~text
Operator and grouping checks: 56
Literal Unicode, whitespace, and punctuation checks passed.
Syntax and empty-input checks passed.
~~~

## 3. Read the results as language evidence

The fixture for `a.b` rejects `aba`, which confirms whole-word recognition for that case. The fixture for `(a.b)*` rejects `aabb`, which checks that repetition preserves the order of the complete operand.

Follow the membership reasoning for `bcc` under `a|b.c*`:

| Step | Subexpression | Word choice |
| --- | --- | --- |
| 1 | `c*` | Choose two repetitions, producing `cc` |
| 2 | `b.c*` | Prefix the chosen word with `b`, producing `bcc` |
| 3 | `a\|b.c*` | Choose the right alternative |

Now try the same reasoning for `ac`. The left branch can only produce `a`; the right branch must begin with `b`. Neither branch produces `ac`. A union chooses a whole alternative; it does not splice prefixes from one branch into suffixes from another.

The literal checks explain why `?` and `[` do not enable optionality or character classes. The expression `[.a.]` contains three literal characters separated by dot operators, so it recognizes the exact word `[a]`.

Two different parsers process `"\\"` in the program. Python first turns its string notation into one backslash character. JAutomata then sees that character as an ordinary literal. JAutomata itself has no escape mechanism. Similarly, `"e\u0301"` contains an `e` followed by a combining accent; it is not the single Python character `"é"`.

The fixtures are checks of selected words, not a proof for every possible input. For these short expressions, language definitions explain the general pattern; the executable checks catch disagreements between that reasoning and the implementation.

**Stop point:** after the program passes, you can pause with a working reference for all operators. Resume by changing one fixture in the exercises below.

## 4. Exercises with solutions

**Exercise A:** change `(a.b)*` to `(a.b)+`. Which existing accepted word must move to the rejected list? Does `abab` change?

<details>
<summary>Reveal the answer</summary>

Move `""` to the rejected list. Positive closure requires at least one `ab` block. `abab` remains accepted because it contains two complete blocks. The operand `a.b` cannot produce an empty word, so plus rejects empty input here.

</details>

**Exercise B:** describe one or more `a` characters followed by exactly one literal `?`. Test `a?`, `aaa?`, `?`, and `a`.

<details>
<summary>Reveal the expression and runnable solution</summary>

The expression is `a+.?`: plus repeats `a`, dot concatenates, and `?` is a literal.

~~~python
from jautomata import accepts, compile_regex

machine = compile_regex("a+.?")
assert accepts(machine, "a?")
assert accepts(machine, "aaa?")
assert not accepts(machine, "?")
assert not accepts(machine, "a")
~~~

This block succeeds silently.

</details>

**Exercise C:** predict empty-input acceptance for `a*.b*`, `a*.b+`, and `(a|b)*`. Explain each result without running it first.

<details>
<summary>Reveal the answer and reasoning</summary>

`a*.b*` accepts empty input because both parts may contribute zero characters. `a*.b+` rejects empty input because the second part requires a `b`. `(a|b)*` accepts empty input because the outer star can use zero repetitions of the entire group.

</details>

**Exercise D:** replace `a|b.c*` with `(a|b).c*` in a fixture. Which rejected example from the old fixture must become accepted?

<details>
<summary>Reveal the answer</summary>

`ac` becomes accepted. The group can choose `a`, then `c*` can choose one `c`. Both expressions still reject `abc`, since neither allows an `a` followed by a `b` within one accepted word.

</details>

## Mistakes to diagnose

- **`RegexSyntaxError` for `ab`:** insert the explicit concatenation operator to get `a.b`.
- **Spaces added for readability:** remove formatting spaces or use explicit dots if a space is intended as input data.
- **Expecting `.` to match an arbitrary character:** this dialect has no wildcard; dot needs two operands and concatenates their words.
- **Expecting `+` to force a nonempty word:** inspect its operand. A nullable operand permits an empty result even under positive closure.
- **Confusing invalid source with rejection:** `compile_regex("")` raises; `accepts(compile_regex("a"), "")` returns `False` for a valid graph and a rejected input.

## Source grounding

**Commentary:** [regex.py:1–13](../../python/src/jautomata/regex.py#L1-L13) specifies this dialect; [regex.py:42–75](../../python/src/jautomata/regex.py#L42-L75) describes the operator nodes.

**Verified implementation:** [regex.py:99–173](../../python/src/jautomata/regex.py#L99-L173) validates source characters and precedence; [thompson.py:97–130](../../python/src/jautomata/thompson.py#L97-L130) compiles validated postfix tokens into an automaton; [simulation.py:143–153](../../python/src/jautomata/simulation.py#L143-L153) evaluates complete input words.

**Historical comment discrepancy:** the comment at [ShuntingYard.java:51–54](../../src/ExpresionRegularToAFN/ShuntingYard.java#L51-L54) proposes inserting a dot, but the literal branch only appends its token. This tutorial follows verified explicit-dot behavior.

**Supplemental explanation:** the fixture languages, nullability reasoning, and membership trace are derived teaching examples. Later construction lessons explain why the compiled graph has those behaviors.

## Recap and resume

You tested every operator, found a word that distinguishes two groupings, and checked literal and empty-input edge cases. Keep the fixture format when studying a new expression: accepted and rejected words expose different mistakes.

**Next action:** read [Parsing theory](../theory/parsing.md), then inspect the postfix tokens and syntax tree in [Parsing tutorial](parsing.md).
