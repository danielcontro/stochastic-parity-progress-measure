from collections.abc import Iterable
from functools import reduce
import operator
from typing import Self, TypeVar

from sympy import And, Eq, Matrix, Or, Symbol, Number, Add, Expr, Mul, Pow
from sympy.core.relational import Relational
from sympy.logic.boolalg import Boolean
from z3 import ArithRef, BoolRef, Real, Sqrt
import z3


z3Mat = list[list[ArithRef | float]]

VarMap = dict[str, ArithRef]

_VAR_MAP: VarMap = {}


class Mat:
    _shape: tuple[int, int]

    @staticmethod
    def zeros(rows: int, cols: int):
        return Mat([[0 for _ in range(cols)] for _ in range(rows)])

    @staticmethod
    def ones(rows: int, cols: int):
        return Mat([[1 for _ in range(cols)] for _ in range(rows)])

    def __init__(self, m):
        self._m = m
        self._shape = len(m), len(m[0])
        return

    def __add__(self, other: Self) -> Self:
        assert self._shape == other._shape
        return type(self)(
            [
                [
                    self._m[row][col] + other._m[row][col]
                    for col in range(self._shape[1])
                ]
                for row in range(self._shape[0])
            ]
        )

    def __sub__(self, other: Self) -> Self:
        assert self._shape == other._shape
        return type(self)(
            [
                [
                    self._m[row][col] - other._m[row][col]
                    for col in range(self._shape[1])
                ]
                for row in range(self._shape[0])
            ]
        )

    def scalar_multiplication(self, scalar: ArithRef | float) -> Self:
        return type(self)([[scalar * value for value in row] for row in self._m])

    def mat_multiplication(self, v: Self) -> Self:
        print(self._shape[1], v._shape[0])
        assert self._shape[1] == v._shape[0]
        return type(self)(
            [
                [
                    sum((self._m[row][i] * v._m[i][col] for i in range(self._shape[1])))
                    for col in range(v._shape[1])
                ]
                for row in range(self._shape[0])
            ]
        )

    def dot_product(self, v: Self) -> ArithRef | float:
        """
        A*v = sum(a_i * v_i) for i in range(len(a))
        """
        assert self._shape[0] == v._shape[1] == 1
        assert self._shape[1] == v._shape[0]
        return sum([self._m[0][i] * v._m[i][0] for i in range(self._shape[1])], 0.0)

    def transpose(self) -> Self:
        """
        Returns the transpose of the matrix
        """
        return type(self)(
            [
                [self._m[row][col] for row in range(self._shape[0])]
                for col in range(self._shape[1])
            ]
        )

    def extend_rows(self, rows: Self) -> Self:
        """
        Returns a new matrix with rows to the matrix
        """
        assert rows.shape()[0] > 0
        assert rows.shape()[1] == self._shape[1]
        return type(self)(self._m + rows._m)

    # def add_column(self, columns):
    #     assert len(columns) > 0
    #     assert ()
    #     pass

    def shape(self) -> tuple[int, int]:
        """
        Returns the shape of the matrix as a tuple (rows, columns)
        """
        return self._shape

    def get_constraint(self, order, rhs: Self) -> list[BoolRef]:
        print("self:", self._shape)
        print("rhs:", rhs._shape)
        assert self._shape == rhs._shape
        assert self._shape[1] == rhs._shape[1] == 1

        return [order(self._m[i][0], rhs._m[i][0]) for i in range(self._shape[0])]

    def to_scalar(self) -> ArithRef | float:
        assert self._shape[0] == self._shape[1] == 1
        return self._m[0][0]


def split_disjunctions(e: BoolRef):
    return e.children() if e.decl().name() == "or" else [e]


def parse_matrix(m: Matrix) -> z3Mat:
    return [
        [parse_expr(m[row, column]) for column in range(m.shape[1])]
        for row in range(m.shape[0])
    ]


def update_var_map(sympy_vars: Iterable[Symbol] = []) -> VarMap:
    for var in sympy_vars:
        if var.name not in _VAR_MAP:
            _VAR_MAP[var.name] = Real(var.name)
    return _VAR_MAP


def get_z3_var_map() -> VarMap:
    return _VAR_MAP


def parse_expr(exp: Expr) -> ArithRef | float:
    "convert a sympy expression to a z3 expression. This returns (z3_vars, z3_expression)"

    result_exp = _sympy_to_z3_rec(exp)

    return result_exp


def _sympy_to_z3_rec(e: Expr):
    "recursive call for sympy_to_z3()"

    if not isinstance(e, Expr):
        raise RuntimeError("Expected sympy Expr: " + repr(e))

    if isinstance(e, Symbol):
        z3_var = get_z3_var_map().get(e.name)

        if z3_var is None:
            raise RuntimeError("No var was corresponds to symbol '" + str(e) + "'")
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
        "Type '"
        + str(type(e))
        + "' is not yet implemented for convertion to a z3 expresion. "
        + "Subexpression was '"
        + str(e)
        + "'."
    )


def parse_DNF(dnf: Boolean) -> list[Boolean]:
    if isinstance(dnf, Or):
        assert all(isinstance(x, Boolean) for x in dnf.args)
        return list(dnf.args)

    return [dnf]


def parse_conjunct(conjunct: Boolean) -> list[Relational]:
    if isinstance(conjunct, And):
        conjs = list(conjunct.args)
        assert all(isinstance(x, Boolean) for x in conjs)
        return conjs

    return [conjunct]


def _parse_constr(conjunct: Relational):
    ordering = conjunct.rel_op
    match ordering:
        case "<":
            return parse_expr(conjunct.lhs) < 0
        case "<=":
            return parse_expr(conjunct.lhs) <= 0
        case ">":
            return parse_expr(conjunct.lhs) > 0
        case ">=":
            return parse_expr(conjunct.lhs) >= 0
        case "==":
            return parse_expr(conjunct.lhs) == 0
        case _:
            RuntimeError("Invalid ordering")


def sympy_dnf_to_z3(dnf: Boolean) -> list[BoolRef]:
    conjs = parse_DNF(dnf)
    constraints = list(map(parse_conjunct, conjs))
    return z3.Or(list(map(lambda x: z3.And(list(map(_parse_constr, x))), constraints)))


def z3_real_to_float(z3_real: ArithRef) -> float:
    # fract = z3_real.as_fraction()
    # return float(fract.numerator) / float(fract.denominator)
    return float(z3_real.as_decimal(10))


def parse_constraint(constraint: Relational) -> list[Expr]:
    """
    `constraint` of the form AX + b ~ 0
    with:
    - A: R^(1xn)
    - X: R^n
    - b: R
    - ~ in {<, <=, >=, >, ==}
    """
    assert isinstance(constraint.lhs, Expr)
    ordering = constraint.rel_op
    match ordering:
        case "<":
            return [constraint.lhs]
        case "<=":
            return [constraint.lhs]
        case ">=":
            return [-constraint.lhs]
        case ">":
            return [-constraint.lhs]
        case "==":
            return [constraint.lhs, -constraint.lhs]
        case _:
            raise RuntimeError("Invalid constraint kind")


def parse_q_assignment(r: Relational):
    assert isinstance(r, Eq)
    add = r.lhs
    assert isinstance(add, Add) or isinstance(add, Symbol)
    return parse_expr(add) == 0


def get_q_assignment(s: Symbol, q: int) -> Relational:
    return Eq(Add(s, -q), 0)


T = TypeVar("T")
U = TypeVar("U")


def unzip(lst: list[tuple[T, U]]) -> tuple[list[T], list[U]]:
    return [x[0] for x in lst], [x[1] for x in lst]
