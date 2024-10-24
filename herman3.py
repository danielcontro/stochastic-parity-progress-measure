import itertools
import os
import time

from antlr4 import CommonTokenStream, FileStream
from sympy import (
    Add,
    And,
    Eq,
    GreaterThan,
    LessThan,
    Matrix,
    Symbol,
    ones,
    symbols,
    zeros,
)

from parity_supermartingale import (
    ParitySupermartingale,
    pretty_lin_lex_psm,
    pretty_state_based_lin_function,
)
from reactive_module import (
    Guard,
    GuardedCommand,
    NonDeterministicStochasticUpdate,
    ReactiveModule,
    StochasticUpdate,
)

from antlr.PrismLexer import PrismLexer
from antlr.PrismParser import PrismParser
from transpiler import PrismEval
from utils import (
    negate_constraint,
    var_eq_val,
    var_gt_val,
    var_lt_val,
    var_ge_val,
    var_le_val,
    var_ne_val,
)

# Experiments setup
RUNS = 5

output_dir = "./results/herman/3"
os.makedirs(output_dir, exist_ok=True)
elapsed_times = []

for RUN in range(RUNS):
    print(f"Starting run {RUN + 1}")
    start_time = time.time()

    file_name = "./prism/case_studies/herman/herman3.prism"
    input_stream = FileStream(file_name)
    lexer = PrismLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = PrismParser(token_stream)
    tree = parser.file_()
    visitor = PrismEval()
    module: ReactiveModule = visitor.visit(tree)
    # manually setting module's Init set
    module.init = [
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0),
        (0.0, 1.0, 1.0),
        (1.0, 0.0, 0.0),
        (1.0, 0.0, 1.0),
        (1.0, 1.0, 0.0),
        (1.0, 1.0, 1.0),
    ]

    q_init = [(1.0,)]
    q = Symbol("q")
    x1 = Symbol("x1")
    x2 = Symbol("x2")
    x3 = Symbol("x3")
    g_to_q1_1 = And(
        var_ne_val(x1, x2), var_ne_val(x1, x3), var_ne_val(x2, x3), var_eq_val(q, 1)
    )
    g_to_q1_2 = And(var_eq_val(x1, x2), var_eq_val(x1, x3), var_eq_val(q, 1))
    g_to_q0_1 = And(var_eq_val(x1, x2), var_ne_val(x1, x3), var_eq_val(q, 1))
    g_to_q0_2 = And(var_eq_val(x2, x3), var_ne_val(x1, x3), var_eq_val(q, 1))
    g_to_q0_3 = And(var_eq_val(x1, x3), var_ne_val(x1, x2), var_eq_val(q, 1))
    g_loop = var_eq_val(q, 0)

    q_to_0: NonDeterministicStochasticUpdate = [
        [
            (
                1,
                (
                    zeros(1),
                    zeros(1),
                ),
            )
        ]
    ]
    q_to_1: NonDeterministicStochasticUpdate = [
        [
            (
                1,
                (
                    zeros(1),
                    ones(1),
                ),
            )
        ]
    ]
    q_body = [
        GuardedCommand([], g_to_q1_1, q_to_1),
        GuardedCommand([], g_to_q1_2, q_to_1),
        GuardedCommand([], g_to_q0_1, q_to_0),
        GuardedCommand([], g_to_q0_2, q_to_0),
        GuardedCommand([], g_to_q0_3, q_to_0),
        GuardedCommand([], g_loop, q_to_0),
    ]
    parity_automaton = ReactiveModule(q_init, (q,), q_body)
    [print(gc.guard, "->", gc.update) for gc in module.body]
    system = module.add_parity_automaton(parity_automaton)

    psm = ParitySupermartingale(system)

    q_states = [0, 1]

    parity_objectives = [var_eq_val(q, 1), var_eq_val(q, 0)]

    # lin_lex_psm = psm.verification(q_states, parity_objectives)
    lin_lex_psm, invariant = psm.invariant_synthesis_and_verification(
        q_states, parity_objectives
    )

    elapsed_times.append(time.time() - start_time)
    print("Time taken: ", elapsed_times[-1])
    # TODO: Function pretty printing and saving
    lin_lex_psm_str = pretty_lin_lex_psm(system.vars, lin_lex_psm)
    invariant_str = pretty_state_based_lin_function(system.vars, invariant)
    print("LinLexPSM: [")
    for lin_psm in lin_lex_psm_str:
        print("    {")
        for state, lin_psm in lin_psm.items():
            print(f"        {state}: {lin_psm},")
        print("    },")
    print("]")
    print("Invariant: {")
    [print(f"    {state}: {lin_f},") for state, lin_f in invariant_str.items()]
    print("}")
    with open(f"{output_dir}/run_{RUN}.txt", "w") as f:
        f.write("Result: ")
        f.write(str(lin_lex_psm_str))
        f.write(str(invariant_str))
        f.write(f"\nTime taken: {elapsed_times[-1]}")

with open(f"{output_dir}/times.txt", "w") as f:
    f.write("Times: ")
    f.write(str(elapsed_times))
    f.write(f"\nAverage time: {sum(elapsed_times) / len(elapsed_times)}")
