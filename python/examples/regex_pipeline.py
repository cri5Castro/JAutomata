"""Run a complete regex -> NFA -> DFA acceptance demonstration.

Run from the repository root:

    uv run --project python python python/examples/regex_pipeline.py
"""

from jautomata import accepts, compile_regex, to_dfa


def main() -> None:
    """Compile one documented expression and print matching NFA/DFA outcomes."""
    expression = "(a.b|a*.c)+"
    nfa = compile_regex(expression)
    dfa = to_dfa(nfa)
    cases = ("", "ab", "c", "ac", "abc", "a", "b", "ca")
    print("expression:", expression)
    for text in cases:
        nfa_result = accepts(nfa, text)
        dfa_result = accepts(dfa, text)
        assert nfa_result == dfa_result
        print(repr(text) + ": NFA=" + str(nfa_result) + " DFA=" + str(dfa_result))


if __name__ == "__main__":
    main()
