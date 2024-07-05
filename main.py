#!/usr/bin/env python3

from sympy import Add, And, Eq, LessThan, Matrix, Or, StrictGreaterThan, Symbol
from sympy.logic.boolalg import Boolean
from reactive_module import ReactiveModule
from stochastic_parity_progress_measure import SPPM

x = Symbol("x")
c = Symbol("c")
pvars = (x, c)

# Mutually exclusive guards as conjunction of inequalities/equalities
guards = [Eq(Add(c, -1), 0), Eq(c, 0)]
updates = [
    [
        (Matrix([[2, 0], [0, 0]]), Matrix([[0], [1]])),
        (Matrix([[1, 0], [0, 0]]), Matrix([[0], [0]])),
    ],
    [(Matrix([[1, 0], [0, 0]]), Matrix([[-1], [0]]))],
]

init = (1.0, 1.0)
# c==1 -> 0.5 : 2x,1; 0.5 : x,0,
body = [
    (guards[0], [[(0.5, updates[0][0]), (0.5, updates[0][1])]]),
    # c==0 -> 1 : x-1,0
    (guards[1], [[(1, updates[1][0])]]),
]

# V_j in DNF form
v: list[Boolean] = [
    And(Eq(c, 0), LessThan(x, 0)),
    Or(Eq(Add(c, -1), 0), And(Eq(c, 0), StrictGreaterThan(x, 0))),
]

rm = ReactiveModule(init, pvars, body)
sppm = SPPM(rm, v)

alpha = sppm.synthesize()
print("Alpha:", alpha)
