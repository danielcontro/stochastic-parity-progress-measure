from sympy import Matrix, Symbol
from sympy.logic.boolalg import Boolean

from z3 import BoolRef, Solver


ProgramVariables = tuple[Symbol, ...]
Guard = Boolean
Update = tuple[Matrix, Matrix]
Transition = tuple[float, Update]


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
