# Source map for the complete curriculum

Use this map to connect a lesson to the comments and implementation that motivated it. Start with the [complete learning map](../learning-map.md), or choose a theory/tutorial pair below. The [getting-started guide](../getting-started.md) provides the shared setup.

Each topic pairs a focused explanation with a runnable tutorial. Historical Java examples supply context; the documented Python contract supplies the executable behavior.

## How to read the evidence

- **Commentary** means a Java comment or Python docstring states the idea. A linked span may also include the nearby implementation.
- **Source behavior** means the implementation or example demonstrates the behavior, even when its comments do not explain it.
- **Supplement** means an explicitly added definition, derivation or prerequisite that helps explain the source. It does not claim that the original comments contained a complete textbook treatment.

The map covers all eleven original Java files and all six Python library modules. Author stamps, diagnostic print statements and unfinished comment fragments add no separate theory topics.

## Start with the model and notation

### Finite automata and languages

[Theory](../theory/automata.md) · [Runnable tutorial](../tutorials/automata.md)

**You will learn:** Describe states, input symbols, start/final states, and whole-string acceptance.
**Before this topic:** Basic Python; sets and graph notation introduced here.

**Commentary:** [Immutable automaton model and epsilon](../../python/src/jautomata/model.py#L1-L17); [State-set and graph invariants](../../python/src/jautomata/model.py#L69-L94); [Public operations](../../python/src/jautomata/__init__.py#L1-L5).
**Source behavior:** [Consuming versus epsilon transitions](../../src/Model/AutomataStructure/Transicion.java#L12-L36).
**Supplement:** Introduce the formal tuple, finite sets, strings, languages, empty string, empty language, and empty active set. These definitions explain the implementation; they are not quotations from its comments.

**Try it:** Construct a machine by hand; predict empty, accepting and rejecting inputs; check its alphabet and structural constraints.

### Regular expressions and language operations

[Theory](../theory/regex.md) · [Runnable tutorial](../tutorials/regex.md)

**You will learn:** Explain literals, concatenation, union, star, plus and grouping in the supported dialect.
**Before this topic:** automata

**Commentary:** [Supported grammar and literal rules](../../python/src/jautomata/regex.py#L1-L13); [Literal and operator node meanings](../../python/src/jautomata/regex.py#L42-L75).
**Source behavior:** [Precedence table](../../src/ExpresionRegularToAFN/ShuntingYard.java#L13-L30).
**Supplement:** Give language-set meanings for each operator, introduce nullable expressions, and distinguish empty input from invalid empty regex syntax.

**Try it:** Compile operator examples, assert language fixtures, compare precedence/grouping, and check literal punctuation/Unicode and invalid implicit concatenation.

### Parsing, postfix notation and syntax trees

[Theory](../theory/parsing.md) · [Runnable tutorial](../tutorials/parsing.md)

**You will learn:** Trace infix tokens into postfix order and an immutable abstract syntax tree.
**Before this topic:** regex

**Commentary:** [Iterative parser rationale](../../python/src/jautomata/regex.py#L91-L98); [Parser and postfix contracts](../../python/src/jautomata/regex.py#L200-L228).
**Source behavior:** [Historical operator stack](../../src/ExpresionRegularToAFN/ShuntingYard.java#L32-L60); [Validation and operator handling](../../python/src/jautomata/regex.py#L99-L173); [AST assembly and operand order](../../python/src/jautomata/regex.py#L176-L197).
**Supplement:** Introduce stack notation, arity and tree vocabulary; show a token-by-token stack table and why left/right order matters. The focus stays on this parser rather than a general context-free-language course.

**Try it:** Use to_postfix and parse; inspect node structure, operator chains and positioned errors using public imports from jautomata.regex.

## Build one Thompson fragment at a time

### Thompson literal fragments

[Theory](../theory/literal.md) · [Runnable tutorial](../tutorials/literal.md)

**You will learn:** Build the two-state literal fragment and explain its one-entry/one-exit invariant.
**Before this topic:** automata, regex, parsing

**Commentary:** [Basic Thompson construction](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L64-L84); [Fragments and fragment-stack rationale](../../python/src/jautomata/thompson.py#L22-L55).
**Source behavior:** [Literal allocation](../../python/src/jautomata/thompson.py#L56-L63).
**Supplement:** Explain fragment invariants, fresh state names, and the literal base case for a compositional correctness argument.

**Try it:** Compile and inspect a literal, assert exact states/edge shape where documented, and compare a hand-built equivalent machine.

### Thompson concatenation

[Theory](../theory/concatenation.md) · [Runnable tutorial](../tutorials/concatenation.md)

**You will learn:** Connect fragments in order and compare epsilon-link concatenation with the historical fusion variant.
**Before this topic:** literal

**Commentary:** [Two concatenation variants](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L87-L117); [Chosen ownership and concatenation policy](../../python/src/jautomata/thompson.py#L1-L10).
**Source behavior:** [Ordered epsilon-link construction](../../python/src/jautomata/thompson.py#L65-L70).
**Supplement:** Derive language concatenation and explain the assumptions required before fusing fragment endpoints. Distinguish graph shape from recognized language.

**Try it:** Inspect a.b, trace the connecting epsilon edge, reject reversed/partial words, and compare explanatory diagrams for the two variants without modifying runtime code.

### Thompson union

[Theory](../theory/union.md) · [Runnable tutorial](../tutorials/union.md)

**You will learn:** Explain the fresh entry/exit and epsilon paths that represent either alternative.
**Before this topic:** literal, concatenation

**Commentary:** [Union construction](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L119-L143); [Standard union/star/plus topology](../../python/src/jautomata/thompson.py#L116-L121).
**Source behavior:** [Union edges](../../python/src/jautomata/thompson.py#L72-L82).
**Supplement:** Connect the four epsilon edges to set union and explain that nondeterministic choice retains every possible branch.

**Try it:** Draw and inspect a|b, assert both alternatives and rejected combinations, then compose a grouped union with concatenation.

### Kleene star

[Theory](../theory/kleene-star.md) · [Runnable tutorial](../tutorials/kleene-star.md)

**You will learn:** Explain zero or more repetitions through the bypass, repeat edge and exit.
**Before this topic:** literal, concatenation, union

**Commentary:** [Kleene closure construction](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L165-L186); [Zero-or-more meaning](../../python/src/jautomata/regex.py#L64-L68).
**Source behavior:** [Repeat and bypass edges](../../python/src/jautomata/thompson.py#L84-L92).
**Supplement:** Define L*, show its empty-word case, and explain nullable operands and the cycles created by composition.

**Try it:** Inspect a*, predict empty/one/many occurrences, and trace nested closures with the delivered cycle-safe evaluator.

### Positive closure

[Theory](../theory/positive-closure.md) · [Runnable tutorial](../tutorials/positive-closure.md)

**You will learn:** Distinguish one repetition from one consumed character.
**Before this topic:** kleene-star

**Commentary:** [Positive closure construction](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L144-L164); [One-or-more meaning](../../python/src/jautomata/regex.py#L72-L75).
**Source behavior:** [Shared repeat construction, star-only bypass](../../python/src/jautomata/thompson.py#L84-L92).
**Supplement:** Define L+ and compare it with L*; show why (a*)+ accepts empty input even though a+ rejects it.

**Try it:** Compare a+, a* and (a*)+ with structural inspection and accepted/rejected fixtures.

## Recognize words and construct a DFA

### Epsilon closure and reachability

[Theory](../theory/epsilon-closure.md) · [Runnable tutorial](../tutorials/epsilon-closure.md)

**You will learn:** Find every state reachable without consuming input and terminate safely on cycles.
**Before this topic:** automata, literal

**Commentary:** [Closure contract, invariant and cost](../../python/src/jautomata/simulation.py#L80-L106).
**Source behavior:** [Visited work list](../../python/src/jautomata/simulation.py#L67-L77); [Historical recursive closure](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L119-L133).
**Supplement:** Introduce graph reachability, work-list invariants, extensiveness and idempotence; explain them as consequences of the algorithm.

**Try it:** Trace empty/multiple seeds, epsilon self-loops and cycles; assert closures and demonstrate why visited states are needed.

### NFA simulation and acceptance

[Theory](../theory/nfa-simulation.md) · [Runnable tutorial](../tutorials/nfa-simulation.md)

**You will learn:** Maintain every possible current state and decide acceptance only after all input is consumed.
**Before this topic:** automata, epsilon-closure

**Commentary:** [Acceptance contract and algorithm](../../python/src/jautomata/simulation.py#L113-L142); [Original NFA verification aim](../../src/Practica1/Practica1Main.java#L11-L13).
**Source behavior:** [Move then close](../../python/src/jautomata/simulation.py#L143-L153); [Historical evaluator branch handling](../../src/Model/AutomataStructure/Estado.java#L32-L80); [Single matching-edge lookup](../../src/Model/AutomataStructure/Estado.java#L100-L110).
**Supplement:** State and justify the prefix-reachability invariant; distinguish nondeterministic possibilities from thread scheduling.

**Try it:** Construct same-symbol branches and consuming/epsilon alternatives; trace acceptance, rejection, empty input and machines with multiple/no final states.

### Subset construction and equivalence

[Theory](../theory/subset-construction.md) · [Runnable tutorial](../tutorials/subset-construction.md)

**You will learn:** Represent each epsilon-closed NFA state set as one DFA state.
**Before this topic:** nfa-simulation

**Commentary:** [Historical work-list explanation](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L35-L43); [Full-subset invariants and BFS contract](../../python/src/jautomata/subsets.py#L57-L87).
**Source behavior:** [Subset discovery, finality and transitions](../../python/src/jautomata/subsets.py#L91-L124); [Abandoned and active kernel equality](../../src/AFDtoAFDbySubsets/Subconjunto.java#L53-L67).
**Supplement:** Distinguish move kernel from its closure, explain set identity, prove the NFA/DFA correspondence by input prefixes, and derive the 2^N upper bound.

**Try it:** Fill a complete subset table, identify initial/final subsets, inspect deterministic numbering, and check bounded language agreement without calling finite tests a proof.

### Complete DFAs and the empty-subset sink

[Theory](../theory/complete-dfa.md) · [Runnable tutorial](../tutorials/complete-dfa.md)

**You will learn:** Explain total transitions over the source alphabet and the reachable empty-subset sink.
**Before this topic:** subset-construction

**Commentary:** [Complete-DFA policy](../../python/src/jautomata/subsets.py#L1-L11); [Alphabet, reachability and finality contract](../../python/src/jautomata/subsets.py#L64-L82); [Alphabet and outgoing-edge views](../../python/src/jautomata/model.py#L128-L142).
**Source behavior:** [Transitions for every source-alphabet symbol](../../python/src/jautomata/subsets.py#L106-L117).
**Supplement:** Distinguish determinism from totality; derive behavior for an empty alphabet, symbols outside the alphabet, no final states, and source symbols occurring only on unreachable NFA edges.

**Try it:** Assert one transition per state/symbol, inspect sink self-loops, and exercise empty-alphabet/no-final and unreachable-source-symbol cases.

## Explain implementation decisions

### Identity, equality and immutable graphs

[Theory](../theory/identity.md) · [Runnable tutorial](../tutorials/identity.md)

**You will learn:** Distinguish state identity, structural value equality and language equivalence.
**Before this topic:** automata, concatenation, subset-construction

**Commentary:** [Historical equality comment](../../src/Model/AutomataStructure/Estado.java#L172-L175); [Copying and transition ownership comments](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L188-L221); [Value equality and normalized collections](../../python/src/jautomata/model.py#L36-L94).
**Source behavior:** [Kernel equality experiment](../../src/AFDtoAFDbySubsets/Subconjunto.java#L53-L67); [Frozen-set normalization and validation](../../python/src/jautomata/model.py#L101-L125).
**Supplement:** Explain object aliases, duplicate collapse, hashing and graph relabeling. Equal outgoing edges alone do not establish language equivalence; minimization is outside this course.

**Try it:** Demonstrate independent caller collections, duplicate transitions and repeated compilation; compare graph/value identity with bounded language agreement.

### Pure execution and work-list design

[Theory](../theory/pure-execution.md) · [Runnable tutorial](../tutorials/pure-execution.md)

**You will learn:** Explain why each recognition call owns its traversal state.
**Before this topic:** nfa-simulation, identity

**Commentary:** [Thread-wait warning and result flags](../../src/Model/AutomataStructure/Automata.java#L28-L52); [Pure iterative simulation rationale](../../python/src/jautomata/simulation.py#L1-L10); [Per-call adjacency rationale](../../python/src/jautomata/simulation.py#L42-L48).
**Source behavior:** [Historical asynchronous branches](../../src/Model/AutomataStructure/Estado.java#L32-L80); [Local closure state](../../python/src/jautomata/simulation.py#L67-L77).
**Supplement:** Explain execution state versus graph data, stack/queue work lists, race-condition reasoning and repeated-call independence. Historical hazards are source-flow findings, not new Java runtime reproductions.

**Try it:** Repeat mixed accepting/rejecting calls, snapshot immutable inputs and trace local work lists without creating a new regex engine.

### Validation and algorithmic complexity

[Theory](../theory/validation-complexity.md) · [Runnable tutorial](../tutorials/validation-complexity.md)

**You will learn:** Interpret structural/syntax errors and derive costs from actual work.
**Before this topic:** parsing, epsilon-closure, subset-construction, identity

**Commentary:** [Positioned syntax error](../../python/src/jautomata/regex.py#L21-L38); [Structural errors and construction cost](../../python/src/jautomata/model.py#L81-L94); [Closure cost and termination](../../python/src/jautomata/simulation.py#L95-L105); [Acceptance cost](../../python/src/jautomata/simulation.py#L124-L136); [Exponential subset bound](../../python/src/jautomata/subsets.py#L78-L86); [Iterative construction cost](../../python/src/jautomata/thompson.py#L49-L55).
**Source behavior:** [Position-aware validation](../../python/src/jautomata/regex.py#L99-L173); [Model validation](../../python/src/jautomata/model.py#L101-L125).
**Supplement:** Introduce asymptotic notation and relevant size variables, separate setup from traversal, and distinguish worst-case bounds from one measurement. Avoid performance promises based only on tiny examples.

**Try it:** Assert precise error classes/positions and graph constraints; count tokens/states/transitions on controlled examples and explain linear compilation versus exponential possible DFA growth.

## Historical source labs

### Practica 1: reconstruct and recognize a hand-built NFA

[Open the lab](../labs/practica1.md)

**Source status:** Active original example.
**Commentary and examples:** [NFA verification and epsilon-cycle example](../../src/Practica1/Practica1Main.java#L11-L42).
**Supplement:** Infer the graph's language: odd-length all-1 words or even-length all-0 words, including empty input. This language characterization is inferred, not stated in the comment.

**Try it:** Reconstruct its six states in Python, trace both branches and the cycle, and compare NFA/DFA results with an independent parity predicate over bounded words.

### Practica 2: compile a compound expression

[Open the lab](../labs/practica2.md)

**Source status:** Active original example.
**Commentary and examples:** [Original NFA-generation goal and expression](../../src/Practica2/Practica2.java#L9-L15).
**Supplement:** Derive the language of ((b.c.d)*|f+.a).f; f is accepted because the left star can take zero repetitions.

**Try it:** Trace grouping, postfix and each constructor; assert accepted examples f, bcdf, faf and rejected examples empty input, bcd, fa.

### Practica 3: follow regex through NFA and DFA

[Open the lab](../labs/practica3.md)

**Source status:** Active original example.
**Commentary and examples:** [Equivalent-DFA goal and expression](../../src/Practica3/Practica3Main.java#L10-L23).
**Supplement:** Explain each block of (a.b|a*.c)+ and why the entire expression rejects empty input.

**Try it:** Expand the existing capstone with construction/subset traces, a complete-DFA check, and bounded language agreement. Link to and preserve the existing tutorial route.

### Main: read and verify historical experiments

[Open the lab](../labs/main.md)

**Source status:** Mixed: the file contains commented probes, unused live setup, and one active final conversion.
**Commentary and examples:** [Commented manual NFA evaluations](../../src/com/company/Main.java#L17-L63); [Commented Thompson and alphabet probes](../../src/com/company/Main.java#L91-L102); [Commented subset-equality experiments](../../src/com/company/Main.java#L103-L138).
**Source behavior:** [Live but unused hand-built setup](../../src/com/company/Main.java#L64-L86); [Active final NFA-to-DFA demo](../../src/com/company/Main.java#L140-L146).
**Supplement:** The complex `((a.a+)|(c+)|(b.c*))+` expression at [line 99](../../src/com/company/Main.java#L99) is a commented probe, not the final run. The active conversion at lines 140–146 uses `(a.b|a*.c)+`. Use the subset probes to revisit equality without treating scratch output as an oracle.

**Try it:** Turn selected historical probes into independent Python assertions, then use the other labs for their complete reconstructions.

## Read historical comments with the implementation

- **A comment proposes implicit dots.** [Source](../../src/ExpresionRegularToAFN/ShuntingYard.java#L51-L54). The active literal branch only appends its token. Explicit concatenation remains required. The nearby 'digit' label also describes a branch that accepts other literal characters.
- **The start-state explanation is too informal.** [Source](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L35-L48). The DFA start represents the epsilon closure of the NFA start; it is a newly represented subset, not the original state object.
- **An old note says closure and move were fixed.** [Source](../../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L51-L54). Read this as historical progress commentary. The recursive closure still has no visited guard; the source-linked Java reference explains the finality limitations.
- **Regex epsilon remains a TODO.** [Source](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L62-L71). This concerns a regex-level epsilon token. Internal epsilon transitions already exist. The basic-construction comment also mentions a counter parameter absent from its signature.
- **'Copy' does not mean independent graph objects.** [Source](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L188-L221). The historical helpers share state/transition objects and mutate transition origins. Explain aliases before comparing them with Python value objects.
- **Comparing transitions is not a definition of language equivalence.** [Source](../../src/Model/AutomataStructure/Estado.java#L172-L175). The comment calls name-only equality temporary. State identity, graph structure and accepted-language equivalence are different questions.
- **A single final state is a fragment assumption.** [Source](../../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L224-L236). The helper assumes one final state. General finite automata can have multiple final states or none; the Python model supports them.
- **The thread-wait warning is real source evidence.** [Source](../../src/Model/AutomataStructure/Automata.java#L28-L52). The code starts processing and immediately reads mutable result flags. Teach the source-flow limitation and the Python local-state design without claiming a new Java runtime reproduction.

For the detailed historical findings, use [Java reference behavior](../java-reference.md). For the current grammar and algorithm guarantees, use [Compatibility](../compatibility.md) and the [Python API](../python-api.md).

## Keep the scope visible

The lessons introduce sets, graphs, induction and cost notation only where needed to explain these algorithms. DFA minimization, the pumping lemma, general context-free grammars and Turing machines are outside this curriculum. Short sections, visible traces and optional formal depth support focused study; they are not a claim of clinical effectiveness.
