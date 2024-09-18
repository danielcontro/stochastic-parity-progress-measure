from itertools import chain
import itertools

from sympy import And, Matrix, Symbol, linear_eq_to_matrix, ones, zeros
from sympy.logic.boolalg import Boolean

from z3 import BoolRef, Solver, unsat

from utils import (
    SPLinearFunction,
    extend_matrix,
    fst,
    parse_conjunct,
    satisfiable,
    snd,
    to_z3_dnf,
    update_var_map,
)

from typing import Self


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
        update_var_map(self._vars)

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

    def parallel_composition(self, other: Self):
        common_vars, _, _ = self._common_vars(other)
        return ReactiveModule(
            self._init_composition(other),
            self.vars + tuple(filter(lambda var: var not in common_vars, other.vars)),
            self._guarded_commands_composition(other),
        )

    def _common_vars(self, other: Self) -> tuple[list[Symbol], list[int], list[int]]:
        common_vars = list(filter(lambda x: x in other.vars, self.vars))
        return (
            common_vars,
            list(map(lambda x: self.vars.index(x), common_vars)),
            list(map(lambda x: other.vars.index(x), common_vars)),
        )

    def _init_composition(self, other: Self) -> list[ProgramState]:
        """
        Computes the set of initial states of the product of two reactive modules
        """

        _, self_indexes, other_indexes = self._common_vars(other)

        return list(
            map(
                lambda self_other_init: fst(self_other_init)
                + tuple(
                    map(
                        snd,
                        filter(
                            lambda i_el: fst(i_el) not in other_indexes,
                            enumerate(snd(self_other_init)),
                        ),
                    )
                ),
                filter(
                    lambda self_other_init: all(
                        fst(self_other_init)[self_idx]
                        == snd(self_other_init)[other_idx]
                        for self_idx, other_idx in zip(self_indexes, other_indexes)
                    ),
                    itertools.product(self.init, other.init),
                ),
            )
        )

    def _update_composition(
        self,
        other: Self,
        self_update: Update,
        other_update: Update,
    ) -> Update:
        # Compute the update equation for both modules
        self_equations = list(self_update[0] * Matrix(self.vars) + self_update[1])
        other_equations = list(other_update[0] * Matrix(other.vars) + other_update[1])

        common_vars, self_indexes, other_indexes = self._common_vars(other)

        # Sum the equations relative to common variables
        for self_idx, other_idx in zip(self_indexes, other_indexes):
            self_equations[self_idx] += other_equations[other_idx]

        # Remove common variables equations from the other ReactiveModule
        other_equations_common_stripped = list(
            map(
                snd,
                filter(
                    lambda x: fst(x) not in other_indexes, enumerate(other_equations)
                ),
            )
        )
        # Compute the update function for the composed ReactiveModule
        composed_update = linear_eq_to_matrix(
            self_equations + other_equations_common_stripped,
            list(
                self.vars
                + tuple(filter(lambda var: var not in common_vars, other.vars))
            ),
        )
        return composed_update[0], -composed_update[1]

    def _stoc_update_composition(
        self,
        other: Self,
        self_updates: StochasticUpdate,
        other_updates: StochasticUpdate,
    ) -> StochasticUpdate:
        return list(
            map(
                lambda x: (
                    fst(fst(x)) * fst(snd(x)),  # p(self_update) * p(other_update)
                    self._update_composition(
                        other,
                        snd(fst(x)),  # self_update
                        snd(snd(x)),  # other_update
                    ),
                ),
                itertools.product(self_updates, other_updates),
            )
        )

    def _non_det_stoc_update_composition(
        self,
        other: Self,
        self_updates: NonDeterministicStochasticUpdate,
        other_updates: NonDeterministicStochasticUpdate,
    ) -> NonDeterministicStochasticUpdate:
        return list(
            map(
                lambda x: self._stoc_update_composition(
                    other,
                    fst(x),  # self_stochastic_update
                    snd(x),  # other_stochastic_update
                ),
                itertools.product(self_updates, other_updates),
            )
        )

    def _guarded_commands_composition(self, other: Self) -> list[GuardedCommand]:
        """
        Computes the set of guarded commands of the parallel composition of two reactive modules
        """
        return list(
            map(
                lambda x: (
                    And(*(parse_conjunct(fst(fst(x))) + parse_conjunct(fst(snd(x))))),
                    self._non_det_stoc_update_composition(
                        other,
                        snd(fst(x)),  # self_non_det_stochastic_update
                        snd(snd(x)),  # other_non_det_stochastic_update
                    ),
                ),
                filter(
                    lambda x: satisfiable(
                        to_z3_dnf(
                            And(
                                *(
                                    parse_conjunct(fst(fst(x)))  # guard of self
                                    + parse_conjunct(fst(snd(x)))  # guard of other
                                )
                            )
                        )
                    ),
                    itertools.product(self.body, other.body),
                ),
            )
        )
