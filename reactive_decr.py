#!/usr/bin/env python3

from time import time
from sympy import (
    Add,
    And,
    Eq,
    GreaterThan,
    LessThan,
    Matrix,
    Or,
    StrictGreaterThan,
    Symbol,
    eye,
    zeros,
)

from reactive_module import ReactiveModule
from parity_supermartingale import ParitySupermartingale, ParityObjective

p = Symbol("p")
c = Symbol("c")
dpa = Symbol("q")
MAX_COUNTER = 65536.0
pvars = (p, c, dpa)

# Mutually exclusive guards as conjunction of inequalities/equalities
not_p = Eq(p, 0)
processing = Eq(Add(p, -1), 0)

p_gt_0 = And(processing, StrictGreaterThan(c, 0))
p_eq_0 = And(processing, Eq(c, 0))

init = [(0.0, MAX_COUNTER, 0)]

to_proc = (zeros(3), Matrix([[1], [MAX_COUNTER], [1]]))
reset = (zeros(3), Matrix([[0.0], [MAX_COUNTER], [0]]))
counter_decr = (Matrix([[0, 0, 0], [0, 1, 0], [0, 0, 0]]), Matrix([[1], [-1], [0]]))

body = [
    # p = false -> 0.5 : to_proc; 0.5 : id
    (not_p, [[(0.5, to_proc), (0.5, reset)]]),
    # p = true & c > 0 -> [0.8 : counter_decr, 0.2: reset], [1: reset]
    (p_gt_0, [[(0.8, counter_decr), (0.2, reset)], [(1, reset)]]),
    # p = true & c = 0 -> 1: reset
    (p_eq_0, [[(1, reset)]]),
]

# V_j in DNF form
gf_waiting_requests: list[ParityObjective] = [Eq(dpa, 0), Eq(Add(dpa, -1), 0)]

q = [0, 1]

rm = ReactiveModule(init, pvars, body)
psm = ParitySupermartingale(rm)

print("Starting synthesising")
start_time = time()
lex_psm = psm.verification(q, gf_waiting_requests)
elapsed = time() - start_time
print("PSM:", lex_psm)
print("Elapsed time:", elapsed)
