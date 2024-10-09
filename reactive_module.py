from itertools import chain
import itertools

from sympy import And, Matrix, Symbol, eye, linear_eq_to_matrix, ones, zeros
from sympy.core.relational import Relational
from sympy.logic.boolalg import Boolean

from z3 import BoolRef, Solver, unsat

from utils import (
    SPLinearFunction,
    extend_matrix,
    fst,
    parse_conjunction,
    satisfiable,
    snd,
    to_z3_dnf,
    update_var_map,
)

from typing import Optional, Self


ProgramVariables = tuple[Symbol, ...]
ProgramState = tuple[float, ...]
Guard = Boolean
Update = SPLinearFunction
ProbabilisticUpdate = tuple[float, Update]
StochasticUpdate = list[ProbabilisticUpdate]
NonDeterministicStochasticUpdate = list[StochasticUpdate]
# GuardedCommand = tuple[Guard, NonDeterministicStochasticUpdate]


class GuardedCommand:
    def __init__(
        self, labels: list[str], guard: Guard, updates: NonDeterministicStochasticUpdate
    ):
        self._labels = labels
        self._guard = guard
        self._updates = updates

    @property
    def labels(self) -> list[str]:
        return self._labels

    @property
    def guard(self) -> Guard:
        return self._guard

    @property
    def update(self) -> NonDeterministicStochasticUpdate:
        return self._updates

    def interleave(
        self,
        other: Self,
        new_guard: Guard,
        strict_self_vars: int,
        strict_other_vars: int,
        common_vars: int,
        order: list[Optional[int]],
    ):
        return GuardedCommand(
            list(set(self.labels).union(other.labels)),
            new_guard,
            self._extend(strict_self_vars + common_vars, strict_other_vars)
            + other._extend_and_reorder(order, strict_other_vars + common_vars),
        )

    def extend(self, new_guard: Guard, strict_self_vars: int, strict_other_vars: int):
        return GuardedCommand(
            self.labels,
            new_guard,
            self._extend(strict_self_vars, strict_other_vars),
        )

    def extend_and_reorder(
        self, new_guard: Guard, self_vars: int, order: list[Optional[int]]
    ):
        return GuardedCommand(
            self.labels,
            new_guard,
            self._extend_and_reorder(order, self_vars),
        )

    def _extend(
        self, strict_self_vars: int, strict_other_vars: int
    ) -> NonDeterministicStochasticUpdate:
        extension_a = zeros(strict_other_vars, strict_self_vars).row_join(
            eye(strict_other_vars)
        )
        extension_b = zeros(strict_other_vars, 1)
        return list(
            map(
                lambda x: list(
                    map(
                        lambda x: (
                            x[0],
                            (
                                x[1][0]
                                .row_join(zeros(strict_self_vars, strict_other_vars))
                                .col_join(extension_a),
                                x[1][1].col_join(extension_b),
                            ),
                        ),
                        x,
                    )
                ),
                self.update,
            )
        )

    def _extend_and_reorder(
        self,
        order: list[Optional[int]],
        self_vars: int,
    ) -> NonDeterministicStochasticUpdate:
        def f(update: Update):
            # Extend self vars updates to take account of new variables
            extended_a = Matrix()
            extended_b = Matrix()
            for n in range(len(order)):
                if order[n] is not None:
                    extended_a = extended_a.row_join(update[0].col(n))
                    extended_b = extended_b.col_join(update[1].row(n))
                else:
                    extended_a = extended_a.row_join(zeros(self_vars, 1))
                    extended_b = extended_b.col_join(zeros(1))

            new_a = Matrix()
            new_b = Matrix()
            new_row_count = 0
            # Extend update to include new variables
            for n in range(len(order)):
                if order[n] is None:
                    new_a = new_a.col_join(extension_a.row(new_row_count))
                    new_b = new_b.col_join(extension_b)
                    new_row_count += 1
                else:
                    new_a = new_a.col_join(extended_a.row(n))
                    new_b = new_b.col_join(extended_b.row(n))

            return new_a, new_b

        new_rows = list(
            map(lambda x: x[0], filter(lambda x: x[1] is None, enumerate(order)))
        )
        extension_a = Matrix(
            [[0] * (i - 1) + [1] + [0] * (len(order) - i) for i in new_rows]
        )
        extension_b = Matrix([[0]])

        return list(
            map(
                lambda stoc_update: list(map(lambda x: (x[0], f(x[1])), stoc_update)),
                self.update,
            )
        )


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
        return list(map(lambda el: el.guard, self._body))

    @property
    def updates(self) -> list[Update]:
        return list(
            map(
                snd,
                chain.from_iterable(
                    map(lambda el: chain.from_iterable(el.update), self._body)
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
        return self._body[command_idx].update

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
                lambda x: GuardedCommand(
                    [],
                    And(
                        *(
                            parse_conjunction(fst(x).guard)
                            + parse_conjunction(snd(x).guard)
                        )
                    ),
                    self._non_det_stoc_update_composition(
                        other,
                        fst(x).update,  # self_non_det_stochastic_update
                        snd(x).update,  # other_non_det_stochastic_update
                    ),
                ),
                filter(
                    lambda x: satisfiable(
                        to_z3_dnf(
                            And(
                                *(
                                    parse_conjunction(fst(x).guard)  # guard of self
                                    + parse_conjunction(snd(x).guard)  # guard of other
                                )
                            )
                        )
                    ),
                    itertools.product(self.body, other.body),
                ),
            )
        )

    def _body_interleaving(self, other: Self) -> list[GuardedCommand]:
        new_gc = []
        common_vars, _, _ = self._common_vars(other)
        new_vars = self.vars + tuple(
            filter(lambda var: var not in common_vars, other.vars)
        )
        strict_self_vars = len(self.vars) - len(common_vars)
        strict_other_vars = len(other.vars) - len(common_vars)

        other_order = list(
            map(
                lambda x: None if x not in common_vars else other.vars.index(x),
                new_vars,
            )
        )

        for gc, other_gc in itertools.product(self.body, other.body):
            guard = And(
                *(parse_conjunction(gc.guard) + parse_conjunction(other_gc.guard))
            )
            if not satisfiable(to_z3_dnf(guard)):
                continue
            new_gc.append(
                gc.interleave(
                    other_gc,
                    guard,
                    strict_self_vars,
                    strict_other_vars,
                    len(common_vars),
                    other_order,
                )
            )

        for gc in self.body:
            neg_other_guards = list(
                chain.from_iterable(
                    [parse_conjunction(other_gc.guard) for other_gc in other.body]
                )
            )
            guard = And(*parse_conjunction(gc.guard) + neg_other_guards)
            if not satisfiable(to_z3_dnf(guard)):
                continue
            new_gc.append(gc.extend(guard, strict_self_vars, strict_other_vars))

        for other_gc in other.body:
            neg_self_guards = list(
                chain.from_iterable([parse_conjunction(gc.guard) for gc in self.body])
            )
            guard = And(*parse_conjunction(other_gc.guard) + neg_self_guards)
            if not satisfiable(to_z3_dnf(guard)):
                continue
            new_gc.append(
                other_gc.extend_and_reorder(
                    guard, strict_other_vars + len(common_vars), other_order
                )
            )

        return new_gc

    def interleaving(self, other: Self):
        return ReactiveModule(
            self._init_composition(other),
            self.vars + tuple(filter(lambda var: var not in self.vars, other.vars)),
            self._body_interleaving(other),
        )
