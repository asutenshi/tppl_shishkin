import pytest
from main import (
    evaluate,
    format_value,
    is_number,
    main,
    normalize_number,
    parse_number,
    postfix_div,
    postfix_mult,
    postfix_sub,
    postfix_sum,
    postfix_tilde,
)


class TestHelpers:
    @pytest.mark.parametrize(
        "token, expected",
        [
            ("0", True),
            ("42", True),
            ("-15", True),
            ("3.14", True),
            ("-0.5", True),
            ("abc", False),
            ("nan", False),
            ("inf", False),
            ("-infinity", False),
            ("", False),
        ],
    )
    def test_is_number(self, token, expected):
        assert is_number(token) == expected

    @pytest.mark.parametrize(
        "value, expected, expected_type",
        [
            (5.0, 5, int),
            (5.25, 5.25, float),
            (10, 10, int),
            (-3.0, -3, int),
            (-3.14, -3.14, float),
        ],
    )
    def test_normalize_number(self, value, expected, expected_type):
        res = normalize_number(value)
        assert res == expected
        assert isinstance(res, expected_type)

    @pytest.mark.parametrize(
        "token, expected",
        [
            ("12", 12),
            ("3.5", 3.5),
            ("-42", -42),
            ("0.0", 0),
        ],
    )
    def test_parse_number(self, token, expected):
        assert parse_number(token) == expected

    @pytest.mark.parametrize(
        "val, expected",
        [
            (7.0, "7"),
            (7.5, "7.5"),
            (0, "0"),
            (-4.0, "-4"),
        ],
    )
    def test_format_value(self, val, expected):
        assert format_value(val) == expected


class TestOperators:
    @pytest.mark.parametrize(
        "op_func, x, y, expected",
        [
            (postfix_sum, 2, 3, 5),
            (postfix_sum, 2.5, 3.5, 6),
            (postfix_sum, -5, 3, -2),
            (postfix_sub, 10, 4, 6),
            (postfix_sub, 4, 10, -6),
            (postfix_sub, 5.5, 0.5, 5),
            (postfix_mult, 3, 4, 12),
            (postfix_mult, 2.5, 2, 5),
            (postfix_mult, -2, 3, -6),
            (postfix_div, 10, 2, 5),
            (postfix_div, 7, 2, 3.5),
        ],
    )
    def test_binary_operations(self, op_func, x, y, expected):
        assert op_func(x, y) == expected

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError, match="Деление на ноль невозможно"):
            postfix_div(5, 0)

    @pytest.mark.parametrize(
        "initial_stack, expected_stack",
        [
            ([10, 3, 8], [10, 5]),
            ([2, 5], [3]),
            ([3, 0, 4], [9]),
            ([0, 4], [0]),
            ([2, 1, 5, 0], [9]),
            ([0, 0], [0]),
        ],
        ids=[
            "diff_positive",
            "diff_order_abs",
            "zero_first_operand_with_remaining",
            "zero_first_operand_empty_remaining",
            "zero_second_operand_with_remaining",
            "both_zeros_empty_remaining",
        ],
    )
    def test_tilde_valid(self, initial_stack, expected_stack):
        assert postfix_tilde(initial_stack) == expected_stack

    @pytest.mark.parametrize(
        "stack",
        [[], [1]],
        ids=["empty_stack", "single_element"],
    )
    def test_tilde_insufficient_operands(self, stack):
        with pytest.raises(ValueError, match="Недостаточно операндов"):
            postfix_tilde(stack)


class TestEvaluate:
    @pytest.mark.parametrize(
        "expression, expected",
        [
            ("3 0 4 ~ 2 ~", 7),
            ("2 2 + 4 - 4 ~ 2 3 * +", 6),
            ("5 1 2 + 4 * + 3 -", 14),
            ("15 3 / 2 +", 7),
            ("4 2 / 2 /", 1),
            ("10 2 - 3 -", 5),
            ("2.5 1.5 +", 4),
            ("-5 3 +", -2),
        ],
        ids=[
            "example_1_from_task",
            "example_2_from_task",
            "complex_arithmetic",
            "division_and_addition",
            "sequential_divisions",
            "sequential_subtractions",
            "float_result_normalized_to_int",
            "negative_numbers",
        ],
    )
    def test_evaluate_valid(self, expression, expected):
        assert evaluate(expression, verbose=False) == expected

    @pytest.mark.parametrize(
        "expression, exc_type, match",
        [
            ("   ", ValueError, "не должно быть пустым"),
            ("2 3 & +", ValueError, "Неизвестные токены"),
            ("2 +", ValueError, "Недостаточно операндов"),
            ("~", ValueError, "Недостаточно операндов"),
            ("1 2 3 +", ValueError, "осталось некорректное число элементов"),
            ("10 0 /", ZeroDivisionError, "Деление на ноль невозможно"),
        ],
        ids=[
            "empty_expression",
            "unknown_operator",
            "binary_op_missing_operands",
            "tilde_missing_operands",
            "too_many_operands_remaining",
            "division_by_zero",
        ],
    )
    def test_evaluate_errors(self, expression, exc_type, match):
        with pytest.raises(exc_type, match=match):
            evaluate(expression, verbose=False)

    def test_verbose_output(self, capsys):
        res = evaluate("2 3 +", verbose=True)
        assert res == 5
        captured = capsys.readouterr()
        assert "Шаг  1: токен '2' -> стек: [2]" in captured.out
        assert "Шаг  2: токен '3' -> стек: [2, 3]" in captured.out
        assert "Шаг  3: токен '+' -> стек: [5]" in captured.out


class TestMainCli:
    @pytest.mark.parametrize(
        "args, expected_code, expected_output",
        [
            ([], 1, "Подсказка:"),
            (["-h"], 0, "Стековая машина"),
            (["--help"], 0, "Стековая машина"),
            (["3 0 4 ~ 2 ~"], 0, "3 0 4 ~ 2 ~ = 7"),
            (["3", "0", "4", "~", "2", "~"], 0, "3 0 4 ~ 2 ~ = 7"),
            (["10 0 /"], 1, "Ошибка: Деление на ноль невозможно."),
            (["invalid_token"], 1, "Ошибка: Неизвестные токены"),
        ],
        ids=[
            "no_args",
            "short_help",
            "long_help",
            "single_string_arg",
            "multiple_argv_tokens",
            "division_by_zero",
            "invalid_token",
        ],
    )
    def test_main_cli_args(self, args, expected_code, expected_output, capsys):
        code = main(args)
        assert code == expected_code
        captured = capsys.readouterr()
        assert expected_output in (captured.out + captured.err)

    def test_main_default_sys_argv(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["main.py", "2", "3", "+"])
        code = main()
        assert code == 0
        captured = capsys.readouterr()
        assert "2 3 + = 5" in captured.out

    def test_main_module_run(self, monkeypatch):
        from pathlib import Path
        import runpy
        import sys
        import main

        main_path = str(Path(main.__file__).resolve())
        monkeypatch.setattr(sys, "argv", ["main.py", "2", "3", "+"])
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_path(main_path, run_name="__main__")
        assert exc_info.value.code == 0
