import math
import sys

HELP_MESSAGE = """Стековая машина для вычисления выражений в постфиксной нотации (RPN).

Использование:
    python main.py "<выражение>"
    python main.py -h | --help

Поддерживаемые операции:
    +   сложение (x + y)
    -   вычитание (x - y)
    *   умножение (x * y)
    /   деление (x / y)
    ~   специальный оператор:
        - если x != 0 и y != 0: вычисляет |x - y| и кладет результат в стек
        - если x == 0 или y == 0: вычисляет сумму всех оставшихся элементов в стеке,
          возводит её в квадрат и кладет результат обратно в стек

Примеры:
    python main.py "3 0 4 ~ 2 ~"
    python main.py "2 2 + 4 - 4 ~ 2 3 * +"
"""


def is_number(token: str) -> bool:
    try:
        return math.isfinite(float(token))
    except ValueError:
        return False


def normalize_number(value: int | float) -> int | float:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def parse_number(token: str) -> int | float:
    return normalize_number(float(token))


def postfix_sum(x: int | float, y: int | float) -> int | float:
    return normalize_number(x + y)


def postfix_sub(x: int | float, y: int | float) -> int | float:
    return normalize_number(x - y)


def postfix_mult(x: int | float, y: int | float) -> int | float:
    return normalize_number(x * y)


def postfix_div(x: int | float, y: int | float) -> int | float:
    if y == 0:
        raise ZeroDivisionError("Деление на ноль невозможно.")
    return normalize_number(x / y)


def postfix_tilde(stack: list[int | float]) -> list[int | float]:
    if len(stack) < 2:
        raise ValueError("Недостаточно операндов в стеке для выполнения операции '~'.")
    y = stack.pop()
    x = stack.pop()

    if x == 0 or y == 0:
        return [normalize_number(sum(stack) ** 2)]

    stack.append(normalize_number(abs(x - y)))
    return stack


OPERATORS = {
    "+": postfix_sum,
    "-": postfix_sub,
    "*": postfix_mult,
    "/": postfix_div,
}


def format_value(val: int | float) -> str:
    return str(normalize_number(val))


def evaluate(expression: str, verbose: bool = True) -> int | float:
    tokens = expression.strip().split()
    if not tokens:
        raise ValueError("Выражение не должно быть пустым.")

    invalid = [t for t in tokens if not (is_number(t) or t in OPERATORS or t == "~")]
    if invalid:
        raise ValueError(f"Неизвестные токены в выражении: {', '.join(invalid)}")

    stack: list[int | float] = []

    for step, token in enumerate(tokens, 1):
        if token in OPERATORS:
            if len(stack) < 2:
                raise ValueError(
                    f"Недостаточно операндов для операции '{token}'. В стеке: {stack}"
                )
            y = stack.pop()
            x = stack.pop()
            result = OPERATORS[token](x, y)
            stack.append(result)
        elif token == "~":
            stack = postfix_tilde(stack)
        else:
            stack.append(parse_number(token))

        if verbose:
            print(f"Шаг {step:2d}: токен '{token}' -> стек: {stack}")

    if len(stack) != 1:
        raise ValueError(
            f"После вычисления в стеке осталось некорректное число элементов: {stack}"
        )

    return stack[0]


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print(
            "Подсказка: передайте постфиксное выражение в аргументах командной строки.\n"
            "Пример: python main.py \"3 0 4 ~ 2 ~\"\n"
            "Для вызова справки используйте: python main.py --help"
        )
        return 1

    if argv[0] in ("-h", "--help"):
        print(HELP_MESSAGE.strip())
        return 0

    raw_expression = " ".join(argv)
    try:
        result = evaluate(raw_expression, verbose=True)
        print(f"\n{raw_expression} = {format_value(result)}")
        return 0
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
