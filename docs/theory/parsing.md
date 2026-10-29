# Parsing: from expression text to a syntax tree

**Goal:** trace operator precedence using stacks, turn postfix tokens into a tree without reversing operands, and use syntax-error positions to explain invalid input.

**Prerequisites:** [Regex theory](regex.md), including explicit concatenation and operator meanings. Basic Python lists help with the [paired tutorial](../tutorials/parsing.md). Stack notation is introduced here.

**First pass:** follow the two tables for `(a|b).c*`. Stop after the tree if needed; return for validation and exercises.

## 1. Two representations answer different questions

Infix source places a binary operator between operands: `a.b`. **Postfix** places the operator after its operands: `ab.`. It removes the need for parentheses because operand order and operator arity determine the structure.

An **abstract syntax tree**, or **AST**, records that structure explicitly. A node represents a literal or operation; its child nodes represent operands. A literal has no children and is called a **leaf**. The outermost operation is the **root**.

~~~text
infix source:       (a|b).c*
                         ↓ validation and operator ordering
postfix tokens:     a b | c * .
                         ↓ assemble nodes
AST root:           Concatenation
                    /             \
              Alternation       KleeneStar
               /      \             |
             "a"      "b"          "c"
~~~

In the public API, `to_postfix(expression)` returns a tuple of character tokens. `parse(expression)` returns an immutable AST. Both functions live in `jautomata.regex`. There is no requirement to call one before the other: each validates its own expression argument.

The compiler consumes postfix tokens directly. The AST is useful for inspecting meaning and structure; compilation does not need to create that tree first.

## 2. A stack keeps the most recent item accessible

A **stack** is a collection with two operations: **push** adds an item at the top; **pop** removes and returns the top item. Last in, first out means the most recently pushed item is popped first.

In the tables below, the bottom is at the left and the top is at the right. Stack `[(, |]` has `|` on top. The empty stack is shown as `—`.

The infix-to-postfix pass uses:

- An **output list**, which accumulates tokens in postfix order.
- An **operator stack**, which holds binary operations waiting for their right operand and opening parentheses marking group boundaries.
- An **expect-operand flag**, which remembers whether the next token must begin an operand.

This implementation emits a postfix `*` or `+` immediately: its operand has already been emitted. It does not leave these unary operators waiting on the operator stack.

## 3. Follow every token of `(a|b).c*`

Positions are zero-based character indexes. Before reading any token, the output and stack are empty, and the parser expects an operand.

| Position and token | Action | Operator stack, bottom → top | Output so far | Expect operand next? |
| --- | --- | --- | --- | --- |
| Start | Initialize | — | — | Yes |
| 0: `(` | Push group boundary | `(` | — | Yes |
| 1: `a` | Emit literal | `(` | `a` | No |
| 2: `\|` | Push union | `( \|` | `a` | Yes |
| 3: `b` | Emit literal | `( \|` | `a b` | No |
| 4: `)` | Pop union into output; remove `(` | — | `a b \|` | No |
| 5: `.` | Push concatenation | `.` | `a b \|` | Yes |
| 6: `c` | Emit literal | `.` | `a b \| c` | No |
| 7: `*` | Emit postfix star immediately | `.` | `a b \| c *` | No |
| End | Pop remaining concatenation | — | `a b \| c * .` | No |

Parentheses never appear in the final postfix tuple. Their job was to control when the grouped union was emitted.

For a binary operator, pop pending binary operators of **greater or equal precedence** before pushing the new operator. Stop at an opening parenthesis. Greater precedence preserves tighter binding; equal precedence produces left-to-right grouping.

For example, `a.b.c` reaches its second dot with output `a b` and the first dot on the stack. That pending dot is popped first, giving `a b .`; only then is the new dot pushed. The final postfix sequence is `a b . c .`, representing `(a.b).c`.

**Predict:** for `a|b.c`, does the dot pop the pending union when it arrives?

<details>
<summary>Reveal the stack decision</summary>

No. Union has lower precedence than dot, so it stays below the dot on the stack. At the end, dot is popped first, then union, producing `a b c . |`. This is `a|(b.c)`.

</details>

## 4. Build the AST from postfix

**Arity** is the number of operands an operator takes. Literals have no operands, `*` and `+` each have one, and `.` and `|` each have two.

The tree-building pass uses a different stack: a stack of partially built AST nodes. Each item is the root of a complete subtree. For compactness, the next table writes a literal leaf as `a`, union as `Alt(left, right)`, and star as `Star(operand)`.

| Token | Action | Node stack, bottom → top |
| --- | --- | --- |
| `a` | Push `Literal("a")` | `a` |
| `b` | Push `Literal("b")` | `a`, `b` |
| `\|` | Pop right `b`, then left `a`; push union | `Alt(a, b)` |
| `c` | Push `Literal("c")` | `Alt(a, b)`, `c` |
| `*` | Pop `c`; push star | `Alt(a, b)`, `Star(c)` |
| `.` | Pop right star, then left union; push concatenation | `Concat(Alt(a, b), Star(c))` |

The result must be exactly one root node. Two unrelated roots would mean the expression failed to connect its operands; an operator with too few nodes would lack operands. The public parser validates infix structure before this assembly pass.

Operand order matters. Given postfix `a b .`, `b` is on top, so the first pop is the **right** operand. Reversing the pops would produce `b.a`, a different language. Union has the same language after swapping operands, but the AST still preserves source order for consistent diagnostics and inspection.

**Stop point:** you now have the full text → postfix → tree trace. On return, compare the node classes and the positioned errors below, then run the tutorial.

## 5. Immutable nodes preserve the parse result

| Class | Fields | Meaning |
| --- | --- | --- |
| `Literal` | `value` | One literal character |
| `Concatenation` | `left`, `right` | Ordered binary concatenation |
| `Alternation` | `left`, `right` | Binary union preserving source order |
| `KleeneStar` | `operand` | Zero-or-more repetition |
| `PositiveClosure` | `operand` | One-or-more repetition |

Each is a frozen dataclass. Parser-produced trees contain these frozen nodes and string leaves, so you can inspect fields but cannot assign a different operand or character to an existing node. To represent a different expression, parse different source or construct a new tree.

Tree equality compares structure and fields. Equal languages need not give equal trees: `a|b` and `b|a` recognize the same words, yet their left and right leaves differ. Conversely, `a.b.c` and `(a.b).c` produce the same grouping even though their source strings differ.

An AST's `Literal("a")` is an instruction in a parsed expression, not an automaton state. Graph states are created later during [Thompson construction](literal.md).

## 6. Validation remembers where a failure occurs

`RegexSyntaxError` stores the original `expression` and a zero-based `position`. The position may equal the source length when an error is discovered at end of input. It is a character offset in the Python string, not a byte offset.

| Source | Position | Why parsing stops |
| --- | --- | --- |
| `""` | 0 | Empty expression is invalid |
| `ab` | 1 | A literal follows a completed operand without a dot |
| `*a` | 0 | Postfix star has no operand |
| `a\|` | 2 | End of input arrives while an operand is required |
| `()` | 1 | The group has no operand |
| `(a` | 2 | End of input arrives before a closing parenthesis |
| `a)` | 1 | There is no opening group to close |

The missing-close message also names the unmatched opening position. For `(a`, `position` is still 2, the place where the parser discovers that input has ended; the message refers back to opening index 0.

The expect-operand flag explains several cases. It starts true, becomes false after a literal or completed group, and becomes true after a binary operator. Postfix repetition requires a completed operand and leaves the flag false. This catches invalid boundaries before they become obscure stack failures.

Non-string expressions raise `TypeError`, because there is no expression text to parse. That is a different failure category from a malformed string.

<details>
<summary>Optional depth: why the stack method preserves structure</summary>

After a prefix has been processed, the output contains completed operands and operations whose ordering is settled. The operator stack holds operations still waiting for a sufficiently complete right operand or the end of their group. An opening parenthesis forms a boundary that an outside operator cannot cross.

When a new binary operator has lower precedence, any tighter pending operator must finish first. At equal precedence, the earlier operator finishes first to preserve left associativity. A closing parenthesis finishes every pending operation inside that group. Together, these rules make the postfix order respect precedence and grouping.

During AST assembly, each stack item is a complete subtree for one available operand. A unary operator replaces one item with one tree; a binary operator replaces its two most recent operand trees with one tree, taking right before left. Valid input ends with one item representing the whole expression.

This is an invariant-based explanation of the algorithm. The source implements both passes iteratively, using explicit lists instead of recursive descent through nested groups. Iteration avoids dependence on Python recursion depth; it does not imply unlimited memory or settle every runtime-cost question. See [Validation and complexity](validation-complexity.md) for cost analysis.

</details>

## 7. Practice and common mistakes

**Exercise A:** write postfix for `a.b|c`, then name the root node. Explain why it differs from `a.(b|c)`.

<details>
<summary>Reveal the answer</summary>

`a.b|c` gives `a b . c |`; its root is `Alternation(Concatenation(a, b), c)`. `a.(b|c)` gives `a b c | .`; its root is `Concatenation(a, Alternation(b, c))`. The first can accept `c`; the second requires an initial `a` and can accept `ac`.

</details>

**Exercise B:** what tree does `a*+` produce? Which operation is the root?

<details>
<summary>Reveal the answer</summary>

Postfix is `a * +`. First star wraps the literal, then plus wraps that subtree. The result is `PositiveClosure(KleeneStar(Literal("a")))`. Plus is the root, and the expression is nullable because its operand `a*` is nullable.

</details>

**Exercise C:** where does parsing `a..b` fail, and why?

<details>
<summary>Reveal the answer</summary>

At index 2, the second dot. The first dot sets expect-operand to true. The next token is another binary operator, which cannot begin an operand. The parser does not wait for AST assembly to discover missing operands.

</details>

Common mistakes are reading the stack top at the wrong end, popping the left operand first, putting parentheses into the postfix result, and treating a source position as a one-based count. Label your stack orientation, number the source from zero, and keep operator ordering separate from tree assembly.

## Source grounding

- **Source commentary:** [regex.py:91–98](../../python/src/jautomata/regex.py#L91-L98) explains the iterative parser; [regex.py:200–231](../../python/src/jautomata/regex.py#L200-L231) documents the public functions.
- **Verified implementation:** [regex.py:99–173](../../python/src/jautomata/regex.py#L99-L173) manages validation, operator/output lists, and positions; [regex.py:176–197](../../python/src/jautomata/regex.py#L176-L197) builds the AST with right-before-left pops. [regex.py:21–38](../../python/src/jautomata/regex.py#L21-L38) defines positioned errors; [regex.py:41–75](../../python/src/jautomata/regex.py#L41-L75) defines frozen node classes. [thompson.py:123–130](../../python/src/jautomata/thompson.py#L123-L130) compiles via postfix directly.
- **Historical implementation:** [ShuntingYard.java:32–60](../../src/ExpresionRegularToAFN/ShuntingYard.java#L32-L60) is the operator-stack reference. Its comment at lines 51–54 suggests dot insertion, while the code only appends the literal. Python validates explicit dots and emits postfix repetition immediately; the table above traces Python's implementation.
- **Supplemental explanation:** the stack diagrams, token-by-token tables, arity vocabulary, and invariants explain those implementations.

## Recap and resume

Parsing first settles operator order, then assembles structure. The operator stack is not the AST-node stack. Binary AST construction pops right before left, and positioned errors explain invalid boundaries before construction.

**Next action:** reproduce the postfix tuple, inspect immutable nodes, and assert error positions in [Parsing tutorial](../tutorials/parsing.md). Then continue to [Literal construction](literal.md), the base case of building an automaton.
