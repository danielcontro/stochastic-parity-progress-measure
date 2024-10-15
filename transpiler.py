import re
from typing import Optional
from sympy import Matrix, Symbol
from reactive_module import GuardedCommand, ReactiveModule, Update
from utils import first


def parse_module(module: str) -> ReactiveModule:
    pass


def parse_guarded_command(guarded_command: str) -> GuardedCommand:
    label = re.search(r"(?<=\[)[^\]]*(?=\])", guarded_command).group()
    guard = re.search(r"(?<=\]).*(?=->)", guarded_command).group()
    command = re.search(r"(?<=->).*", guarded_command).group()

    var_id = r"[a-zA-Z]+[a-zA-Z0-9]*"
    number = r"[0-9]+(?:\.[0-9]+)?"
    monomial = r"(?:%s \* )?%s" % (number, var_id)
    expression = r"-?(?:%s (?:\+|\-))* (?:%s|%s)" % (
        monomial,
        monomial,
        number,
    )
    min_function = r"min\(%s,%s\)" % (expression, expression)
    var_update = r"\(%s' = (?:%s|%s)\)" % (var_id, min_function, expression)
    prob_update = r"(?:(?:%s|%s):(?:%s & )*%s)" % (
        var_id,
        number,
        var_update,
        var_update,
    )
    print(command)
    regex = re.compile(expression)
    print(regex)
    print(re.findall(regex, command))
    updates = re.finditer(re.compile(prob_update), command)
    for up in updates:
        print("match")
        print(up.group())

    pass


def parse_update(vars: list[Symbol], update: str) -> Update:
    functions = list(
        map(lambda s: s[1:-1].split("="), "".join(update.split()).split("&"))
    )
    updates = {
        Symbol(k[:-1]): parse_eq(vars, v) for update in functions for k, v in update
    }

    a = b = Matrix()
    for i, var in enumerate(vars):
        a.col_join(
            updates.get(var, Matrix([[0.0] * i + [1.0] + [0.0] * (len(vars) - i - 1)]))
        )
        b.col_join(updates.get(var, Matrix([[0.0]])))

    return a, b


def parse_eq(vars: list[Symbol], eq: str) -> Update:
    if eq[0:3] == "min":
        # TODO: understand how to parse min equations
        equations = eq[3:].strip("()").split(",")
        lhs = parse_eq(vars, equations[0])
        rhs = parse_eq(vars, equations[1])
        pass

    monomials = eq.split("+")
    coefficients = {k: v for k, v in map(lambda m: parse_monomial(vars, m), monomials)}

    return Matrix([[coefficients.get(var, 0.0) for var in vars]]), Matrix(
        [[coefficients.get(None, 0.0)]]
    )


def parse_monomial(vars: list[Symbol], monomial: str) -> tuple[Optional[Symbol], float]:
    var = first(lambda v: v.name in monomial, vars)
    if var is None:
        # If the monomial does not contain any variable, it is a constant
        return None, float(monomial)

    match monomial.split("*"):
        case [coeff, var.name]:
            return var, float(coeff)
        case [var.name]:
            return var, 1.0
        case _:
            raise ValueError(f"Invalid monomial: {monomial}")
