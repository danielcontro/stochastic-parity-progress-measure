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

from sympy.logic.boolalg import Boolean
from reactive_module import ReactiveModule
from stochastic_parity_progress_measure import SPPM, ParityObjective

# module M
#   counter : [0..MAX_COUNTER] init MAX_COUNTER;
#   processing : bool init false;
#   [] processing = false -> 0.5 : (processing' = true) + 0.5 : (processing' = false);
#   [] processing = true & counter > 0 -> 0.8 : counter_decr + 0.2 : reset;
#   [] processing = true & counter > 0 -> 1 : reset;
#   [] processing = true & counter = 0 -> 1 : reset;
# endmodule

ticking = Symbol("ticking")
counter = Symbol("counter")
MAX_COUNTER = 65536.0
pvars = (ticking, counter)

# Mutually exclusive guards as conjunction of inequalities/equalities
not_ticking = Eq(ticking, 0)
ticking_gt_0 = And(Eq(Add(ticking, -1), 0), StrictGreaterThan(counter, 0))
ticking_eq_0 = And(Eq(Add(ticking, -1), 0), Eq(counter, 0))

init = (0.0, MAX_COUNTER)

wait_req = (eye(2), zeros(2, 1))
to_proc = (Matrix([[0, 0], [0, 1]]), Matrix([[1], [0]]))
reset = (zeros(2, 2), Matrix([[0.0], [MAX_COUNTER]]))
counter_decr = (eye(2), Matrix([[0], [-1]]))

body = [
    # p = false -> 0.5 : to_proc; 0.5 : id
    (not_ticking, [[(0.5, to_proc), (0.5, reset)]]),
    # p = true & c > 0 -> [0.8 : counter_decr, 0.2: reset], [1: reset]
    (ticking_gt_0, [[(0.8, counter_decr), (0.2, reset)], [(1, reset)]]),
    # p = true & c = 0 -> 1: reset
    (ticking_eq_0, [[(1, reset)]]),
]

# V_j in DNF form
gf_waiting_requests: list[ParityObjective] = [
    Eq(ticking, 0),
    And(Eq(ticking - 1, 0), GreaterThan(counter, 0)),
]

rm = ReactiveModule(init, pvars, body)
sppm = SPPM(rm, gf_waiting_requests)

print("Starting synthesising")
start_time = time()
alpha = sppm.synthesize()
elapsed = time() - start_time
print("Alpha:", alpha)
print("Elapsed time:", elapsed)
