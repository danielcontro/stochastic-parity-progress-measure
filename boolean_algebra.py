import itertools
from sympy import Add, Expr, LessThan, false, true
from sympy.core import relational
from sympy.core.relational import Relational
from sympy.logic.boolalg import Boolean, BooleanAtom, BooleanFalse, BooleanTrue
from z3 import BoolRef, Solver, sat, z3

from utils import to_z3_expr

from typing import Self

# class Guard:
#     @staticmethod
#     def _parse_dnf(dnf: Boolean) -> list[list[LessThan | BooleanAtom]]:
#         """
#         Parses the boolean dnf expression `boolean` and converts `Relational`
#         expressions to `LessThan` 0 expressions.
#         """
#         # NOTE: No negation support for the time being
#         if isinstance(dnf, BooleanAtom) or isinstance(dnf, Relational):
#             return [Guard._parse_literal(dnf)]
#         if isinstance(dnf, And):
#             return [Guard._parse_conjunct(dnf)]
#         assert isinstance(dnf, Or)
#         return list(map(Guard._parse_conjunct, dnf.args))
#
#     @staticmethod
#     def _parse_conjunct(conjunct: Boolean) -> list[LessThan | BooleanAtom]:
#         """
#         Parses the boolean conjunct expression `conjunct` and converts `Relational`
#         expressions to `LessThan` 0 expressions.
#         """
#         if isinstance(conjunct, And):
#             return list(chain.from_iterable(map(Guard._parse_literal, conjunct.args)))
#         return Guard._parse_literal(conjunct)
#
#     @staticmethod
#     def _parse_literal(constraint: Boolean) -> list[LessThan | BooleanAtom]:
#         if isinstance(constraint, BooleanAtom):
#             return [constraint]
#
#         assert isinstance(constraint, Relational)
#         assert isinstance(constraint.lhs, Expr) and isinstance(constraint.rhs, Expr)
#
#         match type(constraint):
#             case relational.LessThan | relational.StrictLessThan:
#                 return [LessThan(Add(constraint.lhs, -constraint.rhs), 0)]
#             case relational.GreaterThan | relational.StrictGreaterThan:
#                 return [LessThan(Add(-constraint.lhs, constraint.rhs), 0)]
#             case relational.Equality | relational.Unequality:
#                 return [
#                     LessThan(Add(constraint.lhs, -constraint.rhs), 0),
#                     LessThan(Add(-constraint.lhs, constraint.rhs), 0),
#                 ]
#             case _:
#                 raise RuntimeError(f"Invalid constraint: {type(constraint)}")
#
#     def __init__(self, dnf: Boolean):
#         self._dnf = Guard._parse_dnf(dnf)
#
#     @property
#     def conjuncts(self) -> list[list[LessThan | BooleanAtom]]:
#         return self._dnf
#
#     def to_z3(self, vars: Iterable[Symbol]):
#         a, b = linear_eq_to_matrix([], vars)
#         pass
#
#     def satisfiable(self):
#         solver = Solver()
#         return solver.check() == sat


class Constraint:
    @staticmethod
    def _parse_constraint(constraint: Relational) -> list[LessThan]:
        assert isinstance(constraint.lhs, Expr) and isinstance(constraint.rhs, Expr)
        match type(constraint):
            case relational.LessThan:
                if isinstance(constraint.lhs, Add) and constraint.rhs == 0:
                    # No need to reallocate the constraint
                    return [constraint]
                return [LessThan(Add(constraint.lhs, -constraint.rhs), 0)]
            case relational.StrictLessThan:
                return [LessThan(Add(constraint.lhs, -constraint.rhs), 0)]
            case relational.GreaterThan | relational.StrictGreaterThan:
                return [LessThan(Add(-constraint.lhs, constraint.rhs), 0)]
            case relational.Equality | relational.Unequality:
                return [
                    LessThan(Add(constraint.lhs, -constraint.rhs), 0),
                    LessThan(Add(-constraint.lhs, constraint.rhs), 0),
                ]
            case _:
                raise RuntimeError(f"Invalid constraint: {type(constraint)}")

    @staticmethod
    def from_relational(constraint: Relational):
        return Constraint(Constraint._parse_constraint(constraint))

    def __init__(self, constraint: list[LessThan]) -> None:
        self._constraint = constraint

    def to_z3(self) -> list[BoolRef | bool]:
        return [to_z3_expr(c.lhs) <= 0 for c in self._constraint]

    def satisfiable(self) -> bool:
        solver = Solver()
        solver.add(self.to_z3())
        return solver.check() == sat

    def negate(self):
        return Constraint(
            list(map(lambda x: LessThan(-x.lhs, x.rhs), self._constraint))
        )


class Conjunction:
    @staticmethod
    def from_boolean(conjunction: Boolean):
        if false in conjunction.args:
            return Conjunction(false)
        elif all(map(lambda x: isinstance(x, BooleanTrue), conjunction.args)):
            return Conjunction(true)
        elif isinstance(conjunction, Relational):
            return Conjunction([Constraint(conjunction)])
        else:
            return Conjunction(
                list(
                    map(
                        lambda x: Constraint(x),
                        list(
                            filter(
                                # Safely remove True constraints
                                lambda x: not isinstance(x, BooleanTrue),
                                conjunction.args,
                            )
                        ),
                    )
                )
            )

    def __init__(self, constraints: BooleanAtom | list[Constraint]) -> None:
        self._constraints = constraints

    @property
    def constraints(self):
        return self._constraints

    def to_z3(self):
        match self._constraints:
            case BooleanFalse():
                return False
            case BooleanTrue():
                return True
            case _:
                return z3.And(*list(map(lambda x: x.to_z3(), self._constraints)))

    def satisfiable(self):
        match self._constraints:
            case BooleanFalse():
                return False
            case BooleanTrue():
                return True
            case _:
                solver = Solver()
                solver.add(self.to_z3())
                return solver.check() == sat

    def intersect(self, other: Self):
        match self.constraints, other.constraints:
            case (BooleanFalse(), _) | (_, BooleanFalse()):
                return Conjunction(false)
            case (BooleanTrue(), _):
                return other
            case (_, BooleanTrue()):
                return self
            case _:
                return Conjunction(self.constraints + other.constraints)

    def negate(self):
        pass


class DNF:
    @staticmethod
    def from_boolean(dnf: Boolean):
        if true in dnf.args:
            return DNF(true)
        elif all(map(lambda x: isinstance(x, BooleanFalse), dnf.args)):
            return DNF(false)
        elif isinstance(dnf, Relational):
            return DNF([Conjunction.from_boolean(dnf)])
        else:
            return DNF(
                list(
                    map(
                        lambda x: Conjunction.from_boolean(x),
                        list(
                            filter(
                                # Safely remove False constraints
                                lambda x: not isinstance(x, BooleanFalse),
                                dnf.args,
                            )
                        ),
                    )
                )
            )

    def __init__(self, conjunctions: BooleanAtom | list[Conjunction]) -> None:
        self._conjunctions = conjunctions

    @property
    def conjunctions(self):
        return self._conjunctions

    def to_z3(self):
        match self.conjunctions:
            case BooleanFalse():
                return False
            case BooleanTrue():
                return True
            case _:
                assert isinstance(self.conjunctions, list)
                return z3.Or(*list(map(lambda x: x.to_z3(), self.conjunctions)))

    def satisfiable(self):
        match self.conjunctions:
            case BooleanFalse():
                return False
            case BooleanTrue():
                return True
            case _:
                solver = Solver()
                solver.add(self.to_z3())
                return solver.check() == sat

    def intersect(self, other: Self):
        match self.conjunctions, other.conjunctions:
            case (BooleanFalse(), _) | (_, BooleanFalse()):
                return DNF(false)
            case (BooleanTrue(), _):
                return other
            case (_, BooleanTrue()):
                return self
            case _:
                assert isinstance(self.conjunctions, list) and isinstance(
                    other.conjunctions, list
                )
                new_conjunctions = []
                for c1, c2 in itertools.product(self.conjunctions, other.conjunctions):
                    conjunction = c1.intersect(c2)
                    if conjunction.satisfiable():
                        new_conjunctions.append(conjunction)
                return DNF(new_conjunctions)

    def negate(self):
        pass
