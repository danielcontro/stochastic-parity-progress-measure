from abc import abstractmethod
from typing import Any, Generic, Optional, Self, TypeVar
import sympy
from sympy.core.relational import Relational
from sympy.logic.boolalg import Boolean, BooleanAtom, BooleanFalse, BooleanTrue

from sympy import Add, Expr, LessThan, Matrix, StrictLessThan, Symbol

from collections.abc import Callable, Iterable

from z3 import ArithRef, BoolRef

from utils import first, first_with_exception, fst, snd, to_z3_expr


ParityObjective = Boolean
Specification = list[ParityObjective]
State = Matrix
Variables = tuple[Symbol, ...]


class Constraint:
    def __init__(
        self, constraint: Relational | list[LessThan] | BooleanAtom, vars: Variables
    ) -> None:
        self._vars = vars
        if isinstance(constraint, list) or isinstance(constraint, BooleanAtom):
            self._constraints = constraint
        elif isinstance(constraint, LessThan) and constraint.rhs == 0:
            self._constraints = [constraint]
        else:
            assert isinstance(constraint.lhs, Expr) and isinstance(constraint.rhs, Expr)
            match type(constraint):
                case sympy.LessThan:
                    self._constraints = [
                        LessThan(Add(constraint.lhs, -constraint.rhs), 0)
                    ]
                case sympy.StrictLessThan:
                    self._constraints = [
                        LessThan(Add(constraint.lhs, -constraint.rhs), 0)
                    ]
                case sympy.GreaterThan:
                    self._constraints = [
                        LessThan(Add(constraint.rhs, -constraint.lhs), 0)
                    ]
                case sympy.StrictGreaterThan:
                    self._constraints = [
                        LessThan(Add(constraint.rhs, -constraint.lhs), 0)
                    ]
                case sympy.Equality:
                    self._constraints = [
                        LessThan(Add(constraint.lhs, -constraint.rhs), 0),
                        LessThan(Add(constraint.rhs, -constraint.lhs), 0),
                    ]
                case sympy.Unequality:
                    self._constraints = [
                        LessThan(Add(constraint.lhs, -constraint.rhs), 0),
                        LessThan(Add(constraint.rhs, -constraint.lhs), 0),
                    ]
                case _:
                    raise ValueError(
                        f"Unsupported constraint type: {type(constraint)}, {constraint}"
                    )

    def __call__(self, state: State) -> bool:
        match self._constraints:
            case BooleanTrue():
                return True
            case BooleanFalse():
                return False
            case [_]:
                return all(
                    map(
                        lambda constraint: constraint.evalf(
                            subs=dict(zip(self.vars, state.transpose().tolist()[0]))
                        )
                        <= 0,
                        self._constraints,
                    )
                )
            case _:
                raise ValueError(
                    f"Unexpected constraint type {type(self._constraints)}"
                )

    @property
    def vars(self):
        return self._vars

    def to_z3(self) -> list[BoolRef | bool]:
        """
        Returns a list of constraints in an z3 compatible form; the list
        returned has to be interpreted as a conjunction of constraints.
        """
        match self._constraints:
            case BooleanTrue():
                return [True]
            case BooleanFalse():
                return [False]
            case [_]:
                return list(
                    map(
                        lambda constraint: to_z3_expr(constraint.lhs) <= 0,
                        self._constraints,
                    )
                )
            case _:
                raise ValueError(
                    f"Unexpected constraint type {type(self._constraints)}"
                )


class Guard:
    def __init__(self, condition, vars: Variables) -> None:
        # Parse `condition` into a set of `<= 0` constraints
        ()

    def __call__(self, state: State) -> bool:
        return True

    def to_z3(self):
        pass


class Function:
    def __init__(self, variables: Variables) -> None:
        self._variables = variables

    @property
    def variables(self):
        return self._variables

    @abstractmethod
    def __call__(self, state: State) -> Any:
        pass

    @abstractmethod
    def to_z3(self) -> Any:
        pass


class LinearFunction(Function):
    def __init__(self, a: Matrix, b: Matrix, variables: Variables) -> None:
        super().__init__(variables)
        self._a = a
        self._b = b

    @property
    def a(self):
        return self._a

    @property
    def b(self):
        return self._b

    def __call__(self, state: State) -> State:
        return self.a * state + self.b

    def to_z3(self):
        pass


U = TypeVar("U")


class Distribution[T]:
    def __init__(self, distribution: Iterable[tuple[float, T]]) -> None:
        assert sum(map(fst, distribution)) == 1
        self._distribution = distribution

    @property
    def probabilities(self):
        return list(map(fst, self._distribution))

    @property
    def values(self):
        return list(map(snd, self._distribution))

    @property
    def distribution(self):
        return self._distribution

    def element(self, value: T) -> tuple[float, T]:
        return first_with_exception(lambda x: snd(x) == value, self.distribution)


class StochasticLinearFunction(Function):
    def __init__(
        self, probability: float, f: LinearFunction, variables: Variables
    ) -> None:
        super().__init__(variables)
        self._probability = probability
        self._f = f

    @property
    def probability(self):
        return self._probability

    @property
    def f(self):
        return self._f

    @property
    def a(self):
        return self.f.a

    @property
    def b(self):
        return self.f.b

    def __call__(self, state: State) -> tuple[float, State]:
        return self.probability, self.f(state)

    def to_z3(self):
        pass


class PiecewiseLinearFunction(Function):
    def __init__(self, piecewise_functions: list[tuple[Guard, LinearFunction]]) -> None:
        super().__init__(
            # The variables of the piecewise linear functions are the union of
            # the variables of all the linear functions
            tuple(sum(map(lambda x: x[1].variables, piecewise_functions), ()))
        )
        self._piecewise_functions = piecewise_functions

    @property
    def piecewise_functions(self):
        return self._piecewise_functions

    @property
    def functions(self):
        return list(map(snd, self.piecewise_functions))

    @property
    def guards(self):
        return list(map(fst, self.piecewise_functions))

    def __call__(self, state: State) -> State:
        update = first(lambda x: fst(x)(state), self.piecewise_functions)
        if update is None:
            raise ValueError("No update found for the given state")
        update_variables = update[1].variables
        update_state = Matrix(
            len(update_variables),
            1,
            lambda i, _: state[self.variables.index(update_variables[i]), 0],
        )
        next_update_state = update[1](update_state)
        # Returns the next state with the new values of the variables updated
        # by the selected piecewise function and the old values of the rest of
        # the variables
        return Matrix(
            state.rows,
            1,
            lambda i, _: state[i, 0]
            if self.variables[i] not in update_variables
            else next_update_state[update_variables.index(self.variables[i]), 0],
        )


class StochasticUpdate:
    def __init__(
        self,
        vars: Variables,
        probability: float,
        update: LinearFunction,
    ) -> None:
        self._vars = vars
        self._probability = probability
        self._update = update

    @property
    def vars(self):
        return self._vars

    @property
    def probability(self):
        return self._probability

    @property
    def update(self):
        return self._update

    def __call__(self, state: State) -> tuple[float, State]:
        return self.probability, self.update(state)


class NonDeterministic[T]:
    def __init__(self, choices: list[tuple[Guard, T]]) -> None:
        self._choices = choices

    @property
    def choices(self):
        return self._choices

    @property
    def elements(self):
        return list(map(snd, self.choices))

    @property
    def guards(self):
        return list(map(fst, self.choices))

    def __call__(self, state: State) -> T:
        return snd(first_with_exception(lambda x: fst(x)(state), self.choices))


class Update:
    def __init__(
        self,
        local_vars: Variables,
        input_vars: Variables,
        update: NonDeterministic[Distribution[LinearFunction]],
    ) -> None:
        # Check that the sum of the probabilities is 1 for each
        # stochastic update
        self._local_vars = local_vars
        self._input_vars = input_vars
        # Guards of the update are assumed to be disjoint
        self._update = update

    @property
    def local_vars(self):
        return self._local_vars

    @property
    def input_vars(self):
        return self._input_vars

    @property
    def update(self):
        return self._update

    def __call__(self, state: State, input: State) -> Distribution[State]:
        probabilistic_updates = self.update(input)
        return Distribution(
            list(
                map(
                    lambda x: (fst(x), snd(x)(state)),
                    probabilistic_updates.distribution,
                )
            )
        )

    def to_z3(self):
        pass


class ParityAutomaton:
    def __init__(
        self,
        priorities: list[int],
        transitions: list[tuple[int, Guard, int]],
    ) -> None:
        self._states = range(len(priorities))
        self._priorities = priorities
        self._transitions = transitions

    @property
    def states(self):
        return self._states


class GuardedCommand:
    def __init__(self, guard, update) -> None:
        self._guard = guard
        self._update = update

    @property
    def guard(self):
        return self._guard

    @property
    def update(self):
        return self._update


class Scheduler:
    def __init__(self, vars: Variables) -> None:
        self._vars = vars

    def __call__(self, state: State) -> State:
        return state


class StochasticReactiveSystem:
    def __init__(
        self,
        local_vars: Variables,
        input_vars: Variables,
        init_set: Iterable[State],
        guarded_commands: list[GuardedCommand],
    ) -> None:
        self._init = init_set
        self._local_vars = local_vars
        self._input_vars = input_vars
        self._guarded_commands = guarded_commands

    @property
    def init(self):
        return self._init

    @property
    def local_vars(self):
        return self._local_vars

    @property
    def input_vars(self):
        return self._input_vars

    @property
    def guarded_commands(self):
        return self._guarded_commands

    def parallel_composition(self, other: Self):
        pass

    def interleave(self, other: Self):
        pass

    def product(self, automaton: ParityAutomaton):
        pass


class System:
    def __init__(
        self,
        reactive_system: StochasticReactiveSystem,
        automaton: ParityAutomaton,
    ) -> None:
        self._reactive_system = reactive_system.product(automaton)
        self._automaton = automaton

    @property
    def init(self):
        return self._reactive_system.init

    @property
    def local_vars(self):
        return self._reactive_system.local_vars

    @property
    def input_vars(self):
        return self._reactive_system.input_vars

    @property
    def guarded_commands(self):
        return self._reactive_system.guarded_commands

    @property
    def automaton(self):
        return self._automaton


class ParitySupermartingale:
    def __init__(self, system: System, property: Specification) -> None:
        self._system = system
        self._property = property

    @property
    def system(self):
        return self._system

    @property
    def property(self):
        return self._property

    def _invariant_init(self, invariant: PiecewiseLinearFunction):
        """
        (∀ init ∈ Init.)
            ⋁{q ∈ Q} (I(init, q) (∧ q==q))
        """
        tmp = list(map(lambda x: x, self.system.init))
        pass

    def _demonic_invariant_consecution(self, invariant: PiecewiseLinearFunction):
        pass

    def _demonic_drift_even(self, invariant: PiecewiseLinearFunction):
        pass

    def _demonic_drift_odd(self, invariant: PiecewiseLinearFunction):
        pass

    def demonic_verification(self, invariant: PiecewiseLinearFunction):
        pass

    def demonic_verification_and_invariant_synthesis(self):
        pass

    def _angelic_drift_even(self, invariant: PiecewiseLinearFunction):
        pass

    def _angelic_drift_odd(self, invariant: PiecewiseLinearFunction):
        pass

    def angelic_strategy_synthesis(self, invariant: PiecewiseLinearFunction):
        pass

    def angelic_strategy_and_invariant_synthesis(self):
        pass
