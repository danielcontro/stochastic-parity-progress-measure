import os
import time

from sympy import Add, And, Eq, GreaterThan, LessThan, Matrix, Or, Symbol, symbols

from parity_supermartingale import (
    ParitySupermartingale,
    pretty_lin_lex_psm,
    pretty_state_based_lin_function,
)
from reactive_module import Guard, GuardedCommand, ReactiveModule

from utils import var_eq_val, var_gt_val, var_lt_val, var_ge_val, var_le_val, var_ne_val

# PRISM module
"""
const int N=2;
const int K;
const int range = 2*(K+1)*N;
const int counter_init = (K+1)*N;
const int left = N;
const int right = 2*(K+1)*N - N;

global counter : [0..range] init counter_init;

module process1
	pc1 : [0..3];
	coin1 : [0..1];

	[] (pc1=0)  -> 0.5 : (coin1'=0) & (pc1'=1) + 0.5 : (coin1'=1) & (pc1'=1);
	[] (pc1=1) & (coin1=0) & (counter>0) -> (counter'=counter-1) & (pc1'=2) & (coin1'=0);
	[] (pc1=1) & (coin1=1) & (counter<range) -> (counter'=counter+1) & (pc1'=2) & (coin1'=0);
	[] (pc1=2) & (counter<=left) -> (pc1'=3) & (coin1'=0);
	[] (pc1=2) & (counter>=right) -> (pc1'=3) & (coin1'=1);
	[] (pc1=2) & (counter>left) & (counter<right) -> (pc1'=0);
	[done] (pc1=3) -> (pc1'=3);
endmodule

module process2 = process1[pc1=pc2,coin1=coin2] endmodule
"""

# PRISM property
"""
P>=1 [ F "finished" ]
"""

KS = [2048]
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
        pc3, c3 = symbols("pc3 coin3")
        q = symbols("q")

        def process(counter, pc, c):
            vars = (counter, pc, c)
            init = [
                (COUNTER_INIT, 0.0, 0.0),
            ]
            body = [
                GuardedCommand(
                    [],
                    var_eq_val(pc, 0),
                    [
                        [
                            (
                                0.5,
                                (
                                    Matrix(
                                        [
                                            [1, 0, 0],
                                            [0, 0, 0],
                                            [0, 0, 0],
                                        ]
                                    ),
                                    Matrix(
                                        [
                                            [0],
                                            [1],
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
                                            [1, 0, 0],
                                            [0, 0, 0],
                                            [0, 0, 0],
                                        ]
                                    ),
                                    Matrix(
                                        [
                                            [0],
                                            [1],
                                            [1],
                                        ]
                                    ),
                                ),
                            ),
                        ]
                    ],
                ),
                GuardedCommand(
                    [],
                    And(var_eq_val(pc, 1), var_eq_val(c, 0), var_gt_val(counter, 0)),
                    [
                        [
                            (
                                1,
                                (
                                    Matrix(
                                        [
                                            [1, 0, 0],
                                            [0, 0, 0],
                                            [0, 0, 0],
                                        ]
                                    ),
                                    Matrix(
                                        [
                                            [-1],
                                            [2],
                                            [0],
                                        ]
                                    ),
                                ),
                            )
                        ]
                    ],
                ),
                GuardedCommand(
                    [],
                    And(
                        var_eq_val(pc, 1), var_eq_val(c, 1), var_lt_val(counter, RANGE)
                    ),
                    [
                        [
                            (
                                1,
                                (
                                    Matrix(
                                        [
                                            [1, 0, 0],
                                            [0, 0, 0],
                                            [0, 0, 0],
                                        ]
                                    ),
                                    Matrix(
                                        [
                                            [1],
                                            [2],
                                            [0],
                                        ]
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
                                        [
                                            [1, 0, 0],
                                            [0, 0, 0],
                                            [0, 0, 0],
                                        ]
                                    ),
                                    Matrix(
                                        [
                                            [0],
                                            [3],
                                            [0],
                                        ]
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
                                        [
                                            [1, 0, 0],
                                            [0, 0, 0],
                                            [0, 0, 0],
                                        ]
                                    ),
                                    Matrix(
                                        [
                                            [0],
                                            [3],
                                            [1],
                                        ]
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
                                        [
                                            [1, 0, 0],
                                            [0, 0, 0],
                                            [0, 0, 1],
                                        ]
                                    ),
                                    Matrix(
                                        [
                                            [0],
                                            [0],
                                            [0],
                                        ]
                                    ),
                                ),
                            )
                        ]
                    ],
                ),
                GuardedCommand(
                    ["finished"],
                    var_eq_val(pc, 3),
                    [
                        [
                            (
                                1,
                                (
                                    Matrix(
                                        [
                                            [1, 0, 0],
                                            [0, 1, 0],
                                            [0, 0, 1],
                                        ]
                                    ),
                                    Matrix(
                                        [
                                            [0],
                                            [0],
                                            [0],
                                        ]
                                    ),
                                ),
                            )
                        ]
                    ],
                ),
            ]
            return ReactiveModule(init, vars, body)

        # Process 1
        process1 = process(counter, pc1, c1)
        process2 = process(counter, pc2, c2)
        process3 = process(counter, pc3, c3)

        # Automaton
        q_init = [(0.0,)]

        q_vars = (q,)

        q_body = [
            GuardedCommand(
                [],
                And(var_eq_val(pc1, 3), var_eq_val(pc2, 3), var_eq_val(pc3, 3)),
                [[(1, (Matrix([[0]]), Matrix([[1]])))]],
            ),
            GuardedCommand(
                [],
                And(var_lt_val(pc1, 3), var_le_val(pc2, 3), var_le_val(pc3, 3)),
                [[(1, (Matrix([[0]]), Matrix([[0]])))]],
            ),
            GuardedCommand(
                [],
                And(var_le_val(pc1, 3), var_lt_val(pc2, 3), var_le_val(pc3, 3)),
                [[(1, (Matrix([[0]]), Matrix([[0]])))]],
            ),
            GuardedCommand(
                [],
                And(var_le_val(pc1, 3), var_le_val(pc2, 3), var_lt_val(pc3, 3)),
                [[(1, (Matrix([[0]]), Matrix([[0]])))]],
            ),
        ]

        q_module = ReactiveModule(q_init, q_vars, q_body)

        system = (
            process1.interleaving(process2)
            .interleaving(process3)
            .parallel_composition(q_module)
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
