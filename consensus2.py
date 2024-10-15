import itertools
import os
import time

from sympy import Add, And, Eq, GreaterThan, LessThan, Matrix, Symbol, symbols

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
label "finished" = pc1 = 3 & pc2 = 3;

const int N = 2;
const int K;
const int range = (2 * (2 + 1)) * 2;
const int counter_init = (2 + 1) * 2;
const int left = 2;
const int right = (2 * (2 + 1)) * 2 - 2;
global counter : [0 .. 12] init 6;

module process1process2
    pc1 : [0 .. 3];
    coin1 : [0 .. 1];
    pc2 : [0 .. 3];
    coin2 : [0 .. 1];

    [] pc1 = 0 -> 0.5:(coin1' = 0) & (pc1' = 1) + 0.5:(coin1' = 1) & (pc1' = 1);
    [] (pc1 = 1 & coin1 = 0) & counter > 0 -> (counter' = counter - 1) & (pc1' = 2) & (coin1' = 0);
    [] (pc1 = 1 & coin1 = 1) & counter < 12 -> (counter' = counter + 1) & (pc1' = 2) & (coin1' = 0);
    [] pc1 = 2 & counter <= 2 -> (pc1' = 3) & (coin1' = 0);
    [] pc1 = 2 & counter >= 10 -> (pc1' = 3) & (coin1' = 1);
    [] (pc1 = 2 & counter > 2) & counter < 10 -> (pc1' = 0);
    [done] pc1 = 3 & pc2 = 3 -> (pc1' = 3) & (pc2' = 3);
    [] pc2 = 0 -> 0.5:(coin2' = 0) & (pc2' = 1) + 0.5:(coin2' = 1) & (pc2' = 1);
    [] (pc2 = 1 & coin2 = 0) & counter > 0 -> (counter' = counter - 1) & (pc2' = 2) & (coin2' = 0);
    [] (pc2 = 1 & coin2 = 1) & counter < 12 -> (counter' = counter + 1) & (pc2' = 2) & (coin2' = 0);
    [] pc2 = 2 & counter <= 2 -> (pc2' = 3) & (coin2' = 0);
    [] pc2 = 2 & counter >= 10 -> (pc2' = 3) & (coin2' = 1);
    [] (pc2 = 2 & counter > 2) & counter < 10 -> (pc2' = 0);
endmodule
"""

# PRISM property
"""
P>=1 [ F "finished" ]
"""

KS = [256]
for K in KS:
    # Experiments setup
    RUNS = 20

    output_dir = f"./results/consensus_n2_k{K}"
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
        q = symbols("q")

        # Utility functions
        g1 = [var_eq_val(pc1, 0)]
        g2 = [var_eq_val(pc1, 1), var_eq_val(c1, 0), var_gt_val(counter, 0)]
        g3 = [var_eq_val(pc1, 1), var_eq_val(c1, 1), var_lt_val(counter, RANGE)]
        g4 = [var_eq_val(pc1, 2), var_le_val(counter, LEFT)]
        g5 = [var_eq_val(pc1, 2), var_ge_val(counter, RIGHT)]
        g6 = [var_eq_val(pc1, 2), var_gt_val(counter, LEFT), var_lt_val(counter, RIGHT)]
        g7 = [var_eq_val(pc1, 3), var_eq_val(pc2, 3)]
        g8 = [var_eq_val(pc2, 0)]
        g9 = [var_eq_val(pc2, 1), var_eq_val(c2, 0), var_gt_val(counter, 0)]
        g10 = [var_eq_val(pc2, 1), var_eq_val(c2, 1), var_lt_val(counter, RANGE)]
        g11 = [var_eq_val(pc2, 2), var_le_val(counter, LEFT)]
        g12 = [var_eq_val(pc2, 2), var_ge_val(counter, RIGHT)]
        g13 = [
            var_eq_val(pc2, 2),
            var_gt_val(counter, LEFT),
            var_lt_val(counter, RIGHT),
        ]

        f1: StochasticUpdate = [
            (
                0.5,
                (
                    Matrix(
                        [
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 1, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [1],
                            [0],
                            [0],
                            [0],
                            [0],
                            [0],
                        ]
                    ),
                ),
            ),
            (
                0.5,
                (
                    Matrix(
                        [
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 1, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [1],
                            [1],
                            [0],
                            [0],
                            [0],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f2: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 1, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [2],
                            [0],
                            [0],
                            [0],
                            [-1],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f3: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 1, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [2],
                            [0],
                            [0],
                            [0],
                            [1],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f4: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 1, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [3],
                            [0],
                            [0],
                            [0],
                            [0],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f5: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 1, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [3],
                            [1],
                            [0],
                            [0],
                            [0],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f6: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 1, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [0],
                            [0],
                            [0],
                            [0],
                            [0],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f7: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [0, 0, 0, 0, 0, 0],
                            [0, 1, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [3],
                            [0],
                            [3],
                            [0],
                            [0],
                            [1],
                        ]
                    ),
                ),
            ),
        ]

        f8: StochasticUpdate = [
            (
                0.5,
                (
                    Matrix(
                        [
                            [1, 0, 0, 0, 0, 0],
                            [0, 1, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [0],
                            [0],
                            [1],
                            [0],
                            [0],
                            [0],
                        ]
                    ),
                ),
            ),
            (
                0.5,
                (
                    Matrix(
                        [
                            [1, 0, 0, 0, 0, 0],
                            [0, 1, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [0],
                            [0],
                            [1],
                            [1],
                            [0],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f9: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [1, 0, 0, 0, 0, 0],
                            [0, 1, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [0],
                            [0],
                            [2],
                            [0],
                            [-1],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f10: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [1, 0, 0, 0, 0, 0],
                            [0, 1, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [0],
                            [0],
                            [2],
                            [0],
                            [1],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f11: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [1, 0, 0, 0, 0, 0],
                            [0, 1, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [0],
                            [0],
                            [3],
                            [0],
                            [0],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f12: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [1, 0, 0, 0, 0, 0],
                            [0, 1, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [0],
                            [0],
                            [3],
                            [1],
                            [0],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        f13: StochasticUpdate = [
            (
                1,
                (
                    Matrix(
                        [
                            [1, 0, 0, 0, 0, 0],
                            [0, 1, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0],
                            [0, 0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 0, 0],
                        ]
                    ),
                    Matrix(
                        [
                            [0],
                            [0],
                            [0],
                            [0],
                            [0],
                            [0],
                        ]
                    ),
                ),
            ),
        ]

        g = [g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13]
        f: NonDeterministicStochasticUpdate = [
            f1,
            f2,
            f3,
            f4,
            f5,
            f6,
            f7,
            f8,
            f9,
            f10,
            f11,
            f12,
            f13,
        ]

        cp = list(
            map(
                lambda x: GuardedCommand(
                    [], And(*g[x[0]], *g[x[1]]), [f[x[0]]] + [f[x[1]]]
                ),
                itertools.product(range(0, 6), range(7, 13)),
            )
        )

        def strict_g(indexes: list[int], avoid: list[int]):
            return list(
                map(
                    lambda i: GuardedCommand(
                        [],
                        And(
                            *g[i],
                            *list(
                                itertools.chain.from_iterable(
                                    map(
                                        lambda j: list(
                                            map(lambda k: negate_constraint(k), g[j])
                                        ),
                                        avoid,
                                    )
                                )
                            ),
                        ),
                        [f[i]],
                    ),
                    indexes,
                )
            )

        g_neg_g1 = strict_g([i for i in range(6)], [j for j in range(7, 13)])
        g1_neg_g = strict_g([i for i in range(7, 13)], [j for j in range(6)])

        expected_gc = (
            cp + g_neg_g1 + g1_neg_g + [GuardedCommand([], And(*g[6]), [f[6]])]
        )

        system = ReactiveModule(
            [(0, 0, 0, 0, COUNTER_INIT, 0)],
            (pc1, c1, pc2, c2, counter, q),
            [GuardedCommand([], And(*g[i]), [f[i]]) for i in range(13)],
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
