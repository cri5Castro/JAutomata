# NFA simulation: keep every possible state

**Objective:** Trace an entire input through an epsilon-NFA and decide acceptance from the complete set of reachable states.

**Before you start:** [Automata](automata.md), [epsilon closure](epsilon-closure.md). **Then practice:** [Runnable NFA tutorial](../tutorials/nfa-simulation.md).

An NFA can offer several ways to read the same character. Choosing one path can lose a valid match. Simulation instead stores every state that could be current after the same input prefix. A set represents alternatives; it does not require parallel threads.

## Closure, move, closure

Let `C(S)` mean epsilon closure. Let `move(S, a)` mean all targets of edges labeled `a` leaving any state in `S`. `a` is one character, not an arbitrary word.

1. Initialize the active set with `C({start})`.
2. For each character, collect **all** matching targets from the active set.
3. Close that target set before reading the next character.
4. After the entire word, accept exactly when an active state is final.

The shorthand is `next = C(move(current, a))`. The current set is already closed, so this is often called closure–move–closure without needing a redundant closure call before every step.

## One graph with competing paths

Our six-state example starts at 0 and has final states 4 and 5.

**Read the figure:** Start at `0`; keep both direct `a` branches and the `ε` route to `1`. Double circles mark finals `4` and `5`.

<div class="diagram-scroll" tabindex="0" role="region" aria-label="Three ways to consume a, then follow b, scrollable diagram" style="--diagram-width: 596px">
  <img class="diagram" src="/JAutomata/diagrams/competing-paths.svg" alt="Start 0 has epsilon to 1 and a edges to 2 and 3; 1 has a to final 5, 3 has epsilon to final 4, 2 has b to 5, and 4 loops on b.">
</div>
<p class="diagram-link">Scroll sideways when needed. <a href="/JAutomata/diagrams/competing-paths.svg">Open full-size diagram</a></p>

| Source | Label | Target | Why it matters |
| --- | --- | --- | --- |
| 0 | ε | 1 | A free alternative before consuming |
| 0 | a | 2 | First direct `a` branch |
| 0 | a | 3 | Second direct `a` branch |
| 1 | a | 5 | `a` available through the epsilon alternative |
| 3 | ε | 4 | Free movement after consuming |
| 2 | b | 5 | A path that can consume one `b` |
| 4 | b | 4 | A path that can consume arbitrarily many `b`s |

State 0 has both consuming and epsilon edges. Neither kind cancels the other. After the initial closure, both 0 and 1 are available; the next move must inspect both.

## Worked trace: `abb`

The **kernel** column is the raw result of a move, before closure. We will reuse this distinction in determinization.

| Consumed prefix | Next operation | Move kernel | Closed active set | Final state present? |
| --- | --- | --- | --- | --- |
| `""` | Initial closure | — | `{0, 1}` | no |
| `a` | Consume `a`, then close | `{2, 3, 5}` | `{2, 3, 4, 5}` | yes |
| `ab` | Consume `b`, then close | `{4, 5}` | `{4, 5}` | yes |
| `abb` | Consume `b`, then close | `{4}` | `{4}` | yes |

On the first move, the direct branches contribute 2 and 3; the epsilon alternative contributes 5. Closing adds 4. On the next `b`, state 2 contributes 5 and state 4 contributes 4. Other branches disappear because they cannot consume that character.

The final row accepts `abb`. The earlier “yes” rows would accept if input ended there, but do not permit stopping while characters remain.

**Predict:** The first character of `aa` reaches a final state. Does the whole word accept?

<details>
<summary>Reveal the next step</summary>

No. No state in `{2, 3, 4, 5}` has an `a` edge. The second move gives `∅`, and `C(∅) = ∅`. After all input, the active set contains no final state. Reaching a final state after a prefix cannot consume the remaining characters for free.

</details>

## Empty input, several finals, and no finals

For empty input `""`, perform the initial closure and then check finality. The start state itself need not be final: an epsilon path to a final state is enough. Our example rejects empty input because `{0, 1}` contains neither 4 nor 5.

With several final states, acceptance uses **any** intersection with the final-state set. All branches need not accept. With no final states, every word rejects, including empty input, even when transitions and cycles exist.

An empty active set also stays empty on all subsequent input: there is no state from which a move can start. If a character occurs nowhere in the alphabet, its move is empty. The evaluator returns `False` for such a string; it does not treat the unknown character as epsilon.

<details>
<summary>Optional depth: the prefix-reachability invariant</summary>

Let a word be `w = a₁a₂…aₘ`. After consuming its first `i` characters, the active set contains **exactly** the states reachable from the start by a path whose consuming labels spell that prefix; epsilon labels contribute no characters. The paths may include epsilon edges before, between or after consuming edges.

For `i = 0`, the initial closure enumerates exactly the paths consuming nothing. Suppose the invariant holds for `i`. Any path consuming the next character must start from a state in the current closure, follow one edge labeled `aᵢ₊₁`, and possibly follow epsilon edges afterward. `move` enumerates all such labeled edges; closure enumerates their free continuations. Conversely, every state produced this way has a path spelling the extended prefix. That proves the induction step.

After `m` characters, an accepting path exists exactly when this complete set intersects the final states. This is the correctness argument. A list of matching test cases can support an implementation check but cannot replace this invariant for arbitrary input lengths.

The implementation builds adjacency maps once per `accepts` call, costing `O(T)` for `T` transitions. Each character then explores the relevant move and epsilon-reachable subgraph. Keeping a set merges duplicate ways to reach the same state, avoiding a separate recursive branch for every path. It does not make all possible NFA simulations constant-time.

</details>

## Common mistakes

- Taking only the first matching edge. From state 0, both `a` edges contribute.
- Exploring epsilon only when no consuming edge matches. State 1 remains an alternative even when 0 can consume directly.
- Skipping closure after the move. That would miss state 4 and its `b` loop.
- Requiring all active states to be final. Acceptance asks whether at least one complete accepting path exists.

## Exercise: change only the final states

Keep the graph unchanged. First make `{1}` the final-state set; then make it empty. For each version, predict empty input, `a`, and `b`.

<details>
<summary>Reveal the outcomes and why</summary>

With finals `{1}`, empty input accepts because initial closure is `{0, 1}`. `a` rejects because its final active set is `{2, 3, 4, 5}`, which excludes 1. `b` rejects because its active set becomes empty immediately. With no finals, all three reject: no reached set can intersect an empty final-state set. Changing finals changes acceptance, but does not change the closure or move trace.

</details>

## Where the lesson comes from

**Source commentary:** The [Python acceptance contract](../../python/src/jautomata/simulation.py#L113-L142) describes complete state sets; [Practica 1's comment](../../src/Practica1/Practica1Main.java#L11-L13) states the original NFA-verification aim. **Actual implementation:** [Move followed by closure](../../python/src/jautomata/simulation.py#L143-L153) implements the recurrence and checks finality only after all characters.

**Historical distinction:** The Java evaluator's [branch handling](../../src/Model/AutomataStructure/Estado.java#L32-L80) and [single matching-edge lookup](../../src/Model/AutomataStructure/Estado.java#L100-L110) do not preserve all these alternatives. These are documented static source findings, not a new Java runtime experiment. The [Java reference audit](../java-reference.md#defects-and-port-decisions) records related limitations. The trace and induction proof here are supplemental explanations of the corrected Python behavior.

## Recap and resume

Keep every possibility after the same prefix. Close initially, move on one character, close again, and test finality only when input ends.

**Stop cue:** Write the active sets after `""`, `a`, `ab`, and `abb`. **Resume cue:** Run the [paired tutorial](../tutorials/nfa-simulation.md) to check each row. Next, [subset construction](subset-construction.md) turns those whole sets into individual DFA states.
