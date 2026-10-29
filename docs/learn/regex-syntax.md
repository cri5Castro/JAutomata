# Regex syntax: say concatenation out loud

**Objective:** write valid expressions in this project’s deliberately small
regex language and predict their postfix order.

## The whole grammar

Literals are single Unicode characters except these reserved characters:
`.`, `|`, `*`, `+`, `(`, `)`. Whitespace and punctuation such as `?` are
literals. There are no escapes, character classes, wildcard, implicit
concatenation, or regex-level epsilon token.

| Form | Meaning | Example |
|---|---|---|
| `x` | one literal | `a` accepts only `"a"` |
| `r.s` | `r` followed by `s` | `a.b` accepts `"ab"` |
| `r|s` | either alternative | `a|b` accepts `"a"` or `"b"` |
| `r*` | zero or more repetitions | `a*` accepts `""` |
| `r+` | one or more repetitions | `a+` rejects `""` |
| `(r)` | grouping | `(a|b).c` accepts `"ac"` and `"bc"` |

Postfix `*` and `+` bind first, `.` binds next, and `|` binds last. Binary
operators are left-associative; a chain such as `a*+` is read left to right.

## Worked trace: `a|b.c`

1. Read `a`; it is an operand.
2. Hold `|` until its right operand is complete.
3. Read `b.c`; `.` has higher precedence than `|`.
4. The postfix order is `a b c . |`.

~~~python
from jautomata import accepts, compile_regex
from jautomata.regex import to_postfix

assert to_postfix("a|b.c") == ("a", "b", "c", ".", "|")
machine = compile_regex("a|b.c")
assert [accepts(machine, text) for text in ("a", "bc", "b", "ac")] == [True, True, False, False]
~~~

**Expected output:** the snippet prints nothing. The expression accepts `"a"`
and `"bc"`, not `"b"` or `"ac"`.

### Common mistake

`ab` is invalid here. It is *not* shorthand for `a.b`; write the dot. The
parser raises `RegexSyntaxError` with a character position for `ab`, an empty
expression, unmatched parentheses, or missing operands.

<details>
<summary>Exercise — make <code>(a|b).c</code> accept both two-character words.</summary>

The grouping makes the union happen before concatenation:

~~~python
from jautomata import accepts, compile_regex

grouped = compile_regex("(a|b).c")
assert accepts(grouped, "ac") and accepts(grouped, "bc")
assert not accepts(grouped, "abc")
~~~
</details>

## Deeper: why explicit dots matter

The original Java shunting-yard parser assigns precedence 3, 2, and 1 to
closure, concatenation, and union
([source](../../src/ExpresionRegularToAFN/ShuntingYard.java#L13-L30)). A nearby
comment suggests inserting dots, but the active Java code does not do so
([source](../../src/ExpresionRegularToAFN/ShuntingYard.java#L53)). Python makes
that choice a clear public contract instead of silently repairing an expression.
See [Compatibility](../compatibility.md#purpose-and-assumptions) for the full
error and Unicode rules.

**Next:** turn postfix tokens into a graph with
[Thompson construction](thompson.md).
