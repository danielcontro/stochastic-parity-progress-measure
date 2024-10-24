import itertools
import os
import time

from sympy import Add, And, Eq, GreaterThan, LessThan, Matrix, Symbol, symbols, zeros

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

from utils import (
    negate_constraint,
    var_eq_val,
    var_gt_val,
    var_lt_val,
    var_ge_val,
    var_le_val,
    var_ne_val,
)

# PRISM module
"""
const int N = 6;
const int K;
const int range = (2 * (K + 1)) * N;
const int counter_init = (K + 1) * N;
const int left = N;
const int right = (2 * (K + 1)) * N - N;
global counter : [0 .. range] init counter_init;

module process1process2process3process4process5process6
    pc1 : [0 .. 3];
    coin1 : [0 .. 1];
    pc2 : [0 .. 3];
    coin2 : [0 .. 1];
    pc3 : [0 .. 3];
    coin3 : [0 .. 1];
    pc4 : [0 .. 3];
    coin4 : [0 .. 1];
    pc5 : [0 .. 3];
    coin5 : [0 .. 1];
    pc6 : [0 .. 3];
    coin6 : [0 .. 1];

    [] pc1 = 0 -> 0.5:(coin1' = 0) & (pc1' = 1) + 0.5:(coin1' = 1) & (pc1' = 1);
    [] (pc1 = 1 & coin1 = 0) & counter > 0 -> (counter' = counter - 1) & (pc1' = 2) & (coin1' = 0);
    [] (pc1 = 1 & coin1 = 1) & counter < range -> (counter' = counter + 1) & (pc1' = 2) & (coin1' = 0);
    [] pc1 = 2 & counter <= left -> (pc1' = 3) & (coin1' = 0);
    [] pc1 = 2 & counter >= right -> (pc1' = 3) & (coin1' = 1);
    [] (pc1 = 2 & counter > left) & counter < right -> (pc1' = 0);
    [done] pc1 = 3 & (pc2 = 3 & (pc3 = 3 & (pc4 = 3 & (pc5 = 3 & pc6 = 3)))) -> (pc1' = 3) & (pc2' = 3) & (pc3' = 3) & (pc4' = 3) & (pc5' = 3) & (pc6' = 3);
    [] pc2 = 0 -> 0.5:(coin2' = 0) & (pc2' = 1) + 0.5:(coin2' = 1) & (pc2' = 1);
    [] (pc2 = 1 & coin2 = 0) & counter > 0 -> (counter' = counter - 1) & (pc2' = 2) & (coin2' = 0);
    [] (pc2 = 1 & coin2 = 1) & counter < range -> (counter' = counter + 1) & (pc2' = 2) & (coin2' = 0);
    [] pc2 = 2 & counter <= left -> (pc2' = 3) & (coin2' = 0);
    [] pc2 = 2 & counter >= right -> (pc2' = 3) & (coin2' = 1);
    [] (pc2 = 2 & counter > left) & counter < right -> (pc2' = 0);
    [] pc3 = 0 -> 0.5:(coin3' = 0) & (pc3' = 1) + 0.5:(coin3' = 1) & (pc3' = 1);
    [] (pc3 = 1 & coin3 = 0) & counter > 0 -> (counter' = counter - 1) & (pc3' = 2) & (coin3' = 0);
    [] (pc3 = 1 & coin3 = 1) & counter < range -> (counter' = counter + 1) & (pc3' = 2) & (coin3' = 0);
    [] pc3 = 2 & counter <= left -> (pc3' = 3) & (coin3' = 0);
    [] pc3 = 2 & counter >= right -> (pc3' = 3) & (coin3' = 1);
    [] (pc3 = 2 & counter > left) & counter < right -> (pc3' = 0);
    [] pc4 = 0 -> 0.5:(coin4' = 0) & (pc4' = 1) + 0.5:(coin4' = 1) & (pc4' = 1);
    [] (pc4 = 1 & coin4 = 0) & counter > 0 -> (counter' = counter - 1) & (pc4' = 2) & (coin4' = 0);
    [] (pc4 = 1 & coin4 = 1) & counter < range -> (counter' = counter + 1) & (pc4' = 2) & (coin4' = 0);
    [] pc4 = 2 & counter <= left -> (pc4' = 3) & (coin4' = 0);
    [] pc4 = 2 & counter >= right -> (pc4' = 3) & (coin4' = 1);
    [] (pc4 = 2 & counter > left) & counter < right -> (pc4' = 0);
    [] pc5 = 0 -> 0.5:(coin5' = 0) & (pc5' = 1) + 0.5:(coin5' = 1) & (pc5' = 1);
    [] (pc5 = 1 & coin5 = 0) & counter > 0 -> (counter' = counter - 1) & (pc5' = 2) & (coin5' = 0);
    [] (pc5 = 1 & coin5 = 1) & counter < range -> (counter' = counter + 1) & (pc5' = 2) & (coin5' = 0);
    [] pc5 = 2 & counter <= left -> (pc5' = 3) & (coin5' = 0);
    [] pc5 = 2 & counter >= right -> (pc5' = 3) & (coin5' = 1);
    [] (pc5 = 2 & counter > left) & counter < right -> (pc5' = 0);
    [] pc6 = 0 -> 0.5:(coin6' = 0) & (pc6' = 1) + 0.5:(coin6' = 1) & (pc6' = 1);
    [] (pc6 = 1 & coin6 = 0) & counter > 0 -> (counter' = counter - 1) & (pc6' = 2) & (coin6' = 0);
    [] (pc6 = 1 & coin6 = 1) & counter < range -> (counter' = counter + 1) & (pc6' = 2) & (coin6' = 0);
    [] pc6 = 2 & counter <= left -> (pc6' = 3) & (coin6' = 0);
    [] pc6 = 2 & counter >= right -> (pc6' = 3) & (coin6' = 1);
    [] (pc6 = 2 & counter > left) & counter < right -> (pc6' = 0);
endmodule
"""

# PRISM property
"""
label "finished" = ((((pc1 = 3 & pc2 = 3) & pc3 = 3) & pc4 = 3) & pc5 = 3) & pc6 = 3;
P>=1 [ F "finished" ]
"""

KS = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
for K in KS:
    # Experiments setup
    RUNS = 5

    output_dir = f"./results/consensus6_k{K}"
    os.makedirs(output_dir, exist_ok=True)
    elapsed_times = []

    for RUN in range(RUNS):
        print(f"Starting run {RUN + 1}")
        start_time = time.time()

        # Constants
        N = 2
        RANGE = 2 * (K + 1) * N
        COUNTER_INIT = float((K + 1) * N)
        LEFT = N
        RIGHT = 2 * (K + 1) * N - N

        # System variables
        counter = symbols("counter")
        pc1, c1 = symbols("pc1 coin1")
        pc2, c2 = symbols("pc2 coin2")
        pc3, c3 = symbols("pc3 coin3")
        pc4, c4 = symbols("pc4 coin4")
        pc5, c5 = symbols("pc5 coin5")
        pc6, c6 = symbols("pc6 coin6")
        q = symbols("q")

        vars = (counter, pc1, c1, pc2, c2, pc3, c3, pc4, c4, pc5, c5, pc6, c6, q)

        def process(pc: Symbol, coin: Symbol):
            pc_idx = vars.index(pc)
            coin_idx = vars.index(coin)
            q_idx = vars.index(q)
            vars_idx = [pc_idx, coin_idx]
            exclude_idx = vars_idx + [q_idx]
            return [
                GuardedCommand(
                    [],
                    var_eq_val(pc, 0),
                    [
                        [
                            (
                                0.5,
                                (
                                    Matrix(
                                        len(vars),
                                        len(vars),
                                        lambda i, j: 1
                                        if i == j and i not in exclude_idx
                                        else 0,
                                    ),
                                    Matrix(
                                        len(vars),
                                        1,
                                        lambda i, _: 1 if i == pc_idx else 0,
                                    ),
                                ),
                            ),
                            (
                                0.5,
                                (
                                    Matrix(
                                        len(vars),
                                        len(vars),
                                        lambda i, j: 1
                                        if i == j and i not in exclude_idx
                                        else 0,
                                    ),
                                    Matrix(
                                        len(vars),
                                        1,
                                        lambda i, _: 1 if i in vars_idx else 0,
                                    ),
                                ),
                            ),
                        ]
                    ],
                ),
                GuardedCommand(
                    [],
                    And(var_eq_val(pc, 1), var_eq_val(coin, 0), var_gt_val(counter, 0)),
                    [
                        [
                            (
                                1,
                                (
                                    Matrix(
                                        len(vars),
                                        len(vars),
                                        lambda i, j: 1
                                        if i == j and i not in exclude_idx
                                        else 0,
                                    ),
                                    Matrix(
                                        len(vars),
                                        1,
                                        lambda i, _: -1
                                        if i == 0
                                        else (2 if i == pc_idx else 0),
                                    ),
                                ),
                            )
                        ]
                    ],
                ),
                GuardedCommand(
                    [],
                    And(
                        var_eq_val(pc, 1),
                        var_eq_val(coin, 1),
                        var_lt_val(counter, RANGE),
                    ),
                    [
                        [
                            (
                                1,
                                (
                                    Matrix(
                                        len(vars),
                                        len(vars),
                                        lambda i, j: 1
                                        if i == j and i not in exclude_idx
                                        else 0,
                                    ),
                                    Matrix(
                                        len(vars),
                                        1,
                                        lambda i, _: 1
                                        if i == 0
                                        else (2 if i == pc_idx else 0),
                                    ),
                                ),
                            )
                        ]
                    ],
                ),
                GuardedCommand(
                    [],
                    And(var_eq_val(pc, 2), var_le_val(counter, LEFT)),
                    [
                        [
                            (
                                1,
                                (
                                    Matrix(
                                        len(vars),
                                        len(vars),
                                        lambda i, j: 1
                                        if i == j and i not in exclude_idx
                                        else 0,
                                    ),
                                    Matrix(
                                        len(vars),
                                        1,
                                        lambda i, _: 3 if i == pc_idx else 0,
                                    ),
                                ),
                            )
                        ]
                    ],
                ),
                GuardedCommand(
                    [],
                    And(var_eq_val(pc, 2), var_ge_val(counter, RIGHT)),
                    [
                        [
                            (
                                1,
                                (
                                    Matrix(
                                        len(vars),
                                        len(vars),
                                        lambda i, j: 1
                                        if i == j and i not in exclude_idx
                                        else 0,
                                    ),
                                    Matrix(
                                        len(vars),
                                        1,
                                        lambda i, _: 3
                                        if i == pc_idx
                                        else (1 if i == coin_idx else 0),
                                    ),
                                ),
                            )
                        ]
                    ],
                ),
                GuardedCommand(
                    [],
                    And(
                        var_eq_val(pc, 2),
                        var_gt_val(counter, LEFT),
                        var_lt_val(counter, RIGHT),
                    ),
                    [
                        [
                            (
                                1,
                                (
                                    Matrix(
                                        len(vars),
                                        len(vars),
                                        lambda i, j: 1
                                        if i == j and i not in [pc_idx, q_idx]
                                        else 0,
                                    ),
                                    zeros(len(vars), 1),
                                ),
                            )
                        ]
                    ],
                ),
            ]

        gc7 = GuardedCommand(
            [],
            And(
                var_eq_val(pc1, 3),
                var_eq_val(pc2, 3),
                var_eq_val(pc3, 3),
                var_eq_val(pc4, 3),
                var_eq_val(pc5, 3),
                var_eq_val(pc6, 3),
            ),
            [
                [
                    (
                        1,
                        (
                            Matrix(
                                len(vars),
                                len(vars),
                                lambda i, j: 1
                                if i == j and i in [0, 2, 4, 6, 8, 10, 12]
                                else 0,
                            ),
                            Matrix(
                                len(vars),
                                1,
                                lambda i, _: 1
                                if i == vars.index(q)
                                else (3 if i in [1, 3, 5, 7, 9, 11] else 0),
                            ),
                        ),
                    )
                ]
            ],
        )

        system = ReactiveModule(
            [(COUNTER_INIT, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)],
            vars,
            process(pc1, c1)
            + process(pc2, c2)
            + process(pc3, c3)
            + process(pc4, c4)
            + process(pc5, c5)
            + process(pc6, c6)
            + [gc7],
        )

        psm = ParitySupermartingale(system)

        q_states = [0, 1]

        parity_objectives = [var_eq_val(q, 1), var_eq_val(q, 0)]

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
        with open(f"{output_dir}/run_{RUN}_K_{K}.txt", "w") as f:
            f.write("Result: ")
            f.write(str(lin_lex_psm_str))
            f.write(str(invariant_str))
            f.write(f"\nTime taken: {elapsed_times[-1]}")

    with open(f"{output_dir}/times.txt", "w") as f:
        f.write("Times: ")
        f.write(str(elapsed_times))
        f.write(f"\nAverage time: {sum(elapsed_times) / len(elapsed_times)}")
