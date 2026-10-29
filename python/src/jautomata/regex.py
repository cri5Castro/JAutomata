"""Strict parser for the documented JAutomata regex dialect.

The grammar is deliberately smaller than a general-purpose regex engine:
literal characters, explicit dot concatenation, union, postfix star/plus, and
parentheses. It corresponds to the precedence table in Java ShuntingYard.java,
but adds validation and deliberately rejects implicit concatenation instead of
inserting missing dots.

Whitespace and punctuation other than . | * + ( ) are literal one-character
tokens. There are no escapes, classes, wildcard, or source-level epsilon token.

Parsing is O(n) time and O(n) stack space for n Unicode characters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Union


class RegexSyntaxError(ValueError):
    """Raised when text is not in the supported explicit-concatenation grammar.

    Attributes:
        expression: Original expression supplied by the caller.
        position: Zero-based character offset at which parsing failed.

    Example:
        >>> to_postfix("a|")
        Traceback (most recent call last):
        ...
        jautomata.regex.RegexSyntaxError: expected an operand after '|' at index 2
    """

    def __init__(self, message: str, expression: str, position: int) -> None:
        self.expression = expression
        self.position = position
        super().__init__(message + " at index " + str(position))


@dataclass(frozen=True, slots=True)
class Literal:
    """One literal character leaf in a parsed expression."""

    value: str


@dataclass(frozen=True, slots=True)
class Concatenation:
    """Binary explicit concatenation node; left and right preserve source order."""

    left: "RegexNode"
    right: "RegexNode"


@dataclass(frozen=True, slots=True)
class Alternation:
    """Binary union node; left and right preserve source order."""

    left: "RegexNode"
    right: "RegexNode"


@dataclass(frozen=True, slots=True)
class KleeneStar:
    """Postfix zero-or-more closure node."""

    operand: "RegexNode"


@dataclass(frozen=True, slots=True)
class PositiveClosure:
    """Postfix one-or-more closure node."""

    operand: "RegexNode"


RegexNode = Union[Literal, Concatenation, Alternation, KleeneStar, PositiveClosure]
_RESERVED = frozenset(".|*+()")


_Token = tuple[str, int]
_BINARY_PRECEDENCE = {"|": 1, ".": 2}


def _syntax_error(message: str, expression: str, position: int) -> None:
    """Raise a positioned grammar error from the iterative parser."""
    raise RegexSyntaxError(message, expression, position)


def _postfix_tokens(expression: str) -> list[_Token]:
    """Validate expression and emit postfix tokens with source positions.

    This iterative shunting-yard variant is source-faithful to the Java parser
    but validates every token boundary. It uses explicit operator and output
    stacks, so arbitrarily deep legal groups and long left-associative chains do
    not consume Python call-stack depth.
    """
    if not expression:
        _syntax_error("expression must not be empty", expression, 0)

    output: list[_Token] = []
    operators: list[_Token] = []
    expect_operand = True

    for position, token in enumerate(expression):
        if token not in _RESERVED:
            if not expect_operand:
                _syntax_error("missing explicit '.' before operand", expression, position)
            output.append((token, position))
            expect_operand = False
            continue

        if token == "(":
            if not expect_operand:
                _syntax_error("missing explicit '.' before operand", expression, position)
            operators.append((token, position))
            continue

        if token == ")":
            if not any(operator == "(" for operator, _ in operators):
                _syntax_error("unexpected closing ')'", expression, position)
            if expect_operand:
                prior = expression[position - 1] if position else ""
                if prior == "(":
                    _syntax_error("empty group", expression, position)
                _syntax_error("expected an operand before ')'", expression, position)
            while operators and operators[-1][0] != "(":
                output.append(operators.pop())
            operators.pop()
            expect_operand = False
            continue

        if token in ("*", "+"):
            if expect_operand:
                _syntax_error(
                    "postfix operator '" + token + "' has no operand",
                    expression,
                    position,
                )
            output.append((token, position))
            continue

        # The only remaining reserved tokens are binary '.' and '|'.
        if expect_operand:
            _syntax_error("expected an operand before '" + token + "'", expression, position)
        precedence = _BINARY_PRECEDENCE[token]
        while (
            operators
            and operators[-1][0] != "("
            and _BINARY_PRECEDENCE[operators[-1][0]] >= precedence
        ):
            output.append(operators.pop())
        operators.append((token, position))
        expect_operand = True

    opening = next(
        (position for operator, position in reversed(operators) if operator == "("),
        None,
    )
    if opening is not None:
        _syntax_error(
            "missing closing ')' for '(' at index " + str(opening),
            expression,
            len(expression),
        )
    if expect_operand:
        last = expression[-1]
        _syntax_error("expected an operand after '" + last + "'", expression, len(expression))

    while operators:
        output.append(operators.pop())
    return output


def _tree_from_postfix(tokens: list[_Token], expression: str) -> RegexNode:
    """Assemble an immutable AST iteratively from validated postfix tokens."""
    nodes: list[RegexNode] = []
    for token, position in tokens:
        if token not in _RESERVED:
            nodes.append(Literal(token))
        elif token == ".":
            right = nodes.pop()
            left = nodes.pop()
            nodes.append(Concatenation(left, right))
        elif token == "|":
            right = nodes.pop()
            left = nodes.pop()
            nodes.append(Alternation(left, right))
        elif token == "*":
            nodes.append(KleeneStar(nodes.pop()))
        else:
            assert token == "+"
            nodes.append(PositiveClosure(nodes.pop()))
    if len(nodes) != 1:
        _syntax_error("invalid expression", expression, len(expression))
    return nodes[0]


def parse(expression: str) -> RegexNode:
    """Parse expression into an immutable syntax tree without recursion.

    Parameters:
        expression: Non-empty Unicode string in the documented regex grammar.

    Returns:
        An immutable tree used for diagnostics or advanced construction.

    Raises:
        TypeError: If expression is not str.
        RegexSyntaxError: If grammar, grouping, operands, or explicit dots are
            invalid.

    The parser is O(n) time and space. It intentionally rejects implicit
    concatenation rather than inserting dots.
    """
    if not isinstance(expression, str):
        raise TypeError("expression must be str")
    return _tree_from_postfix(_postfix_tokens(expression), expression)


def to_postfix(expression: str) -> Tuple[str, ...]:
    """Return validated postfix tokens without recursive tree traversal.

    This transparent counterpart of Java ShuntingYard.postfix rejects malformed
    syntax and preserves explicit-dot semantics. Postfix output is O(n) time
    and space, including deeply nested groups and long concatenation chains.
    """
    if not isinstance(expression, str):
        raise TypeError("expression must be str")
    return tuple(token for token, _ in _postfix_tokens(expression))
