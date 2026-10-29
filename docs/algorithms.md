# Algorithms and Java correspondence

For worked traces before the formal comparison, follow
[Regex syntax](learn/regex-syntax.md), [Thompson construction](learn/thompson.md),
[Epsilon closure](learn/epsilon-closure.md), and
[Subset construction](learn/subset-construction.md).

## Regex parsing and Thompson construction

The Java parser records precedence 3 for closure, 2 for concatenation, and 1
for union in [ShuntingYard.java](../src/ExpresionRegularToAFN/ShuntingYard.java#L13-L30).
Its comment at [line 53](../src/ExpresionRegularToAFN/ShuntingYard.java#L53)
suggests inserting dots, but active code does not. Python deliberately requires
explicit dots and validates missing concatenation.

Java ConstructorDeAutomatas says it uses Thompson construction
([lines 9-14](../src/ExpresionRegularToAFN/ConstructorDeAutomatas.java#L9-L14)).
Python keeps the language construction but allocates fresh immutable states and
uses epsilon-link concatenation. The iterative postfix parser/compiler avoids
recursion depth dependence while retaining O(n) time and space.

## Epsilon-NFA simulation

Java Automata.evaluar immediately checks result flags after processing
([lines 28-52](../src/Model/AutomataStructure/Automata.java#L28-L52)); the
comment at [line 31](../src/Model/AutomataStructure/Automata.java#L31) identifies
the thread-wait issue. Estado.procesar selects one matching transition and only
branches epsilon paths in another case ([lines 48-71](../src/Model/AutomataStructure/Estado.java#L48-L71),
[100-110](../src/Model/AutomataStructure/Estado.java#L100-L110)).

Python instead keeps an immutable set of active states. Epsilon closure is an
iterative work list with a visited set, then each character advances all
matching edges before another closure. This recognizes nondeterministic branches
and terminates for cycles. Per acceptance call, adjacency setup is O(T); the
remaining cost is proportional to reached states and edges for each character.

## Subset conversion

The Java converter describes processing subsets and creating transitions
([lines 35-79](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L35-L79)) but its
recursive epsilon closure has no visited set
([119-126](../src/AFDtoAFDbySubsets/ContructorAFNtoAFD.java#L119-L126)).
Python represents each DFA state as a full epsilon-closed NFA subset, marks it
final if it intersects NFA finals, and processes sorted source-alphabet symbols
in BFS order.

At most 2^N subsets are reachable for N NFA states. The produced DFA is complete
over the original alphabet; a reachable empty subset is an explicit sink. This
is deterministic construction, not DFA minimization.
