# Java reference behavior

Use this as evidence and historical commentary, not as a first lesson. The
[learning path](index.md#learn) explains the Python contract first, then links
back here where a Java comment motivated an intentional correction.

This source-linked audit covers all eleven Java files. It separates intended
regular-language semantics from observed Java behavior; Java is not the
correctness oracle for the Python port.

## Inventory and source commentary

| File | Role and active entry points | Commentary / examples |
|---|---|---|
| `src/Model/AutomataStructure/Automata.java` | Mutable machine: state/start/edge insertion, alphabet, `evaluar`, `getEstadoFinal` ([10-164](../src/Model/AutomataStructure/Automata.java#L10-L164)). | `evaluar` reports stdout; the author flags its threading problem at [31](../src/Model/AutomataStructure/Automata.java#L31). `getEstadoFinal` says it is only for Thompson automata at [121](../src/Model/AutomataStructure/Automata.java#L121). |
| `src/Model/AutomataStructure/Estado.java` | State, transition lookup, epsilon lookup, recursive/asynchronous evaluation ([10-177](../src/Model/AutomataStructure/Estado.java#L10-L177)). | Inactive [39-46](../src/Model/AutomataStructure/Estado.java#L39-L46) acknowledges epsilon-loop trouble; [172](../src/Model/AutomataStructure/Estado.java#L172) calls name-only equality temporary. |
| `src/Model/AutomataStructure/Transicion.java` | Directed label; empty label is epsilon; forwards unchanged or consumes one character ([6-75](../src/Model/AutomataStructure/Transicion.java#L6-L75)). | Constructor comment [13](../src/Model/AutomataStructure/Transicion.java#L13) records the equality-check decision. |
| `src/ExpresionRegularToAFN/ShuntingYard.java` | Single-character infix-to-postfix parser ([11-61](../src/ExpresionRegularToAFN/ShuntingYard.java#L11-L61)). | [53](../src/ExpresionRegularToAFN/ShuntingYard.java#L53) says normal tokens should gain a dot, but active code only appends them. |
| `src/ExpresionRegularToAFN/ConstructorDeAutomatas.java` | Postfix stack plus public Thompson operations ([15-238](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L15-L238)). | Class comment names Thompson construction [9-14](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L9-L14); regex epsilon representation remains TODO at [62](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L62). |
| `src/AFDtoAFDbySubsets/Subconjunto.java` | Prospective DFA state: `kernel`, epsilon `cerradura`, backing state ([12-68](../src/AFDtoAFDbySubsets/Subconjunto.java#L12-L68)). | Abandoned equality experiment [53-63](../src/AFDtoAFDbySubsets/Subconjunto.java#L53-L63); active equality is kernel-only [64-67](../src/AFDtoAFDbySubsets/Subconjunto.java#L64-L67). |
| `src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java` | Work-list subset conversion, move, recursive closure ([16-135](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L16-L135)). | Intended work-list rationale [35-43](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L35-L43); [52](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L52) says the containing loop needed repair. |
| `src/Practica1/Practica1Main.java` | Active hand-built NFA evaluator example ([12-43](../src/Practica1/Practica1Main.java#L12-L43)). | It calls itself NFA string verification [11](../src/Practica1/Practica1Main.java#L11), and supplies an epsilon cycle [30-31](../src/Practica1/Practica1Main.java#L30-L31). |
| `src/Practica2/Practica2.java` | Active regex-to-NFA printing example ([12-16](../src/Practica2/Practica2.java#L12-L16)). | Comment says it generates an NFA [9-11](../src/Practica2/Practica2.java#L9-L11). |
| `src/Practica3/Practica3Main.java` | Active regex-NFA then subset-DFA printing example ([12-24](../src/Practica3/Practica3Main.java#L12-L24)). | Comments describe subset conversion [10-11](../src/Practica3/Practica3Main.java#L10-L11). |
| `src/com/company/Main.java` | Scratch/demo program; live but unused setup builds `b` and `c` at [64-86](../src/com/company/Main.java#L64-L86), while the final printed regex-to-DFA conversion is [140-146](../src/com/company/Main.java#L140-L146). | Manual NFA evaluation [17-63](../src/com/company/Main.java#L17-L63), Thompson probes [91-102](../src/com/company/Main.java#L91-L102), and subset experiments [103-138](../src/com/company/Main.java#L103-L138) are commented out. |

## Grammar and parsing contract inferred from Java

`infix.split("")` makes this a sequence of one-character tokens
([ShuntingYard 37](../src/ExpresionRegularToAFN/ShuntingYard.java#L37)).

| Form | Intended language meaning | Evidence |
|---|---|---|
| `x` | A literal edge labelled `x`. | Default postfix branch builds a two-state fragment ([Constructor 49-52, 71-84](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L49-L84)). |
| `r.s` | Explicit concatenation. | `.` precedence 2; parser uses state-fusion concat ([ShuntingYard 15-25](../src/ExpresionRegularToAFN/ShuntingYard.java#L15-L25), [Constructor 38-43](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L38-L43)). |
| `r|s` | Union. | Precedence 1 dispatch at [44-47](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L44-L47) uses fresh start/final construction at [126-142](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L126-L142). |
| `r*` | Zero or more. | Precedence 3 dispatch at [32-34](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L32-L34); fresh-start bypass is at [171-185](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L171-L185). |
| `r+` | One or more. | Precedence 3 dispatch at [35-37](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L35-L37); operand entry and loop are at [150-163](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L150-L163). |
| `(r)` | Grouping. | Parentheses only control the postfix stack ([ShuntingYard 43-50](../src/ExpresionRegularToAFN/ShuntingYard.java#L43-L50)). |

The conversion pops equal-or-higher precedence operators
([ShuntingYard 27-30, 39-42](../src/ExpresionRegularToAFN/ShuntingYard.java#L27-L42));
binary operators are left-associative. `*` and `+` are equal-precedence
postfix operators processed left-to-right. Explicit `.` is required: the
dot-insertion comment is not code, so `ab` is not defined as `a.b`.

Epsilon is internal only: `Transicion` makes `""` epsilon
([12-24](../src/Model/AutomataStructure/Transicion.java#L12-L24)); no regex
epsilon literal exists ([Constructor 62](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L62)).

Malformed input has no validation contract. Static outcomes are stack underflow
for unmatched `)` ([47-50](../src/ExpresionRegularToAFN/ShuntingYard.java#L47-L50)),
emitting unmatched `(` ([58-59](../src/ExpresionRegularToAFN/ShuntingYard.java#L58-L59)),
and operand underflow for operators ([Constructor 32-47](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L32-L47)).
Empty input and adjacent literals are unspecified because construction pops one
fragment without checking stack cardinality ([56](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L56)).
These findings are static: no Java runtime is installed.

## Algorithm and runtime behavior

**Thompson (intended).** Basic fragments have one start/final; union, plus,
and star use epsilon edges; ordinary concat is [94-102](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L94-L102)
but parser-selected concat is fusion ([112-118](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L112-L118)).
Operations share and mutate input states ([191-197](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L191-L197))
and assume one final state ([224-236](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L224-L236)).

**Subset conversion (intended).** Start from epsilon closure, process a work
list, and for each non-epsilon symbol apply move then closure
([44-79](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L44-L79), [86-90](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L86-L90)).
`kernel` is immediate move destinations; `cerradura` is epsilon-reachable keys.

**Evaluator (observed; not a valid NFA oracle).** `evaluar` calls start
`procesar` then immediately reads flags ([Automata 28-52](../src/Model/AutomataStructure/Automata.java#L28-L52)).
A state chooses only the last matching edge ([Estado 100-110](../src/Model/AutomataStructure/Estado.java#L100-L110));
only when no symbol edge matches does it thread per epsilon edge ([48-71](../src/Model/AutomataStructure/Estado.java#L48-L71)).
Acceptance is a mutable flag set when a final state sees empty input ([32-37](../src/Model/AutomataStructure/Estado.java#L32-L37)).

## Defects and port decisions

“Verified” below means directly proven by source flow; Java runtime reproduction
is blocked by the absent JDK.

| Classification | Finding | Required Python behavior |
|---|---|---|
| Verified static | Source explicitly says evaluator threads must be awaited ([Automata 31](../src/Model/AutomataStructure/Automata.java#L31)), but flags are checked immediately ([30-32](../src/Model/AutomataStructure/Automata.java#L30-L32)). | Synchronous set evaluation, no threads or state flags. |
| Verified static | Epsilon closure recurses without visited set ([Converter 119-126](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L119-L126)); practice contains a cycle ([Practica1 30-31](../src/Practica1/Practica1Main.java#L30-L31)). | Work-list closure with visited set. |
| Verified static | Evaluator misses competing symbol paths and epsilon alternatives ([Estado 48-71, 100-110](../src/Model/AutomataStructure/Estado.java#L48-L110)). | Advance complete epsilon-closed state sets. |
| Verified static | Alphabet views share one cache despite different epsilon policies ([Automata 132-159](../src/Model/AutomataStructure/Automata.java#L132-L159)). | Independent immutable/no-cache views. |
| Verified static | Converter marks finality inconsistently: source subset in `mover`, kernel in closure, not full subset; initial state is not marked ([93-114](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L93-L114), [44-48](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L44-L48)). | DFA final iff full represented subset intersects NFA finals. |
| Verified static | Subset constructor discards supplied kernel/closure ([Subconjunto 27-31](../src/AFDtoAFDbySubsets/Subconjunto.java#L27-L31)). | Preserve full immutable represented set. |
| Suspected runtime | `visitado`/acceptance reset can race live worker threads ([Estado 33,79](../src/Model/AutomataStructure/Estado.java#L33-L79), [Automata 40-49](../src/Model/AutomataStructure/Automata.java#L40-L49)). | Repeated calls are pure and deterministic. |

## Independent language fixtures

| Expression/model | Accept | Reject |
|---|---|---|
| `a` | `a` | `""`, `aa`, `b` |
| `a.b` | `ab` | `""`, `a`, `b`, `aba` |
| `a|b` | `a`, `b` | `""`, `ab`, `c` |
| `a*` | `""`, `a`, `aa` | `b`, `ab` |
| `a+` | `a`, `aa` | `""`, `b` |
| `a|b.c` | `a`, `bc` | `""`, `b`, `c`, `ac` |
| `(a|b).c` | `ac`, `bc` | `a`, `b`, `abc` |
| `(a.b|a*.c)+` | `c`, `ac`, `ab`, `abc` | `""`, `a`, `b`, `ca` |
| `q0 -ε-> q1 -ε-> q0`, `q1 -a-> q2(final)` | `a` | `""`, `aa`, `b`; closure terminates |
| Repeated calls on one compiled `a*` automaton | `accepts("")`, `accepts("a")`, then `accepts("")` are all `true` | `accepts("b")` is always `false`; earlier calls do not change later answers |

Python parser tests should reject `""`, `ab`, `a|`, `*a`, `(a`, and
`a)` with a documented syntax exception. That is a deliberate Python contract,
not a claim of Java compatibility for malformed input.
