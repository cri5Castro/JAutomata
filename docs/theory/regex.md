# Regular expressions describe languages

**Goal:** read an expression in JAutomata's dialect, determine which complete words it describes, and predict how precedence, grouping, and repetition change that language.

**Prerequisites:** [Automata theory](automata.md), especially alphabets, words, languages, and empty input. Use the [paired tutorial](../tutorials/regex.md) to test your predictions.

**First pass:** learn the operator table, work through one expression, and answer the empty-input prediction. The formal language equations are optional.

## 1. An expression is a recipe for a language

The expression `a.b` describes the one-word language `{ab}`. The dot means concatenate: take a word from the left language, then a word from the right language, and put them next to each other.

The expression itself is source text; the words it recognizes are input text. For `a.b`, the source contains a dot but the accepted word `ab` does not. `compile_regex` turns source text into an epsilon-NFA, and `accepts` checks a complete input word against that graph.

~~~text
expression text        automaton graph              Boolean result
     a.b       --compile_regex-->  NFA  --accepts(..., "ab")-->  True
~~~

This dialect is deliberately small. Familiar features from another regex library may have a different meaning or be unavailable here.

## 2. The operators and what they mean

| Form | Name | Meaning | Accepted examples | Rejected examples |
| --- | --- | --- | --- | --- |
| `a` | Literal | Exactly one `a` | `a` | `""`, `aa` |
| `a.b` | Concatenation | An `a` followed by a `b` | `ab` | `a`, `ba` |
| `a\|b` | Union / alternation | Either language | `a`, `b` | `""`, `ab` |
| `a*` | Kleene star | Zero or more repetitions | `""`, `a`, `aaa` | `b` |
| `a+` | Positive closure | One or more repetitions | `a`, `aaa` | `""`, `b` |
| `(a\|b).c` | Grouping | Apply concatenation to the whole group | `ac`, `bc` | `a`, `abc` |

`*` and `+` are **postfix operators**: they come after the expression they repeat. Dot and union are **binary operators**: each needs a left operand and a right operand. Parentheses control grouping without contributing input characters.

Repetition applies to words in an operand's language, not necessarily to one character. `(a.b)+` accepts `ab`, `abab`, and so on. It rejects `aabb`: the repeated unit is `ab`, not “some `a` characters followed by some `b` characters.”

## 3. Precedence determines the grouping

**Precedence** says which operation binds more tightly when parentheses do not settle the question.

| Priority | Operators | Example interpretation |
| --- | --- | --- |
| Highest | Postfix `*`, `+` | `a.b*` means `a.(b*)` |
| Middle | Explicit concatenation `.` | `a\|b.c` means `a\|(b.c)` |
| Lowest | Union `\|` | `a.b\|c` means `(a.b)\|c` |

Binary chains are grouped from left to right: `a.b.c` parses as `(a.b).c`. Chained postfix operators also apply left to right: `a*+` means `(a*)+`. The later [parsing lesson](parsing.md) shows how those choices appear in the syntax tree.

Work through `a|b.c*` in three steps:

1. `c*` describes `""`, `c`, `cc`, and any further repetitions of `c`.
2. `b.c*` describes `b`, `bc`, `bcc`, and so on.
3. Union adds the separate possibility `a`.

The full language is therefore `{a, b, bc, bcc, …}`. It does not contain `ac`, because the `c*` belongs only to the right branch.

Compare `(a|b).c*`. The parentheses make either `a` or `b` available before `c*`, so `ac` now belongs to the language.

**Predict:** which of `a`, `ac`, `bc`, and `""` belong to each expression?

<details>
<summary>Reveal the comparison</summary>

| Word | `a\|b.c*` | `(a\|b).c*` |
| --- | --- | --- |
| `a` | Accept | Accept |
| `ac` | Reject | Accept |
| `bc` | Accept | Accept |
| `""` | Reject | Reject |

Both require at least one literal character before they can finish. In the first expression `ac` cannot use pieces from different union branches. In the second expression concatenation applies to the entire union.

</details>

**Stop point:** if you can explain the `ac` row, you understand the main precedence rule. Resume with the literal-character rules below before using familiar regex syntax.

## 4. Literal means exactly one character

The only reserved source characters are `.`, `|`, `*`, `+`, `(`, and `)`. Every other character is a literal, including whitespace and other punctuation.

- `?` matches an actual question mark. It is not an optionality operator.
- A source string containing one space matches one space. Spaces are not ignored as formatting.
- `é` matches that Unicode character. The implementation processes Python string characters; it performs no case folding or Unicode normalization.
- `ε` matches an actual Greek epsilon character. It is not a source token for an empty word.
- `[` and `]` are ordinary literals. `[ab]` is invalid because it places literal tokens next to each other without dots; it is not a character class.
- A backslash is an ordinary literal, not an escape prefix. There is no syntax for escaping a reserved operator into a literal.

The dot always means explicit concatenation, never “any character.” Source `ab`, `a(b)`, and `(a)(b)` are invalid because they omit required dots. Write `a.b`, `a.(b)`, and `(a).(b)` respectively.

Whitespace in a Python expression string is input data. For example, source `"a. .b"` contains a literal space between the two dot operators and describes the word `"a b"`. Writing `"a . b"` as visual spacing instead puts a literal space immediately after `a`, which violates the explicit-dot rule.

These are implementation rules, not universal definitions of regular expressions.

## 5. Empty input and nullable expressions

An expression is **nullable** when its language contains the empty word. This property asks about recognized input, not the length of the expression's source text.

`a*` is nullable because zero repetitions are allowed. `a+` is not nullable because every repetition contributes an `a`. But `(a*)+` **is** nullable: its one required repetition may select the empty word from the inner `a*` language.

~~~text
outer +: choose at least one repetition
one repetition of inner a*: choose zero a characters
result: the empty word
~~~

“At least one repetition” and “at least one input character” are different requirements. Positive closure enforces the former.

The source expression `""` is invalid, even though some nonempty expressions accept input `""`. Empty parentheses `()` are also invalid. There is no source-level epsilon constant; to represent a machine accepting only the empty word, you can build one by hand as in the [automata tutorial](../tutorials/automata.md).

<details>
<summary>Optional formal depth: language operations and nullability</summary>

Let `L(r)` mean the language described by expression `r`. Let `uv` mean the concatenation of words `u` and `v`.

- Literal `a`: `L(a) = {a}`.
- Union: `L(r|s) = L(r) ∪ L(s)`.
- Concatenation: `L(r.s) = {uv : u ∈ L(r), v ∈ L(s)}`.
- Grouping: `L((r)) = L(r)`.

For a language `A`, define `A⁰ = {ε}` and `Aⁿ⁺¹ = AⁿA`. Then `A*` is the union of `Aⁿ` over all integers `n ≥ 0`, and `A+` is the union over `n ≥ 1`. Thus `L(r*) = L(r)*` and `L(r+) = L(r)+`.

Nullability follows from these definitions:

| Expression kind | Nullable exactly when |
| --- | --- |
| Literal | Never |
| Union | At least one operand is nullable |
| Concatenation | Both operands are nullable |
| Star | Always |
| Positive closure | Its operand is nullable |

For the positive-closure rule, one repetition of an empty word is sufficient. Conversely, if every word in the operand has positive length, concatenating one or more such words cannot produce length zero. These equations are supplemental explanations of the supported operators.

</details>

## 6. Practice and mistakes

**Exercise A:** give the first three accepted words of `(a.b)*`, ordered by length. Does it accept `aba`?

<details>
<summary>Reveal the answer</summary>

The first three are `""`, `ab`, and `abab`. It rejects `aba` because every nonempty repetition contributes the full two-character block `ab`. A trailing `a` cannot complete a block.

</details>

**Exercise B:** is `(a*).(b+)` nullable? Is `(a*).(b*)` nullable?

<details>
<summary>Reveal the answer</summary>

The first is not nullable: `b+` requires at least one `b`. The second is nullable: both sides can choose zero repetitions, and concatenating two empty words still gives the empty word.

</details>

**Exercise C:** how would you express exactly the words `ac` and `bc`?

<details>
<summary>Reveal two equivalent expressions</summary>

`(a|b).c` and `a.c|b.c` describe the same two-word language. They have different expression trees, but grouping and distribution explain their language agreement. Neither expression accepts the single word `abc`.

</details>

Common mistakes include importing wildcard or character-class assumptions, omitting dots, and assuming plus always rejects empty input. Check the dialect first, identify each operand, and then reason about the words its language contains.

## Source grounding

- **Source commentary:** [regex.py:1–13](../../python/src/jautomata/regex.py#L1-L13) defines the dialect and literal rules; [regex.py:42–75](../../python/src/jautomata/regex.py#L42-L75) documents literal, binary, and repetition node meanings.
- **Verified implementation:** [regex.py:79–83](../../python/src/jautomata/regex.py#L79-L83) lists reserved tokens and binary precedence; [regex.py:99–173](../../python/src/jautomata/regex.py#L99-L173) enforces grouping, operands, explicit dots, and postfix order.
- **Historical implementation:** [ShuntingYard.java:13–30](../../src/ExpresionRegularToAFN/ShuntingYard.java#L13-L30) assigns star/plus higher precedence than concatenation, then union. Its [literal-branch comment at lines 51–54](../../src/ExpresionRegularToAFN/ShuntingYard.java#L51-L54) suggests adding a dot, but the active branch only appends the token. That comment is not evidence that implicit concatenation works.
- **Supplemental explanation:** the set equations, nullability rules, and derived example languages explain these operators; they are not additional parser features.

## Recap and resume

Regex operators combine languages. Read postfix repetition first, dot concatenation next, and union last unless parentheses say otherwise. Use explicit dots and treat nonreserved characters, including spaces, literally.

**Next action:** run [Regex tutorial](../tutorials/regex.md), then open [Parsing theory](parsing.md) to follow source text into postfix tokens and an immutable syntax tree.
