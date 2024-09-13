from time import time

from sympy import (
    And,
    GreaterThan,
    LessThan,
    Or,
    Eq,
    Add,
    StrictGreaterThan,
    StrictLessThan,
    Symbol,
    Matrix,
    zeros,
)

from parity_supermartingale import ParityObjective, ParitySupermartingale
from reactive_module import GuardedCommand, ReactiveModule

c = Symbol("c")
x = Symbol("x")
q = Symbol("q")

vars = (c, x, q)

init = (1, 1, 0)

c_0 = Eq(c, 0)
c_1 = Eq(Add(c, -1), 0)
x_ge_10 = GreaterThan(Add(x, -10), 0)
x_le_0 = LessThan(x, 0)
x_g_0 = StrictGreaterThan(x, 0)
x_l_10 = StrictLessThan(Add(x, -10), 0)
q_0 = Eq(q, 0)
q_1 = Eq(Add(q, -1), 0)
q_2 = Eq(Add(q, -2), 0)

body: list[GuardedCommand] = [
    (
        And(c_0, x_ge_10),
        [
            [
                (
                    1,
                    (
                        Matrix([[0, 0, 0], [0, 1, 0], [0, 0, 0]]),
                        Matrix([[0], [-1], [0]]),
                    ),
                ),
            ]
        ],
    ),
    (
        And(c_0, x_le_0),
        [
            [
                (
                    1,
                    (
                        Matrix([[0, 0, 0], [0, 1, 0], [0, 0, 0]]),
                        Matrix([[0], [-1], [1]]),
                    ),
                ),
            ]
        ],
    ),
    (
        And(c_0, x_g_0, x_l_10),
        [
            [
                (
                    1,
                    (
                        Matrix([[0, 0, 0], [0, 1, 0], [0, 0, 0]]),
                        Matrix([[0], [-1], [2]]),
                    ),
                ),
            ]
        ],
    ),
    (
        And(c_1, x_ge_10),
        [
            [
                (
                    0.5,
                    (
                        Matrix([[0, 0, 0], [0, 2, 0], [0, 0, 0]]),
                        Matrix([[1], [0], [0]]),
                    ),
                ),
                (
                    0.5,
                    (zeros(3), zeros(3, 1)),
                ),
            ]
        ],
    ),
    (
        And(c_1, x_le_0),
        [
            [
                (
                    0.5,
                    (
                        Matrix([[0, 0, 0], [0, 2, 0], [0, 0, 0]]),
                        Matrix([[1], [0], [1]]),
                    ),
                ),
                (
                    0.5,
                    (
                        zeros(3),
                        Matrix([[0], [0], [1]]),
                    ),
                ),
            ]
        ],
    ),
    (
        And(c_1, x_g_0, x_l_10),
        [
            [
                (
                    0.5,
                    (
                        Matrix([[0, 0, 0], [0, 2, 0], [0, 0, 0]]),
                        Matrix([[1], [0], [2]]),
                    ),
                ),
                (
                    0.5,
                    (
                        zeros(3),
                        Matrix([[0], [0], [2]]),
                    ),
                ),
            ]
        ],
    ),
]

system = ReactiveModule([init], vars, body)
psm = ParitySupermartingale(system)

objectives: list[ParityObjective] = [q_0, q_1, q_2]

print("Starting synthesising")
start_time = time()
lex_psm = psm.invariant_synthesis_and_verification([0, 1, 2], objectives)
elapsed = time() - start_time
print("Elapsed time:", elapsed)
print("PSM:", lex_psm)
