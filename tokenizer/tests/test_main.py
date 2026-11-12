import runpy
import sys
from pathlib import Path

import pytest
import main
from main import Lexer, LexicalException

MAIN_PY = Path(__file__).resolve().parent.parent / "main.py"

class TestLexer:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("x = y * 2 + z * 3", [
                ("IDENT", "x", 1, 1),
                ("OP", "=", 1, 3),
                ("IDENT", "y", 1, 5),
                ("OP", "*", 1, 7),
                ("INT", "2", 1, 9),
                ("OP", "+", 1, 11),
                ("IDENT", "z", 1, 13),
                ("OP", "*", 1, 15),
                ("INT", "3", 1, 17)
            ]),
            ('def f(a, b) {\n  return a >= b; # cmp\n}', [
                ("KEYWORD", "def", 1, 1),
                ("IDENT", "f", 1, 5),
                ("SEP", "(", 1, 6),
                ("IDENT", "a", 1, 7),
                ("SEP", ",", 1, 8),
                ("IDENT", "b", 1, 10),
                ("SEP", ")", 1, 11),
                ("SEP", "{", 1, 13),
                ("KEYWORD", "return", 2, 3),
                ("IDENT", "a", 2, 10),
                ("OP", ">=", 2, 12),
                ("IDENT", "b", 2, 15),
                ("SEP", ";", 2, 16),
                ("SEP", "}", 3, 1),
            ])
        ]
    )
    def test_lexer(self, text, expected):
        lexer = Lexer(text)
        tokens = lexer.tokenize()

        assert tokens == expected


    @pytest.mark.parametrize(
        "text, expected",
        [
            ("3.14", [("FLOAT", "3.14", 1, 1)]),
            ("1.",   [("FLOAT", "1.",   1, 1)]),
            ("42",   [("INT",   "42",   1, 1)]),
        ]
    )
    def test_numbers(self, text, expected):
        lexer =  Lexer(text)
        tokens = lexer.tokenize()
        
        assert tokens == expected


    @pytest.mark.parametrize(
        "text, expected",
        [
            ("a\n  b\n\tc", [
                ("IDENT", "a", 1, 1),
                ("IDENT", "b", 2, 3),
                ("IDENT", "c", 3, 2),
            ]),
            ("x\n\n  y", [
                ("IDENT", "x", 1, 1),
                ("IDENT", "y", 3, 3),
            ]),
            ("x = 1\ny = 2", [
                ("IDENT", "x", 1, 1),
                ("OP", "=", 1, 3),
                ("INT", "1", 1, 5),
                ("IDENT", "y", 2, 1),
                ("OP", "=", 2, 3),
                ("INT", "2", 2, 5),
            ]),
        ]
    )
    def test_new_line(self, text, expected):
        lexer =  Lexer(text)
        tokens = lexer.tokenize()       

        assert tokens == expected



    @pytest.mark.parametrize(
        "text",
        [
            "a @ b",
        ]
    )
    def test_unexpected_token(self, text):
        lexer =  Lexer(text)

        with pytest.raises(LexicalException) as ex_info:
            lexer.tokenize()

        ex = ex_info.value
        assert ex.line == 1
        assert ex.col == 3
        assert "unexpected character" in ex.text


    @pytest.mark.parametrize("keyword", ["if", "else", "while", "return", "for", "def"])
    def test_keywords(self, keyword):
        tokens = Lexer(keyword).tokenize()

        assert tokens == [("KEYWORD", keyword, 1, 1)]


    @pytest.mark.parametrize(
        "text",
        ["iff", "define", "If", "_if", "x1", "_a_1", "returns"]
    )
    def test_identifiers_are_not_keywords(self, text):
        tokens = Lexer(text).tokenize()

        assert tokens == [("IDENT", text, 1, 1)]


    @pytest.mark.parametrize(
        "text, expected",
        [
            ("+", [("OP", "+", 1, 1)]),
            ("-", [("OP", "-", 1, 1)]),
            ("*", [("OP", "*", 1, 1)]),
            ("/", [("OP", "/", 1, 1)]),
            ("=", [("OP", "=", 1, 1)]),
            ("<", [("OP", "<", 1, 1)]),
            (">", [("OP", ">", 1, 1)]),
            ("==", [("OP", "==", 1, 1)]),
            ("<=", [("OP", "<=", 1, 1)]),
            (">=", [("OP", ">=", 1, 1)]),
            ("= =", [("OP", "=", 1, 1), ("OP", "=", 1, 3)]),
            ("a<=b", [
                ("IDENT", "a", 1, 1),
                ("OP", "<=", 1, 2),
                ("IDENT", "b", 1, 4),
            ]),
        ]
    )
    def test_operators(self, text, expected):
        assert Lexer(text).tokenize() == expected


    def test_separators(self):
        tokens = Lexer("(){},;").tokenize()

        assert tokens == [
            ("SEP", "(", 1, 1),
            ("SEP", ")", 1, 2),
            ("SEP", "{", 1, 3),
            ("SEP", "}", 1, 4),
            ("SEP", ",", 1, 5),
            ("SEP", ";", 1, 6),
        ]


    @pytest.mark.parametrize(
        "text, expected",
        [
            ("# only comment", []),
            ("x # comment", [("IDENT", "x", 1, 1)]),
            ("x # comment\ny", [("IDENT", "x", 1, 1), ("IDENT", "y", 2, 1)]),
            ("# a\n# b\nz", [("IDENT", "z", 3, 1)]),
        ]
    )
    def test_comments(self, text, expected):
        assert Lexer(text).tokenize() == expected


    @pytest.mark.parametrize(
        "text, expected",
        [
            ("", []),
            ("   \t \n  ", []),
            ("  \t x", [("IDENT", "x", 1, 5)]),
        ]
    )
    def test_whitespace(self, text, expected):
        assert Lexer(text).tokenize() == expected


    @pytest.mark.parametrize(
        "text, expected",
        [
            ('"abc"', [("STRING", '"abc"', 1, 1)]),
            ('""', [("STRING", '""', 1, 1)]),
            ('"a # b ( 1"', [("STRING", '"a # b ( 1"', 1, 1)]),
            ('x = "hi"', [
                ("IDENT", "x", 1, 1),
                ("OP", "=", 1, 3),
                ("STRING", '"hi"', 1, 5),
            ]),
        ]
    )
    def test_strings(self, text, expected):
        assert Lexer(text).tokenize() == expected


    @pytest.mark.parametrize(
        "text, line, col",
        [
            ('"abc', 1, 1),
            ('x = "abc', 1, 5),
            ('a\n  "abc\ndef', 2, 3),
        ]
    )
    def test_unclosed_string(self, text, line, col):
        with pytest.raises(LexicalException) as ex_info:
            Lexer(text).tokenize()

        assert ex_info.value.line == line
        assert ex_info.value.col == col


class TestMain:
    @staticmethod
    def run(monkeypatch, *args):
        monkeypatch.setattr(sys, "argv", ["main.py", *args])
        main.main()

    def test_prints_tokens(self, monkeypatch, capsys, tmp_path):
        src = tmp_path / "input.txt"
        src.write_text("x = 1\n", encoding="utf-8")

        self.run(monkeypatch, str(src))

        out = capsys.readouterr()
        assert out.out == "(IDENT, x, 1:1)\n(OP, =, 1:3)\n(INT, 1, 1:5)\n"
        assert out.err == ""

    def test_lexical_error(self, monkeypatch, capsys, tmp_path):
        src = tmp_path / "input.txt"
        src.write_text("a @ b", encoding="utf-8")

        with pytest.raises(SystemExit) as exit_info:
            self.run(monkeypatch, str(src))

        out = capsys.readouterr()
        assert exit_info.value.code == 1
        assert out.out == ""
        assert out.err == f"{src}:1:3: lexical: unexpected character '@'\n"

    def test_no_arguments(self, monkeypatch, capsys):
        with pytest.raises(SystemExit) as exit_info:
            self.run(monkeypatch)

        assert exit_info.value.code == 2
        assert main.HELP_MESSAGE in capsys.readouterr().err

    def test_too_many_arguments(self, monkeypatch, capsys):
        with pytest.raises(SystemExit) as exit_info:
            self.run(monkeypatch, "a.txt", "b.txt")

        assert exit_info.value.code == 2
        assert capsys.readouterr().err == main.USAGE_MESSAGE + "\n"

    def test_missing_file(self, monkeypatch, capsys, tmp_path):
        with pytest.raises(SystemExit) as exit_info:
            self.run(monkeypatch, str(tmp_path / "nope.txt"))

        assert exit_info.value.code == 1
        assert "nope.txt" in capsys.readouterr().err

    def test_not_utf8_file(self, monkeypatch, capsys, tmp_path):
        src = tmp_path / "bin.txt"
        src.write_bytes(b"\xff\xfe")

        with pytest.raises(SystemExit) as exit_info:
            self.run(monkeypatch, str(src))

        assert exit_info.value.code == 1
        assert capsys.readouterr().err != ""

    def test_run_as_script(self, monkeypatch, capsys, tmp_path):
        src = tmp_path / "input.txt"
        src.write_text("if", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["main.py", str(src)])

        runpy.run_path(str(MAIN_PY), run_name="__main__")

        assert capsys.readouterr().out == "(KEYWORD, if, 1:1)\n"
