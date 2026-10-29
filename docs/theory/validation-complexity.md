# Validation and algorithmic complexity

**Goal:** diagnose the layer that rejects an input and explain the cost of an operation using sizes and work, rather than one timing result.

**Before you start:** [parsing](parsing.md), [epsilon closure](epsilon-closure.md), [subset construction](subset-construction.md) and [identity](identity.md).

**Route:** locate an error → count a small construction → separate setup from traversal → predict. Use the [paired tutorial](../tutorials/validation-complexity.md) to check exact exceptions and counts.

## Which layer owns the error?

| Input | Layer | Expected result |
| --- | --- | --- |
| `compile_regex(12)` | Python argument type | `TypeError` |
| `compile_regex("ab")` | Regex grammar | `RegexSyntaxError`, position 1: a dot is missing |
| `compile_regex("a\|")` | Regex grammar | `RegexSyntaxError`, position 2: end of input lacks an operand |
| `Transition(0, "ab", 1)` | Transition shape | `ValueError`: a consuming label must be one character |
| Automaton with start outside its states | Graph structure | `ValueError` |
| A valid machine asked about a nonmember word | Language recognition | `False`, not a syntax exception |

`RegexSyntaxError` is a subclass of `ValueError` with `expression` and `position` attributes. Positions are **zero-based character offsets**. A position equal to the expression length points just beyond the final character, where a required operand or closing parenthesis is missing. These are Python string-character positions, not encoded-byte offsets.

An empty input word is valid data for recognition. An empty regex expression is invalid syntax in this grammar. A symbol outside an automaton's alphabet simply has no matching move and leads to rejection.

## Validate the whole graph once

The model requires a nonempty state set, one start belonging to that set, final states drawn from that set, and both endpoints of every edge inside it. Final states may be empty. State IDs must be integers; Boolean IDs are explicitly rejected even though Python treats `bool` as a subclass of `int`.

An individual `Transition` validates its own types and label length. Only its containing `Automaton` can determine whether its endpoints exist. Epsilon is `None`; an empty label string is invalid.

Normalizing to frozen sets both isolates caller collections and collapses duplicate entries. Validation does **not** require every state to be reachable or every state to have a transition on every symbol. Those are different properties; [complete-DFA conversion](complete-dfa.md) supplies totality.

## Counts first, bounds second

Let `n` be the number of validated postfix tokens. Let `V` be the number of distinct states, `T` the number of distinct transitions, `A` the number of alphabet symbols, and `m` the input word length.

**Big O**, written `O(f(n))`, is an upper bound on growth up to a constant multiplier for sufficiently large inputs under a stated cost model. It is not a promise of seconds, nor an exact count. We use ordinary average-case hash-table operations and treat state IDs and symbols as constant-size values for this analysis.

For the family of `k` literals joined with dots, such as `a.a.a`, postfix has `2k − 1` tokens. Each literal adds two states and one consuming edge; each concatenation adds one epsilon edge and no states.

| Number of literals `k` | Postfix tokens | States | Transitions |
| --- | --- | --- | --- |
| 1 | 1 | 2 | 1 |
| 2 | 3 | 4 | 3 |
| 4 | 7 | 8 | 7 |

These are exact structural counts for this family in the current construction. The validated postfix builder does constant work per token, so its total time and output size grow linearly, `O(n)`. That construction claim is about processing the validated token sequence; parsing and final model normalization are distinct stages to account for when discussing the entire compiler.

## Setup is work even when little is reached

The public `epsilon_closure` builds adjacency views from **all** transitions before visiting the reachable portion. Let `K` be the number of supplied seeds, `Vε` the reached states, and `Eε` the outgoing epsilon edges examined from them. Its work is `O(K + T + Vε + Eε)` with local adjacency construction included.

A closure reaching only one isolated state can therefore still pay to index a large graph. Conversely, the visited set ensures a reachable epsilon cycle does not create infinite work. A call to `transitions_from` is a linear scan over `T`, while an already-built adjacency map offers direct access to a state's grouped edges. Do not charge the two approaches as if they were the same.

`accepts` builds its maps once per call, then reuses them for every character. It also computes the initial closure before consuming any input. A useful accounting is:

~~~text
one adjacency setup
+ initial closure
+ for each character: examine current states and matching moves, then close targets
~~~

Even after the active set becomes empty, the loop still reads the remaining characters. A coarse bound is `O(T + V + m(V + T + 1))`, with `O(T + V)` auxiliary space. Actual reached sets can be much smaller. This expanded bound makes initial closure and input scanning visible; the source docstring expresses the same design using a sum over reached subgraphs.

## Why DFA conversion can grow much larger

Each DFA state represents a subset of the `V` NFA states. There are at most `2^V` subsets because each state has two membership choices: included or absent. Only reachable closed subsets are generated.

If `D` is the **actual** number of generated DFA states, a complete DFA has exactly `D × A` transitions. That product is an exact count for the returned graph, not the full conversion cost: computing each target subset also takes traversal and set operations. The worst-case subset count can be exponential even though the NFA construction is linear in postfix size.

<details>
<summary>Optional depth: a conservative conversion bound</summary>

The converter indexes the source graph and sorts its alphabet, then processes every discovered subset once and every alphabet symbol for that subset. A coarse per-symbol move-and-closure bound is `O(V + T + 1)`. This gives `O(T + A log A + D(1 + A(V + T + 1)))` time under the stated hash-table model, before suppressing constant and lower-order terms. It includes subset hashing and copying within the coarse state cost.

Storing subsets can need `O(DV)` membership space in addition to source adjacency and `O(DA)` output edges. Replacing `D` by `2^V` gives a worst-case bound, not a prediction for a specific expression. An empty alphabet still needs its one initial subset to be examined even though there are zero output transitions.

</details>

## Predict before revealing

An NFA has 8 states. Conversion produces 5 DFA states over 3 symbols. Must the result contain 256 states because `2^8 = 256`?

<details>
<summary>Answer and reason</summary>

No. 256 is a maximum number of subsets, not a required output size. The measured output has 5 reachable subsets and exactly 15 transitions because it is complete over those 3 symbols. Neither number is a running-time measurement.

</details>

**Common mistake:** timing one tiny example and calling that a complexity proof. Another is quoting reachable traversal cost while omitting adjacency construction. Use exact counts to explain one case and an argument about the loops and data structures to explain growth.

## Source evidence

- **Commentary:** [positioned syntax errors](../../python/src/jautomata/regex.py#L21-L38), [model cost and invariants](../../python/src/jautomata/model.py#L81-L94), [closure setup and traversal](../../python/src/jautomata/simulation.py#L95-L105), [acceptance cost](../../python/src/jautomata/simulation.py#L124-L136), and [subset bound](../../python/src/jautomata/subsets.py#L78-L86).
- **Verified implementation:** [syntax validation](../../python/src/jautomata/regex.py#L99-L173), [graph validation](../../python/src/jautomata/model.py#L101-L125), and [postfix construction](../../python/src/jautomata/thompson.py#L48-L95).
- **Supplement:** the size definitions, family counts and expanded bounds above derive from the implementation under the stated cost model. They are not benchmark results.

## Recap and stop point

Validation separates malformed requests from valid rejections. Complexity separates actual counts, setup costs, reached traversal and worst-case growth.

**Stop here:** explain why one reachable state does not make public closure cost constant. **Resume:** run the [validation and complexity tutorial](../tutorials/validation-complexity.md), check its error positions, and compare its measured graph sizes with the bounds.
