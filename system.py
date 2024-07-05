from reactive_module import ReactiveModule
from sympy import Symbol


class System:
    def __init__(self, modules: list[ReactiveModule]):
        self._modules = modules

    @property
    def vars(self) -> list[Symbol]:
        return list(set().union(*[m.vars for m in self._modules]))

    # def transitions(
    #     self, state: list[float]
    # ) -> list[tuple[ReactiveModule, list[float]]]:
    #     return [(m, m.transition(state)) for m in self._modules if m.eval_guard(state)]
