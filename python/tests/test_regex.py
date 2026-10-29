"""Parser tests for supported grammar and rejected malformed input."""

import unittest

from jautomata.regex import RegexSyntaxError, parse, to_postfix


class RegexParserTests(unittest.TestCase):
    def test_precedence_grouping_and_left_associativity(self) -> None:
        self.assertEqual(to_postfix("a|b.c"), ("a", "b", "c", ".", "|"))
        self.assertEqual(to_postfix("(a|b).c"), ("a", "b", "|", "c", "."))
        self.assertEqual(to_postfix("a.b.c"), ("a", "b", ".", "c", "."))

    def test_postfix_chains_are_left_to_right(self) -> None:
        self.assertEqual(to_postfix("a*+"), ("a", "*", "+"))
        self.assertEqual(to_postfix("(a*)+"), ("a", "*", "+"))

    def test_unicode_whitespace_and_other_punctuation_are_literals(self) -> None:
        self.assertEqual(to_postfix("😀. "), ("😀", " ", "."))
        self.assertEqual(to_postfix("?.!"), ("?", "!", "."))

    def test_malformed_expressions_raise_positioned_syntax_error(self) -> None:
        for expression in ("", "ab", "a|", "*a", "(a", "a)", "()", "a..b"):
            with self.subTest(expression=expression):
                with self.assertRaises(RegexSyntaxError) as raised:
                    to_postfix(expression)
                self.assertIsInstance(raised.exception, ValueError)
                self.assertGreaterEqual(raised.exception.position, 0)

    def test_non_string_expression_is_type_error(self) -> None:
        with self.assertRaises(TypeError):
            to_postfix(None)  # type: ignore[arg-type]

    def test_long_concatenation_and_deep_groups_use_no_python_recursion(self) -> None:
        long_concatenation = ".".join(["a"] * 1500)
        deeply_grouped = "(" * 300 + "a" + ")" * 300
        self.assertEqual(len(to_postfix(long_concatenation)), 2999)
        self.assertEqual(to_postfix(deeply_grouped), ("a",))
        self.assertIsNotNone(parse(long_concatenation))
        self.assertIsNotNone(parse(deeply_grouped))


if __name__ == "__main__":
    unittest.main()
