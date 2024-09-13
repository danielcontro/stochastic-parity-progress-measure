from sympy import Add, And, Eq, Matrix, Or, StrictGreaterThan, Symbol, zeros

from parity_supermartingale import ParityObjective, ParitySupermartingale
from reactive_module import (
    GuardedCommand,
    ReactiveModule,
)
from utils import SPLinearFunction

p = Symbol("p")
c = Symbol("c")
q = Symbol("q")

MAX = 65536

p_0 = Eq(p, 0)
p_1 = Eq(Add(p, -1), 0)
c_gt_0 = StrictGreaterThan(c, 0)
c_eq_0 = Eq(c, 0)
q_0 = Eq(q, 0)
q_1 = Eq(Add(q, -1), 0)
q_2 = Eq(Add(q, -2), 0)

init = (0, 0, 2)
vars = (p, c, q)
to_init: SPLinearFunction = zeros(3), Matrix([[0], [0], [2]])
to_proc: SPLinearFunction = zeros(3), Matrix([[1], [MAX], [0]])
decr: SPLinearFunction = (
    Matrix([[0, 0, 0], [0, 1, 0], [0, 0, 0]]),
    Matrix([[1], [-1], [0]]),
)
finish: SPLinearFunction = zeros(3), Matrix([[1], [0], [1]])

body: list[GuardedCommand] = [
    (p_0, [[(1, to_init)], [(0.1, to_proc), (0.9, to_init)]]),
    (
        And(p_1, c_gt_0),
        [[(0.8, to_init), (0.2, decr)]],
    ),
    (And(p_1, c_eq_0), [[(1, finish)]]),
]

system = ReactiveModule([init], vars, body)
spec: list[ParityObjective] = [
    Eq(1, 0),
    Eq(q, 0),
    Or(Eq(Add(q, -1), 0), Eq(Add(q, -2), 0)),
]

psm = ParitySupermartingale(system)
# psm.synthesize_dpa_based([0, 1, 2], spec)
print(psm.invariant_synthesis_and_verification([0, 1, 2], spec))
