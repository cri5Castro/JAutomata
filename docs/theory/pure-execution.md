# Pure execution and local work lists

**Goal:** explain why recognition data belongs to one call, and why an NFA does not require operating-system threads.

**Before you start:** [NFA simulation](nfa-simulation.md) and [identity](identity.md). Recall that epsilon, written `ε`, changes state without consuming input.

**Route:** separate graph from run → trace a cycle → examine timing → predict. The [paired tutorial](../tutorials/pure-execution.md) checks repeated calls.

## A graph is a reusable question

An automaton stores the question “which words belong to this language?” A run supplies one word and computes its answer. Store permanent and temporary information separately:

| Permanent graph data | Local data for one run |
| --- | --- |
| States and start state | Current set of possible states |
| Final states | Targets after one input character |
| Labeled transitions | Epsilon-closure visited set and pending work |

In the delivered Python API, `accepts(machine, text)` returns a Boolean and leaves the machine unchanged. Repeating that call with the same arguments gives the same result. Local sets and dictionaries may mutate while computing it: purity at this API boundary does not require every temporary variable to be immutable.

## Nondeterminism is a semantic choice

“Nondeterministic” means that several transitions may be possible for the same input prefix. A word is accepted if **at least one complete path** consumes the entire word and ends in a final state.

The simulation keeps all possible states in a set. It does not pick a random edge, and it does not ask a scheduler to choose which answer wins. One ordinary thread can compute the entire set.

~~~text
                    a
              ┌──────────> 2*  (accepting)
start 0 ─ε─> 1
       <─ε───┘
       └──────a──────────> 3 ──b──> 4*
~~~

Initial closure is `{0, 1}`. After `a`, both `{2, 3}` remain possible. The word `a` accepts because `2` is final. For `ab`, the branch at `2` has no `b` move, but the branch at `3` reaches `4`, so that word also accepts. The algorithm must retain the nonfinal branch at `3` even while another branch is already final.

## Worked trace: stop an epsilon cycle

A **work list** holds discovered states still needing examination. A **visited set** records states already discovered in this closure computation. The implementation uses a stack: the last appended item is processed first.

| Action | Pending stack | Visited |
| --- | --- | --- |
| Seed with 0 | `[0]` | `{0}` |
| Pop 0, discover 1 | `[1]` | `{0, 1}` |
| Pop 1, see 0 already visited | `[]` | `{0, 1}` |
| Return | empty | `{0, 1}` |

Mark a state when adding it, so it is never added twice in this closure. A queue would change processing order but compute the same reachable set. The actual implementation uses a list and `pop()` for closure, while subset conversion uses a queue for stable breadth-first state numbering.

**Visited is local to one closure.** A state can legitimately occur again after the next character or on a later recognition call. A permanent “visited once ever” flag would incorrectly prune those paths.

## Why the Java timing warning matters

The historical Java evaluator starts processing and then checks mutable acceptance flags. Its own comment warns that it should wait for other threads. Branch processing starts asynchronous threads; the final check also resets flags.

An illustrative timing hazard is:

~~~text
main evaluator: start branch ── check flag(false) ── reset flags
branch worker:                  still running ─────── set accepted(true)
~~~

This ordering could report before a branch finishes or leave a late flag for another call. It explains a risk visible in control flow; it is not a claim that this exact interleaving was reproduced. Correct thread coordination could support a concurrent evaluator, but concurrency is unnecessary to define NFA semantics.

Python builds adjacency maps locally for each call. An **adjacency map** groups edges by origin and label, so traversal need not scan every edge for every state. Each call owns those maps and its work lists; no prior run contributes an acceptance flag.

<details>
<summary>Optional depth: the two invariants</summary>

Closure invariant: every visited state is epsilon-reachable from a seed, and every discovered but unprocessed state is pending. When pending is empty, all epsilon edges leaving discovered states have been examined. Finite states and one admission per state guarantee termination.

Recognition invariant: after a prefix of the input, `current` is exactly the set reachable by consuming that prefix, with any epsilon moves before, between and after its characters. The initial closure establishes the empty-prefix case. Taking every matching move and then its closure preserves the claim. After the full word, intersection with the final set decides acceptance.

These are supplemental correctness arguments. They explain why temporary mutation of local work lists produces a stable result without thread scheduling.

</details>

## Predict before revealing

The machine above accepts `a`. If the next call asks about the empty word, should it accept because the earlier call reached state `2`?

<details>
<summary>Answer and reason</summary>

No. The next call starts from the initial closure `{0, 1}` again. Neither state is final. Acceptance from the earlier run is not part of the graph. Similarly, `aa` rejects: after the first `a`, neither state `2` nor state `3` has an `a` transition.

</details>

**Common mistake:** returning immediately when any final state appears before all characters have been consumed. Finality answers the question for the prefix so far, not for every possible suffix. Another mistake is caching execution flags on an otherwise reusable graph.

## Source evidence

- **Commentary:** [pure iterative simulation rationale](../../python/src/jautomata/simulation.py#L1-L10), [per-call adjacency rationale](../../python/src/jautomata/simulation.py#L42-L48), and [the Java thread warning and flag reset](../../src/Model/AutomataStructure/Automata.java#L28-L52).
- **Verified implementation:** [Java asynchronous branch flow](../../src/Model/AutomataStructure/Estado.java#L32-L80), [Python closure's local sets](../../python/src/jautomata/simulation.py#L67-L77), and [full recognition loop](../../python/src/jautomata/simulation.py#L143-L153).
- **Supplement:** the timing diagram illustrates a possible ordering from source flow. The invariants justify the current algorithm; neither is a new Java runtime experiment.

## Recap and stop point

Keep graph data reusable and traversal data local. Sets represent all semantic possibilities; work lists terminate on cycles by avoiding repeated work within one closure.

**Stop here:** state when a visited set must be discarded. **Resume:** run the [pure-execution tutorial](../tutorials/pure-execution.md) and check that alternating accepted and rejected inputs leaves the graph snapshot unchanged.
