from collections.abc import Iterable
from functools import reduce
from itertools import chain
import operator
from typing import Self, TypeVar

from sympy import (
    And,
    Eq,
    GreaterThan,
    LessThan,
    Matrix,
    Or,
    StrictGreaterThan,
    StrictLessThan,
    Symbol,
    Number,
    Add,
    Expr,
    Mul,
    Pow,
    linear_eq_to_matrix,
)
from sympy.core.relational import Relational
from sympy.logic.boolalg import Boolean, BooleanFalse
from z3 import ArithRef, BoolRef, Real, Sqrt
import z3

SPLinearFunction = tuple[Matrix, Matrix]
SPStateBasedLinearFunction = dict[int, SPLinearFunction]

Mat = list[list[ArithRef | float]]
LinearFunction = tuple[Mat, Mat]
StateBasedLinearFunction = dict[int, LinearFunction]

VarMap = dict[str, ArithRef]

_VAR_MAP: VarMap = {}


def split_disjunctions(e: BoolRef):
    return e.children() if e.decl().name() == "or" else [e]


def parse_matrix(m: Matrix) -> Mat:
    return [
        [to_z3_expr(m[row, column]) for column in range(m.shape[1])]
        for row in range(m.shape[0])
    ]


def update_var_map(sympy_vars: Iterable[Symbol] = []) -> VarMap:
    for var in sympy_vars:
        if var.name not in _VAR_MAP:
            _VAR_MAP[var.name] = Real(var.name)
    return _VAR_MAP


def get_z3_var_map() -> VarMap:
    return _VAR_MAP


def get_z3_var(var: Symbol) -> ArithRef:
    return get_z3_var_map().get(var.name)


def to_z3_expr(exp: Expr) -> ArithRef | float:
    "convert a sympy expression to a z3 expression. This returns (z3_vars, z3_expression)"

    result_exp = _sympy_to_z3_rec(exp)

    return result_exp


def _sympy_to_z3_rec(e: Expr):
    "recursive call for sympy_to_z3()"

    if not isinstance(e, Expr):
        raise RuntimeError("Expected sympy Expr: " + repr(e))

    if isinstance(e, Symbol):
        z3_var = get_z3_var(e)

        if z3_var is None:
            raise RuntimeError(f"No var was corresponds to symbol '{e}'")
        return z3_var

    elif isinstance(e, Number):
        return float(e)

    elif isinstance(e, Mul):
        return reduce(operator.mul, [_sympy_to_z3_rec(child) for child in e.args], 1.0)

    elif isinstance(e, Add):
        return sum([_sympy_to_z3_rec(child) for child in e.args], 0.0)

    elif isinstance(e, Pow):
        exponent = _sympy_to_z3_rec(e.args[1])

        if exponent == 0.5:
            return Sqrt(_sympy_to_z3_rec(e.args[0]))

        return _sympy_to_z3_rec(e.args[0]) ** exponent

    raise RuntimeError(
        f"Type '{type(e)}' is not yet implemented for convertion to z3."
        + f"Subexpression was '{e}'."
    )


def parse_DNF(dnf: Boolean) -> list[Boolean]:
    if isinstance(dnf, Or):
        assert all(isinstance(x, Boolean) for x in dnf.args)
        return list(dnf.args)

    return [dnf]


def parse_conjunct(conjunct: Boolean) -> list[Relational]:
    """
    Extrapolates a list of constraints from a conjunct
    """
    if isinstance(conjunct, And):
        conjs = list(conjunct.args)
        assert all(isinstance(x, Boolean) for x in conjs)
        return conjs

    return [conjunct]


def _parse_constr(conjunct: Relational) -> BoolRef:
    match conjunct.rel_op:
        case "<":
            return to_z3_expr(conjunct.lhs) < 0
        case "<=":
            return to_z3_expr(conjunct.lhs) <= 0
        case ">":
            return to_z3_expr(conjunct.lhs) > 0
        case ">=":
            return to_z3_expr(conjunct.lhs) >= 0
        case "==":
            return to_z3_expr(conjunct.lhs) == 0
        case _:
            raise RuntimeError("Invalid ordering")


def to_z3_dnf(dnf: Boolean) -> list[BoolRef]:
    conjs = parse_DNF(dnf)
    constraints = list(map(parse_conjunct, conjs))
    return z3.Or(list(map(lambda x: z3.And(list(map(_parse_constr, x))), constraints)))


def z3_real_to_float(z3_real: ArithRef) -> float:
    fract = z3_real.as_fraction()
    return float(fract.numerator) / float(fract.denominator)


def parse_constraint(constraint: Relational) -> list[Expr]:
    """
    `constraint` of the form AX + b ~ 0
    with:
    - A: R^(1xn)
    - X: R^n
    - b: R
    - ~ in {<, <=, >=, >, ==}
    """
    if isinstance(constraint, BooleanFalse):
        return [1]
    assert isinstance(constraint.lhs, Expr)
    ordering = constraint.rel_op
    match ordering:
        case "<":
            return [constraint.lhs]
        case "<=":
            return [constraint.lhs]
        case ">=":
            return [-(constraint.lhs)]
        case ">":
            return [-(constraint.lhs)]
        case "==":
            return [constraint.lhs, -(constraint.lhs)]
        case _:
            raise RuntimeError("Invalid constraint kind")


def parse_q_assignment(r: Relational):
    assert isinstance(r, Eq)
    return list(map(lambda expr: to_z3_expr(expr) <= 0, parse_constraint(r)))


def get_symbol_assignment(s: Symbol, q: int) -> Relational:
    return Eq(Add(s, -q), 0)


T = TypeVar("T")
U = TypeVar("U")


def fst(t: tuple[T, U]) -> T:
    return t[0]


def snd(t: tuple[T, U]) -> U:
    return t[1]


def unzip(lst: list[tuple[T, U]]) -> tuple[list[T], list[U]]:
    return [x[0] for x in lst], [x[1] for x in lst]


def DNF_to_linear_function(dnf: Boolean, vars: tuple[Symbol, ...]) -> SPLinearFunction:
    conjuncts = parse_DNF(dnf)
    constraints = list(
        chain.from_iterable(
            map(parse_constraint, chain.from_iterable(map(parse_conjunct, conjuncts)))
        )
    )
    a, neg_b = linear_eq_to_matrix(constraints, vars)
    return a, -neg_b
