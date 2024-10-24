from collections.abc import Callable, Iterable
import enum
from functools import reduce
from itertools import chain
import operator
from typing import Optional, Self, TypeVar

from sympy import (
    And,
    Eq,
    Equality,
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
    Unequality,
    linear_eq_to_matrix,
    zeros,
)
import sympy
from sympy.core.relational import Relational
from sympy.logic.boolalg import Boolean, BooleanFalse, BooleanTrue
from z3 import ArithRef, BoolRef, Real, Solver, Sqrt, sat
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


def parse_disjunction(dnf: Boolean) -> list[Boolean]:
    if isinstance(dnf, Or):
        print(dnf.args)
        return list(dnf.args)

    return [dnf]


def parse_conjunction(conjunct: Boolean) -> list[Relational]:
    """
    Extrapolates a list of constraints from a conjunct
    """
    if isinstance(conjunct, And):
        conjs = list(conjunct.args)
        assert all(isinstance(x, Boolean) for x in conjs)
        return conjs

    return [conjunct]


def _parse_constraint(constraint: Relational) -> BoolRef:
    assert isinstance(constraint.lhs, Expr) and isinstance(constraint.rhs, Expr)
    match type(constraint):
        case sympy.StrictLessThan:
            return to_z3_expr(constraint.lhs) < 0
        case sympy.LessThan:
            return to_z3_expr(constraint.lhs) <= 0
        case sympy.StrictGreaterThan:
            return to_z3_expr(constraint.lhs) > 0
        case sympy.GreaterThan:
            return to_z3_expr(constraint.lhs) >= 0
        case sympy.Equality:
            return to_z3_expr(constraint.lhs) == 0
        case sympy.Unequality:
            return to_z3_expr(constraint.lhs) != 0
        case _:
            raise RuntimeError(f"Invalid ordering {type(constraint)} {constraint}")


def to_z3_dnf(dnf: Boolean) -> list[BoolRef]:
    if isinstance(dnf, BooleanFalse):
        return [False]
    if isinstance(dnf, BooleanTrue):
        return [True]
    conjunctions = parse_disjunction(dnf)
    dnf_repr = list(
        map(
            lambda conjunction: list(
                map(_parse_constraint, parse_conjunction(conjunction))
            ),
            conjunctions,
        )
    )
    return z3.Or(*list(map(lambda x: z3.And(*x), dnf_repr)))


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
    if isinstance(constraint, BooleanTrue):
        return [0]
    assert isinstance(constraint.lhs, Expr)
    match type(constraint):
        case sympy.StrictLessThan:
            return [constraint.lhs]
        case sympy.LessThan:
            return [constraint.lhs]
        case sympy.StrictGreaterThan:
            return [-constraint.lhs]
        case sympy.GreaterThan:
            return [-constraint.lhs]
        case sympy.Equality:
            return [constraint.lhs, -constraint.lhs]
        case sympy.Unequality:
            return [constraint.lhs, -constraint.lhs]
        case _:
            raise RuntimeError("Invalid ordering")


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
    conjuncts = parse_disjunction(dnf)
    constraints = list(
        chain.from_iterable(
            map(
                parse_constraint, chain.from_iterable(map(parse_conjunction, conjuncts))
            )
        )
    )
    a, neg_b = linear_eq_to_matrix(constraints, vars)
    return a, -neg_b


def equations_to_update(equations, variables: Iterable[Symbol]) -> SPLinearFunction:
    a, b = linear_eq_to_matrix(equations, variables)
    return a, -b


def negate_constraint(constraint) -> Boolean | Relational:
    # TODO:
    if isinstance(constraint, BooleanFalse) or isinstance(constraint, BooleanTrue):
        return ~constraint
    match type(constraint):
        case sympy.StrictLessThan:
            return GreaterThan(constraint.lhs, 0)
        case sympy.LessThan:
            return StrictGreaterThan(constraint.lhs, 0)
        case sympy.StrictGreaterThan:
            return LessThan(constraint.lhs, 0)
        case sympy.GreaterThan:
            return StrictLessThan(constraint.lhs, 0)
        case sympy.Equality:
            return Unequality(constraint.lhs, 0)
        case sympy.Unequality:
            return Equality(constraint.lhs, 0)
        case _:
            raise RuntimeError("Invalid ordering")


def extend_matrix(a: Matrix, ext: Matrix) -> Matrix:
    """
    Given two matrices `a` and `ext`, return the matrix
    a | 0
    -------
    0 | ext
    Example:
    a = [1   2]    ext =  [ 5    6    7]
        [3   4]           [ 8    9   10]
                          [11   12   13]

    returns [1   2    0    0    0]
            [3   4    0    0    0]
            [0   0    5    6    7]
            [0   0    8    9   10]
            [0   0   11   12   13]

    """
    return a.row_join(zeros(a.rows, ext.cols)).col_join(
        zeros(ext.rows, a.cols).row_join(ext)
    )


def satisfiable(query):
    solver = Solver()
    solver.add(query)
    return solver.check() == sat


def var_rel_val(var: Symbol, rel, val: float) -> Relational:
    return rel(Add(var, -val), 0)


var_eq_val = lambda var, val: var_rel_val(var, Equality, val)
var_gt_val = lambda var, val: var_rel_val(var, StrictGreaterThan, val)
var_ge_val = lambda var, val: var_rel_val(var, GreaterThan, val)
var_lt_val = lambda var, val: var_rel_val(var, StrictLessThan, val)
var_le_val = lambda var, val: var_rel_val(var, LessThan, val)
var_ne_val = lambda var, val: var_rel_val(var, Unequality, val)


def first(
    predicate: Callable[[T], bool], iterable: Iterable[T], default: Optional[T] = None
) -> Optional[T]:
    return next(filter(predicate, iterable), default)


def first_with_exception(predicate: Callable[[T], bool], iterable: Iterable[T]) -> T:
    return next(filter(predicate, iterable))
