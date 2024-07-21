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
from stochastic_parity_progress_measure import SPPM, ParityObjective

# module M
#   ticking  : bool init false;
#   counter     : [0..MAX_COUNTER] init 0;
#   q           : [0..1] init 0;
#   [] ticking = false ->
#       0.5 : (ticking' = true, counter' = MAX_COUNTER, q' = 1) +
#       0.5 : (ticking' = false, counter' = 0, q' = 0);
#   [] ticking = true & counter > 0 ->
#       0.8 : (counter' = counter - 1) +
#       0.2 : (ticking' = false, counter' = 0, q' = 0);
#   [] ticking = true & counter > 0 ->
#       1 : (ticking' = false, counter' = 0, q' = 0);
#   [] ticking = true & counter = 0 ->
#       1 : (ticking' = false, counter' = 0, q' = 0);
# endmodule

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
reset = (zeros(3), Matrix([[0.0], [MAX_COUNTER], []]))
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
sppm = SPPM(rm, q, gf_waiting_requests)

print("Starting synthesising")
start_time = time()
alpha = sppm.synthesize()
elapsed = time() - start_time
print("Alpha:", alpha)
print("Elapsed time:", elapsed)
