"""Public APIs for documented regex compilation and automata recognition.

Only completed operations are exported: strict regex compilation, cycle-safe
epsilon closure, pure NFA/DFA acceptance, and deterministic subset conversion.
"""

from .regex import RegexSyntaxError
from .simulation import accepts, epsilon_closure
from .subsets import to_dfa
from .thompson import compile_regex

__version__ = "0.1.0"

__all__ = [
    "RegexSyntaxError",
    "accepts",
    "compile_regex",
    "epsilon_closure",
    "to_dfa",
]
