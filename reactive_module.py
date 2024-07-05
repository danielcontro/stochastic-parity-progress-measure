import functools
from itertools import accumulate
import itertools
from typing import Optional, Self

from sympy import Matrix, Symbol
from sympy.logic.boolalg import Boolean

from z3 import BoolRef, Solver


ProgramVariables = tuple[Symbol, ...]
Guard = Boolean
Update = tuple[Matrix, Matrix]
Transition = tuple[float, Update]
StochasticUpdate = list[tuple[float, Update]]
NonDeterministicStochasticUpdate = list[StochasticUpdate]


class Atom:
    def __init__(
        self,
        vars: ProgramVariables,
        ctrl: ProgramVariables,
        read: ProgramVariables,
        wait: ProgramVariables,
        init: list[tuple[Guard, NonDeterministicStochasticUpdate]],
        update: list[tuple[Guard, NonDeterministicStochasticUpdate]],
    ):
        assert all(map(lambda x: x in vars, ctrl))
        assert all(map(lambda x: x in vars, read))
        assert all(map(lambda x: x in vars, wait))

        self._ctrl = ctrl
        self._read = read
        self._wait = wait
        self._init = init
        self._update = update

    # TODO: Get dependency graph
    def _dependency_graph(self):
        pass

    @staticmethod
    def _is_acyclic(dependency_graph) -> bool:
        return True

    @property
    def guards(self) -> list[Guard]:
        return list(map(lambda x: x[0], self._init)) + list(
            map(lambda x: x[0], self._update)
        )

    # @property
    # def vars(self) -> ProgramVariables:
    #     return self._ctrl + self._read + self._wait unique


class RM1:
    def __init__(
        self,
        ext_vars: ProgramVariables,
        int_vars: ProgramVariables,
        body: list[Atom],
    ):
        # TODO: Check for:
        # - acyclicity of the dependency graph
        # - mutual empty disjunction of control sets
        # - no useless variables (opt)

        self._ext_vars = ext_vars
        self._int_vars = int_vars
        self._body = body

    @property
    def guards(self) -> list[Guard]:
        return functools.reduce(
            list.append, map(lambda atom: atom.guards, self._body), []
        )

    @property
    def vars(self) -> ProgramVariables:
        return self._ext_vars + self._int_vars

    def parallel_composition(self, other: Self) -> Optional[Self]:
        pass


class ReactiveModule:
    def __init__(
        self,
        init: tuple[float, ...],
        vars: ProgramVariables,
        body: list[tuple[Guard, list[list[Transition]]]],
    ):
        """
        Assume guards mutually exclusive
        guard = A*X op b
        update = A,b such that X' = A*X + b
        """
        # FIXME: Guards not in DNF form
        assert len(init) == len(vars)

        self._state = init
        self._vars = vars
        self._body = body

    @property
    def guards(self) -> list[Guard]:
        return list(map(lambda el: el[0], self._body))

    @property
    def vars(self) -> ProgramVariables:
        return self._vars

    def _eval_guard(self, guard: BoolRef, state: tuple[float, ...]) -> bool:
        assignments = [x == v for x, v in zip(self._vars, state)]
        s = Solver()
        s.add(assignments)
        m = s.model()
        eval = m.eval(guard)
        assert isinstance(eval, bool)
        return eval

    def transitions(self, guard_idx: int) -> list[list[Transition]]:
        return self._body[guard_idx][1]

    def parallel_composition(self, other: Self) -> Optional[Self]:
        # TODO: Check for compatibility
        return
        # assert self.vars == other.vars
        # new_body = []
        # for (guard1, trans1), (guard2, trans2) in zip(self._body, other._body):
        #     new_guard = guard1 & guard2
        #     new
