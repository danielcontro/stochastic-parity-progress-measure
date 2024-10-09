from typing import Optional
from sympy import Matrix, Symbol

from boolean_algebra import DNF


State = tuple[float, ...]
Variable = Symbol
Init = list[State]


class Update:
    def __init__(self, a: Matrix, b: Matrix) -> None:
        self._a = a
        self._b = b

    @property
    def a(self) -> Matrix:
        return self._a

    @property
    def b(self) -> Matrix:
        return self._b

    def to_z3(self):
        pass


class StocUpdate:
    def __init__(self, prob: float, update: Update) -> None:
        assert (0 <= prob) and (prob <= 1)
        self._prob = prob
        self._update = update

    @property
    def prob(self) -> float:
        return self._prob

    @property
    def update(self) -> Update:
        return self._update


class Command:
    def __init__(
        self, label: Optional[str], guard: DNF, update: list[StocUpdate]
    ) -> None:
        self._label = label
        self._guard = guard
        assert sum(map(lambda u: u.prob, update)) == 1
        self._update = update

    @property
    def label(self) -> Optional[str]:
        return self._label

    @property
    def guard(self) -> DNF:
        return self._guard

    @property
    def update(self) -> list[StocUpdate]:
        return self._update


class Automaton:
    pass


Action = list[int]


class Module:
    def _compute_actions(self) -> list[Action]:
        actions = []
        for n in range(2 ** len(self.commands)):
            action: Action = [int(i) for i in f"{n:0{len(self.commands)}b}"]
            for i, c in enumerate(self.commands):
                if action[i]:
                    pass

    def __init__(
        self,
        init: Init,
        vars: list[Variable],
        commands: list[Command],
        actions: Optional[list[Action]],
    ) -> None:
        self._init = init
        self._vars = vars
        self._commands = commands

    @property
    def vars(self) -> list[Variable]:
        return self._vars

    @property
    def init(self) -> Init:
        return self._init

    @property
    def commands(self) -> list[Command]:
        return self._commands


class System:
    def __init__(self, modules: list[Module], automaton: Automaton):
        self._vars = []
        self._commands = list(map(lambda m: m.commands, modules))
        self._modules = modules
        # Sync automaton with all commands

    @property
    def vars(self) -> list[Symbol]:
        return list(set().union(*[m.vars for m in self._modules]))
