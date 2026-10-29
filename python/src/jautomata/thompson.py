"""Thompson construction from parsed JAutomata regular expressions.

compile_regex builds a fresh immutable epsilon-NFA on every call. It follows
the intended Java ConstructorDeAutomatas operations while using epsilon-link
concatenation rather than mutable state fusion. This makes fragment ownership
explicit and preserves value-model invariants.

Construction consumes each validated postfix token once, so time and space are
O(n) for n tokens. State allocation is local to one compilation; no call can
share mutable construction state with another.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import Automaton, Transition
from .regex import to_postfix


@dataclass(slots=True)
class _Fragment:
    """One partial NFA with exactly one entry and one exit state."""

    start: int
    end: int


@dataclass(slots=True)
class _Builder:
    """Per-compilation state allocator and temporary edge collector."""

    next_state: int = 0
    states: set[int] = field(default_factory=set)
    transitions: set[Transition] = field(default_factory=set)

    def state(self) -> int:
        """Allocate and register one fresh state id."""
        state = self.next_state
        self.next_state += 1
        self.states.add(state)
        return state

    def epsilon(self, source: int, target: int) -> None:
        """Add one internal epsilon edge."""
        self.transitions.add(Transition(source, None, target))

    def build_postfix(self, tokens: tuple[str, ...]) -> _Fragment:
        """Translate validated postfix tokens with a fragment stack.

        Each literal creates a two-state fragment. Operators pop the needed
        completed fragments and push one replacement fragment. This is the
        iterative counterpart of recursive Thompson construction: it has O(n)
        time and space but does not depend on expression nesting depth.
        """
        fragments: list[_Fragment] = []
        for token in tokens:
            if token not in (".", "|", "*", "+"):
                start = self.state()
                end = self.state()
                self.transitions.add(Transition(start, token, end))
                fragments.append(_Fragment(start, end))
                continue

            if token == ".":
                right = fragments.pop()
                left = fragments.pop()
                self.epsilon(left.end, right.start)
                fragments.append(_Fragment(left.start, right.end))
                continue

            if token == "|":
                right = fragments.pop()
                left = fragments.pop()
                start = self.state()
                end = self.state()
                self.epsilon(start, left.start)
                self.epsilon(start, right.start)
                self.epsilon(left.end, end)
                self.epsilon(right.end, end)
                fragments.append(_Fragment(start, end))
                continue

            operand = fragments.pop()
            start = self.state()
            end = self.state()
            self.epsilon(start, operand.start)
            if token == "*":
                self.epsilon(start, end)
            self.epsilon(operand.end, operand.start)
            self.epsilon(operand.end, end)
            fragments.append(_Fragment(start, end))

        assert len(fragments) == 1
        return fragments[0]

def compile_regex(expression: str) -> Automaton:
    """Compile expression into a fresh immutable Thompson epsilon-NFA.

    Parameters:
        expression: Explicit-concatenation regex accepted by regex.parse.

    Returns:
        Automaton with integer IDs, exactly one final state, and None-labelled
        epsilon edges. The graph is immutable and contains no evaluation flags.

    Raises:
        TypeError: If expression is not str.
        RegexSyntaxError: If expression is malformed.

    Example:
        >>> automaton = compile_regex("a.b*")
        >>> automaton.alphabet == frozenset({"a", "b"})
        True

    Correspondence:
        This is the value-oriented counterpart of Java
        ExpresionRegularToAFN/ConstructorDeAutomatas.java. Union/star/plus use
        the standard fresh-entry/fresh-exit Thompson topology; concatenation
        uses the Java class's available epsilon-link variant instead of its
        mutable fusion variant.
    """
    builder = _Builder()
    fragment = builder.build_postfix(to_postfix(expression))
    return Automaton(
        states=builder.states,
        start_state=fragment.start,
        final_states={fragment.end},
        transitions=builder.transitions,
    )
