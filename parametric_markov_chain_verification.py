#!/usr/bin/env python3

from time import time

from stochastic_parity_progress_measure import SPPM, ParityObjective

from reactive_module import Guard, ReactiveModule, Transition

from sympy import (
    And,
    Eq,
    Add,
    Or,
    Matrix,
    StrictGreaterThan,
    StrictLessThan,
    Symbol,
    eye,
    zeros,
)

s = Symbol("state")
q = Symbol("q")
vars = (s, q)
init = (0.0, 0.0)
s4_q_inc = eye(2), Matrix([[0], [1]])
s4_dec_q_inc = eye(2), Matrix([[-1], [1]])
s0_q_inc = eye(2), Matrix([[0], [1]])
s0_inc_q_inc = eye(2), Matrix([[1], [1]])
s0_q_res = zeros(2), Matrix([[0], [0]])
s0_inc_q_res = zeros(2), Matrix([[1], [0]])

sq_inc = eye(2), Matrix([[1], [1]])
s_dec_q_inc = eye(2), Matrix([[-1], [1]])
sq_dec = eye(2), Matrix([[-1], [-1]])
s_inc_q_dec = eye(2), Matrix([[1], [-1]])
s_inc = eye(2), Matrix([[1], [0]])
s_dec = eye(2), Matrix([[-1], [0]])


body: list[tuple[Guard, list[list[Transition]]]] = [
    (
        And(Eq(Add(s, -4), 0), Eq(q, 0)),
        # [[(1, s4_dec_q_inc)]],
        [[(1, s4_q_inc)]],
    ),  # s = 4, q = 0
    (
        And(Eq(Add(s, -4), 0), Eq(Add(q, -1), 0)),
        [[(1, s4_dec_q_inc)]],
        # [(1, s4_q_inc)]],
    ),  # s = 4, q = 1
    (
        And(Eq(Add(s, -4), 0), Eq(Add(q, -2), 0)),
        [[(1, s4_dec_q_inc)]],
        # [(1, s4_q_inc)]],
    ),  # s = 4, q = 2
    (
        And(Eq(s, 0), Eq(q, 0)),
        # [[(1, s0_q_inc)],
        [[(1, s0_inc_q_inc)]],
    ),  # s = 0, q = 0
    (
        And(Eq(s, 0), Eq(Add(q, -2), 0)),
        [[(1, s0_q_inc)]],
        # [[(1, s0_inc_q_inc)]],
    ),  # s = 0, q = 2
    (
        And(Eq(s, 0), Eq(Add(q, -3), 0)),
        # [[(1, s0_q_res)]],
        [[(1, s0_inc_q_res)]],
    ),  # s = 0, q = 3
    (
        And(StrictLessThan(s, 4), StrictGreaterThan(s, 0), Eq(q, 0)),
        # [[(1, s_dec_q_inc)]],
        [[(1, sq_inc)]],
    ),  # 0 < s < 4, q = 0
    (
        And(StrictLessThan(s, 4), StrictGreaterThan(s, 0), Eq(Add(q, -2), 0)),
        [[(1, s_dec_q_inc)]],
        # [[(1, sq_inc)]],
    ),  # 0 < s < 4, q = 2
    (
        And(StrictLessThan(s, 4), Eq(Add(q, -1), 0)),
        [[(1, s_inc)]],
    ),  # s < 4, q = 1
    (
        And(StrictGreaterThan(s, 0), Eq(Add(q, -3), 0)),
        [[(1, s_dec)]],
    ),  # s > 0, q = 3
]

rm = ReactiveModule([init], vars, body)

gf_s0_gf_s4: list[ParityObjective] = [
    Or(And(Eq(q, 0)), And(Eq(Add(q, -2), 0))),
    Or(And(Eq(Add(q, -1), 0)), And(Eq(Add(q, -3), 0))),
]

q_val = [0, 1, 2, 3]

sppm = SPPM(rm)

print("Starting synthesising")
start_time = time()
alpha = sppm.synthesize_dpa_based(q_val, gf_s0_gf_s4)
elapsed = time() - start_time
[print("Alpha:", alpha_i) for alpha_i in alpha]
print("Elapsed time:", elapsed)

# s = 4, q == 0 || q == 1 || q==2  -> [s' = 3, q' = q+1], [s' = 4, q' = q+1]
# s = 0, q == 0 || q==2 -> [s' = 0, q' = q+1], [s' = 1, q' = q+1]
# s = 0, q == 3  -> [s' = 0, q' = 0], [s' = 1, q' = 0]
# s != 0, s != 4, q == 0 || q==2-> [s' = s-1, q' = q+1], [s' = s+1, q' = q+1]
#
# s > 0, q == 3 -> s' = s-1, q' = q
# s < 4, q == 1 -> s' = s+1, q' = q


# q = 0 -> q' = 1
# s = 4, k = -1, q == 0  -> 3  -> s' = 3, q' = 1
# s = 4, k =  1, q == 0  -> 4  -> s' = 4, q' = 1
# s = 3, k =  1, q == 0  -> 4  -> s' = 4, q' = 1
# s = 3, k = -1, q == 0  -> 2  -> s' = 2, q' = 1
# s = 2, k =  1, q == 0  -> 3  -> s' = 3, q' = 1
# s = 2, k = -1, q == 0  -> 1  -> s' = 1, q' = 1
# s = 1, k =  1, q == 0  -> 2  -> s' = 2, q' = 1
# s = 1, k = -1, q == 0  -> 0  -> s' = 0, q' = 1
# s = 0, k = -1, q == 0  -> -1 -> s' = 0, q' = 1
# s = 0, k =  1, q == 0  -> 1  -> s' = 1, q' = 1
#
# s = 4, k = -1, q == 2  -> 3  -> s' = 3, q' = 3
# s = 4, k =  1, q == 2  -> 4  -> s' = 4, q' = 3
# s = 3, k =  1, q == 2  -> 4  -> s' = 4, q' = 3
# s = 3, k = -1, q == 2  -> 2  -> s' = 2, q' = 3
# s = 2, k =  1, q == 2  -> 3  -> s' = 3, q' = 3
# s = 2, k = -1, q == 2  -> 1  -> s' = 1, q' = 3
# s = 1, k =  1, q == 2  -> 2  -> s' = 2, q' = 3
# s = 1, k = -1, q == 2  -> 0  -> s' = 0, q' = 3
# s = 0, k = -1, q == 2  -> -1 -> s' = 0, q' = 3
# s = 0, k =  1, q == 2  -> 1  -> s' = 1, q' = 3
#
#
# s = 4, k = -1, q == 1  -> 3  -> s' = 3, q' = 2
# s = 4, k =  1, q == 1  -> 4  -> s' = 4, q' = 2
#
#
# s = 0, k = -1, q == 3  -> -1 -> s' = 0, q' = 0
# s = 0, k =  1, q == 3  -> 1  -> s' = 1, q' = 0
#
#
# q Loop
#
#
# s = 4, k = -1, q == 3  -> 3  -> s' = 3, q' = q +
# s = 3, k = -1, q == 3  -> 2  -> s' = 2, q' = q +
# s = 2, k = -1, q == 3  -> 1  -> s' = 1, q' = q +
# s = 1, k = -1, q == 3  -> 0  -> s' = 0, q' = q +
#
# s = 3, k =  1, q == 1  -> 4  -> s' = 4, q' = q +
# s = 2, k =  1, q == 1  -> 3  -> s' = 3, q' = q +
# s = 1, k =  1, q == 1  -> 2  -> s' = 2, q' = q +
# s = 0, k =  1, q == 1  -> 1  -> s' = 1, q' = q +
#
#
# s = 4, k =  1, q == 3  -> 4  -> id             -
# s = 3, k =  1, q == 3  -> 4  -> s' = 4, q' = q -
# s = 3, k = -1, q == 1  -> 2  -> s' = 2, q' = q -
# s = 2, k =  1, q == 3  -> 3  -> s' = 3, q' = q -
# s = 2, k = -1, q == 1  -> 1  -> s' = 1, q' = q -
# s = 1, k =  1, q == 3  -> 2  -> s' = 2, q' = q -
# s = 1, k = -1, q == 1  -> 0  -> s' = 0, q' = q -
# s = 0, k = -1, q == 1  -> -1 -> id             -
