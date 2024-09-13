from itertools import chain

from sympy import Matrix, Symbol
from sympy.logic.boolalg import Boolean

from z3 import BoolRef, Solver

from utils import SPLinearFunction, snd


ProgramVariables = tuple[Symbol, ...]
ProgramState = tuple[float, ...]
Guard = Boolean
Update = SPLinearFunction
ProbabilisticUpdate = tuple[float, Update]
StochasticUpdate = list[ProbabilisticUpdate]
NonDeterministicStochasticUpdate = list[StochasticUpdate]
GuardedCommand = tuple[Guard, NonDeterministicStochasticUpdate]


class ReactiveModule:
    def __init__(
        self,
        init: list[ProgramState],
        vars: ProgramVariables,
        body: list[GuardedCommand],
    ):
        """
        Assume guards mutually exclusive and given as conjunction of inequalities/equalities
        guard = A*X ~ b
        update = A,b such that X' = A*X + b
        """
        # FIXME: Guards not in DNF form
        # assert len(init) == len(vars)

        self._init = init
        self._vars = vars
        self._body = body

    @property
    def init(self) -> list[ProgramState]:
        return self._init

    @property
    def vars(self) -> ProgramVariables:
        return self._vars

    @property
    def body(self):
        return self._body

    @property
    def guards(self) -> list[Guard]:
        return list(map(lambda el: el[0], self._body))

    @property
    def updates(self) -> list[Update]:
        return list(
            map(
                snd,
                chain.from_iterable(
                    map(lambda el: chain.from_iterable(snd(el)), self._body)
                ),
            )
        )

    def _eval_guard(self, guard: BoolRef, state: tuple[float, ...]) -> bool:
        assignments = [x == v for x, v in zip(self._vars, state)]
        s = Solver()
        s.add(assignments)
        m = s.model()
        eval = m.eval(guard)
        assert isinstance(eval, bool)
        return eval

    def get_nth_command_updates(
        self, command_idx: int
    ) -> NonDeterministicStochasticUpdate:
        return self._body[command_idx][1]
