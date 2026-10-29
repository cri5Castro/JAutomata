# Inspect postfix tokens, syntax trees, and errors

**Goal:** verify a complete parsing trace, inspect immutable AST structure, and use exact syntax-error positions to explain malformed expressions.

**Prerequisites:** [Parsing theory](../theory/parsing.md), [Regex tutorial](regex.md), basic Python lists and exception handling, and [Getting started](../getting-started.md).

The public functions used here are `parse` and `to_postfix` from `jautomata.regex`. You do not need private parser helpers.

## 1. Predict both representations

For `(a|b).c*`, predict the postfix token sequence and the AST root. Ask which operation combines the two largest pieces: the grouped union and the repeated `c`.

<details>
<summary>Reveal the prediction</summary>

The postfix tuple is `("a", "b", "|", "c", "*", ".")`. The root is `Concatenation`; its left child is `Alternation`, and its right child is `KleeneStar`. Parentheses have already done their grouping work and do not appear as nodes.

</details>

## 2. Save and run the complete program

Save this block as `parsing_lesson.py` in the repository root. The `worked_trace` data records the manual token-by-token reasoning from the theory page; it does not claim to expose private runtime stacks. The assertions compare its final sequence with the public parser's actual result.

~~~python
from dataclasses import FrozenInstanceError

from jautomata import RegexSyntaxError
from jautomata.regex import (
    Alternation,
    Concatenation,
    KleeneStar,
    Literal,
    PositiveClosure,
    parse,
    to_postfix,
)

expression = "(a|b).c*"
# Each row: source token just read, pending operators, output tokens.
# The stack top is at the right. These are worked-example data.
worked_trace = [
    ("(", ("(",), ()),
    ("a", ("(",), ("a",)),
    ("|", ("(", "|"), ("a",)),
    ("b", ("(", "|"), ("a", "b")),
    (")", (), ("a", "b", "|")),
    (".", (".",), ("a", "b", "|")),
    ("c", (".",), ("a", "b", "|", "c")),
    ("*", (".",), ("a", "b", "|", "c", "*")),
    ("END", (), ("a", "b", "|", "c", "*", ".")),
]
assert tuple(row[0] for row in worked_trace[:-1]) == tuple(expression)
postfix = to_postfix(expression)
assert postfix == worked_trace[-1][2]
print("Postfix:", " ".join(postfix))
print("Manual trace: token / operator stack / output")
for token, operators, output in worked_trace:
    print(f"{token}: {' '.join(operators) or '—'} / {' '.join(output) or '—'}")

expected_tree = Concatenation(
    Alternation(Literal("a"), Literal("b")),
    KleeneStar(Literal("c")),
)
tree = parse(expression)
assert tree == expected_tree
assert isinstance(tree, Concatenation)
assert isinstance(tree.left, Alternation)
assert tree.left.left.value == "a"
assert tree.left.right.value == "b"
assert isinstance(tree.right, KleeneStar)
assert tree.right.operand.value == "c"
print("Root:", type(tree).__name__)

# Binary operations retain left-to-right order and associativity.
assert parse("a.b") == Concatenation(Literal("a"), Literal("b"))
assert parse("a.b") != parse("b.a")
assert to_postfix("a.b.c") == ("a", "b", ".", "c", ".")
assert parse("a.b.c") == Concatenation(
    Concatenation(Literal("a"), Literal("b")), Literal("c")
)
assert parse("a.b.c") == parse("(a.b).c")
assert parse("a|b") != parse("b|a")  # Same language, different tree.

# Postfix operators wrap the available tree in source order.
assert to_postfix("a*+") == ("a", "*", "+")
assert parse("a*+") == PositiveClosure(KleeneStar(Literal("a")))

# Frozen nodes reject assignment; inspection did not mutate the tree.
try:
    tree.left.left.value = "z"
except FrozenInstanceError:
    pass
else:
    raise AssertionError("Parser-produced Literal should be immutable")
assert tree == expected_tree

invalid = {"": 0, "ab": 1, "*a": 0, "a|": 2, "()": 1, "(a": 2, "a)": 1, "a..b": 2}
for bad_expression, position in invalid.items():
    for operation in (to_postfix, parse):
        try:
            operation(bad_expression)
        except RegexSyntaxError as error:
            assert error.expression == bad_expression
            assert error.position == position, (bad_expression, error.position)
            assert f"at index {position}" in str(error)
        else:
            raise AssertionError(f"Expected syntax error: {bad_expression!r}")

for operation in (to_postfix, parse):
    try:
        operation(123)
    except TypeError:
        pass
    else:
        raise AssertionError("Non-string input should raise TypeError")

print("Structure, immutability, and positioned-error checks passed.")
~~~

Run from the repository root:

~~~sh
uv run --project python python parsing_lesson.py
~~~

Expected output:

~~~text
Postfix: a b | c * .
Manual trace: token / operator stack / output
(: ( / —
a: ( / a
|: ( | / a
b: ( | / a b
): — / a b |
.: . / a b |
c: . / a b | c
*: . / a b | c *
END: — / a b | c * .
Root: Concatenation
Structure, immutability, and positioned-error checks passed.
~~~

## 3. Explain the operator trace

At `)`, the parser emits the union and removes the opening parenthesis. At `*`, the operand `c` is already in the output, so star is emitted immediately. At the end, concatenation is still waiting and is emitted last. Its final position in postfix corresponds to its position at the root of the AST.

The manually supplied intermediate rows are an explanatory trace. The program verifies that their source tokens match the expression and that their final output matches `to_postfix`; it does not instrument the parser's internal state on every row. The implementation evidence for the intermediate actions is [regex.py:106–155](../../python/src/jautomata/regex.py#L106-L155).

For AST assembly, separate the operator stack above from the node stack below. Here `Alt`, `Star`, and `Concat` abbreviate the corresponding class names.

| Next postfix token | Nodes available after processing it |
| --- | --- |
| `a` | `Literal("a")` |
| `b` | `Literal("a")`, `Literal("b")` |
| `\|` | `Alt(a, b)` |
| `c` | `Alt(a, b)`, `Literal("c")` |
| `*` | `Alt(a, b)`, `Star(c)` |
| `.` | `Concat(Alt(a, b), Star(c))` |

Every row represents complete subtrees awaiting a parent. For a binary operator, the right subtree is on top and must be popped first. `expected_tree` checks the final nested structure, including that order.

## 4. Interpret the error checks

The eight invalid strings cover empty source, missing dots, missing operands, empty groups, and unmatched parentheses. Both public functions use the same validation rules, so the program checks each error with both functions.

For `a|`, indexes 0 and 1 are valid source characters; index 2 is the end of input. That is where a required operand is missing. For `a..b`, the error occurs earlier, at index 2, because the second dot arrives while an operand is required.

For `(a`, the error's `position` points to index 2, the end of input. The message also identifies the opening parenthesis at index 0. The detection location and the related opening location are different facts.

An integer raises `TypeError` instead: it violates the API's input type rather than the regex grammar. Parser validation occurs before AST construction, so these cases produce useful syntax errors rather than node-stack underflow.

**Stop point:** the complete program checks the parsing contract. Resume with Exercise A to practice the stack order without reading the expected tree first.

## 5. Exercises with solutions

**Exercise A:** predict postfix and the AST root for `a.b|c`. Check whether its tree equals the tree for `a.(b|c)`.

<details>
<summary>Reveal a complete runnable solution</summary>

The first expression has union at the root; the second has concatenation at the root. The dot in the first expression binds before union.

~~~python
from jautomata.regex import Alternation, Concatenation, Literal, parse, to_postfix

first = parse("a.b|c")
second = parse("a.(b|c)")
assert to_postfix("a.b|c") == ("a", "b", ".", "c", "|")
assert to_postfix("a.(b|c)") == ("a", "b", "c", "|", ".")
assert first == Alternation(Concatenation(Literal("a"), Literal("b")), Literal("c"))
assert second == Concatenation(Literal("a"), Alternation(Literal("b"), Literal("c")))
assert first != second
~~~

This block succeeds silently.

</details>

**Exercise B:** change `a*+` to `a+*`. What is the new outer node? Do the two expressions accept the same words?

<details>
<summary>Reveal the answer</summary>

`a+*` parses as `KleeneStar(PositiveClosure(Literal("a")))`; star is outermost. Both expressions describe zero or more `a` characters, so their languages are equal even though their trees differ. For `a*+`, one or more repetitions can each be empty. For `a+*`, the outer star can select zero repetitions; its nonempty repetitions consist only of `a` characters.

</details>

**Exercise C:** remove the dot in `(a|b).c*`. At which index should validation fail?

<details>
<summary>Reveal the answer and diagnosis</summary>

The new expression is `(a|b)c*`. Index 5 contains `c`, immediately after the closed group. The group is already a complete operand, so another literal needs an explicit dot before it. Validation reports position 5.

</details>

## Mistakes to diagnose

- **Importing `parse_regex`:** this module's public function is named `parse`; use `from jautomata.regex import parse`.
- **Reversing concatenation:** pop the right operand first when reading a stack from the right-hand top.
- **Expecting parentheses in postfix:** grouping influences order; its delimiter tokens disappear.
- **Equating tree equality with language equality:** swapped union branches have different trees but equal languages.
- **Editing a parsed node in place:** frozen nodes preserve the parse result. Parse another expression or build a new tree instead.

## Source grounding

**Commentary:** [regex.py:91–98](../../python/src/jautomata/regex.py#L91-L98) explains iteration; [regex.py:200–231](../../python/src/jautomata/regex.py#L200-L231) defines the public contracts.

**Verified implementation:** [regex.py:106–173](../../python/src/jautomata/regex.py#L106-L173) defines the stack and validation steps; [regex.py:176–197](../../python/src/jautomata/regex.py#L176-L197) preserves right/left operand order; [regex.py:21–38](../../python/src/jautomata/regex.py#L21-L38) attaches positions to syntax errors; [regex.py:41–75](../../python/src/jautomata/regex.py#L41-L75) makes AST nodes frozen dataclasses.

**Historical reference:** [ShuntingYard.java:32–60](../../src/ExpresionRegularToAFN/ShuntingYard.java#L32-L60) contains the original operator-stack method. Its dot-insertion comment at lines 51–54 does not match an insertion in active code; this tutorial relies on verified Python validation.

**Supplemental explanation:** the manual trace, AST diagrams, and language comparisons explain the source. The program uses the existing parser and does not implement a replacement engine.

## Recap and resume

You checked postfix order, nested node structure, left/right order, frozen values, and positioned errors. Those are distinct claims: a correct final language alone would not reveal every structural or diagnostic mistake.

**Next action:** continue to [Literal construction](../theory/literal.md) and its [tutorial](literal.md). You will turn the smallest parsed operand into the first automaton fragment.
