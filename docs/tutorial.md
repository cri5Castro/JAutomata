# Tutorial: regex to NFA to DFA

This tutorial uses the delivered public API. Run snippets from the repository
root after uv sync --project python. For an interactive packaged session, start
uv run --project python python rather than the system Python executable.

## Compile and recognize

~~~python
from jautomata import accepts, compile_regex, to_dfa

expression = "(a.b|a*.c)+"
nfa = compile_regex(expression)
dfa = to_dfa(nfa)

cases = {
    "": False,
    "ab": True,
    "c": True,
    "ac": True,
    "abc": True,
    "a": False,
    "b": False,
    "ca": False,
}
for text, expected in cases.items():
    assert accepts(nfa, text) is expected
    assert accepts(dfa, text) is expected
~~~

The dot is required: a.b means a followed by b. The expression accepts one or
more blocks that are either ab or zero-or-more a followed by c. Empty input is
rejected because the outer plus requires at least one block, even though a*
inside one alternative can be empty.

## Inspect epsilon closure

~~~python
from jautomata import epsilon_closure

start_closure = epsilon_closure(nfa, {nfa.start_state})
assert nfa.start_state in start_closure
~~~

None represents internal epsilon in transitions; it is not a string accepted
from input and it is not present in nfa.alphabet.

## Complete DFA behavior

to_dfa creates deterministic transitions for every state and every NFA alphabet
symbol. Missing moves lead to a reachable empty-subset sink. That policy makes
accepts(dfa, text) agree with accepts(nfa, text) for both in-alphabet and
rejecting paths.

For a command-line version of the tutorial, run:

~~~sh
uv run --project python python python/examples/regex_pipeline.py
~~~
