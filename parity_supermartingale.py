from functools import partial
from sympy.logic.boolalg import Boolean
from reactive_module import (
    Guard,
    GuardedCommand,
    NonDeterministicStochasticUpdate,
    ProbabilisticUpdate,
    ProgramState,
    ReactiveModule,
)

from itertools import chain, product

from z3 import (
    And as z3_And,
    BoolRef,
    ExprRef,
    Implies,
    ModelRef,
    Optimize,
    Or,
    Solver,
    sat,
    unsat,
)
from sympy import Add, And, Eq, Expr, Symbol, Matrix, linear_eq_to_matrix, zeros

from utils import (
    DNF_to_linear_function,
    LinearFunction,
    Mat,
    SPLinearFunction,
    SPStateBasedLinearFunction,
    StateBasedLinearFunction,
    fst,
    get_symbol_assignment,
    get_z3_var,
    get_z3_var_map,
    parse_DNF,
    parse_conjunct,
    parse_constraint,
    parse_q_assignment,
    snd,
    to_z3_dnf,
    to_z3_expr,
    parse_matrix,
    unzip,
    update_var_map,
    z3_real_to_float,
)

ParityObjective = Boolean
SPLinPSM = SPLinearFunction
SPLinLexPSM = list[dict[int, SPLinPSM]]
LinPSM = LinearFunction
LinLexPSM = list[dict[int, LinPSM]]


class ParitySupermartingale:
    def __init__(
        self,
        system: ReactiveModule,
    ) -> None:
        """
        Methods for computing a Parity Supermartingale for a
        given reactive module and a given property (passed as boolean indicator
        functions for priority levels).
        """
        self._counter = 0
        self._system = system
        update_var_map(system._vars)
        self._fresh_vars = []

    def _fresh_var(self, prefix: str) -> Symbol:
        self._counter += 1
        self._fresh_vars.append(Symbol(f"{prefix}_({self._counter})"))
        update_var_map([self._fresh_vars[-1]])
        return self._fresh_vars[-1]

    def _fresh_var_vec(self, prefix: str, n: int, row=False) -> Matrix:
        row, col = (1, n) if row else (n, 1)
        return Matrix(
            row, col, lambda i, j: self._fresh_var(f"{prefix}_{j if row else i}")
        )

    def _fresh_var_mat(self, prefix: str, shape: tuple[int, int]) -> Matrix:
        return Matrix(*shape, lambda i, j: self._fresh_var(f"{prefix}_{i},{j}"))

    def _satisfiable(self, query) -> bool:
        solver = Solver()
        solver.add(query)
        return solver.check() == sat

    def _farkas_constraint(
        self, a_t: Matrix, b_t: Matrix, c: Matrix, d: Expr, z: Matrix
    ) -> list[BoolRef]:
        z3_at_z = parse_matrix(a_t * z)
        z3_c = parse_matrix(c)

        return [z3_at_z[i][0] == z3_c[i][0] for i in range(len(z3_at_z))] + [
            to_z3_expr(b_t.dot(z)) <= to_z3_expr(d)
        ]

    def _farkas_lemma(
        self,
        a: Matrix,
        b: Matrix,
        c: Matrix,
        d: Expr,
        with_gale_constraint: bool = False,
    ):
        z = self._fresh_var_vec("z", a.shape[0])
        z_non_neg: list[BoolRef] = [to_z3_expr(z[i, 0]) >= 0 for i in range(z.shape[0])]

        if with_gale_constraint:
            # TODO: Implement Gale constraint for Farkas lemma
            pass

        farkas_constraint = self._farkas_constraint(
            a.transpose(), b.transpose(), c, d, z
        )
        return z_non_neg + farkas_constraint

    def _v_j_constraint(
        self,
        i: int,
        v_j: tuple[int, ParityObjective],
        guards: list[tuple[int, Guard]],
        template: SPLinearFunction,
    ) -> tuple[list[ExprRef], list[tuple[Symbol, int]]]:
        """
        Given index `i` of the SPPM component, index `j` of Parity Objective,
        a set of `guards` of the system, a `template` for the linear constraints
        """
        a_template, _ = template
        constraints: list[ExprRef] = []
        decrement_vars: list[tuple[Symbol, int]] = []
        v_j_conjuncts = list(enumerate(parse_DNF(v_j[1])))

        for guard in guards:
            guard_conjuncts = parse_DNF(guard[1])

            for guard_conjunct, v_j_conjunct in product(guard_conjuncts, v_j_conjuncts):
                premise_constraints = list(
                    # Convert conjunct of constraints to z3 representation
                    chain.from_iterable(
                        map(
                            parse_constraint,
                            parse_conjunct(guard_conjunct)
                            + parse_conjunct(v_j_conjunct[1]),
                        )
                    )
                )
                a, b = linear_eq_to_matrix(premise_constraints, self._system.vars)
                assert isinstance(a, Matrix) and isinstance(b, Matrix)

                ax_z3 = parse_matrix(a * Matrix(self._system.vars))
                b_z3 = parse_matrix(b)

                # Check if the premise is satisfiable, otherwise skip
                premise = z3_And([ax_z3[i][0] <= b_z3[i][0] for i in range(len(ax_z3))])
                if not self._satisfiable(premise):
                    # print("Premise not satisfiable, skipped:\n", premise)
                    continue

                actions_transitions = self._system.get_nth_command_updates(guard[0])

                # same epsilon decrease for all non-deterministic actions
                eps = self._fresh_var(
                    f"epsilon_v{i},g{guard[0]},s{v_j[0]},{v_j_conjunct[0]}"
                )
                decrement_vars.append((eps, guard[0]))

                z3_eps = get_z3_var_map()[eps.name]

                if v_j[0] % 2 and v_j[0] == i:
                    # if j odd and j == i epsilon must be strictly positive
                    constraints.append(0 < z3_eps)
                else:
                    constraints.append(0 <= z3_eps)

                constraints.append(z3_eps <= 1)

                for transitions in actions_transitions:
                    distribution, updates = unzip(transitions)
                    updates_a, updates_b = unzip(updates)

                    # c_t = a_template * \sum(p_i * a_i) - a_template
                    c_t: Matrix = (
                        a_template
                        * sum(
                            map(
                                lambda p_i, a_i: p_i * a_i,
                                distribution,
                                updates_a,
                            ),
                            zeros(len(self._system.vars)),
                        )
                        - a_template
                    )

                    # d = -a_template * \sum(p_i * b_i) (- epsilon_g if j is odd
                    d = (
                        -a_template.dot(
                            sum(
                                map(
                                    lambda p_i, b_i: p_i * b_i,
                                    distribution,
                                    updates_b,
                                ),
                                zeros(len(self._system.vars), 1),
                            )
                        )
                        - eps
                    )

                    constraints.extend(self._farkas_lemma(a, b, c_t.transpose(), d))
        return constraints, decrement_vars

    def _get_linear_template(self, prefix: str, m: int, n: int) -> SPLinearFunction:
        return (
            self._fresh_var_mat(f"{prefix}_a", (m, n)),
            self._fresh_var_vec(f"{prefix}_b", m),
        )

    def _is_ranked_guard(self, model: ModelRef, eps: tuple[Symbol, int]) -> bool:
        z3_symb = get_z3_var(eps[0])
        return model.eval(z3_symb > 0)

    def _alpha(
        self, i: int, guards: list[tuple[int, Guard]], s: list[ParityObjective], q: int
    ) -> tuple[LinPSM, list[tuple[int, Guard]]]:
        epsilons: list[tuple[Symbol, int]] = []
        constraints: list[ExprRef] = []
        template = self._get_linear_template(
            f"alpha{i}_q{q}", 1, len(self._system.vars)
        )
        lp = Optimize()
        # force alpha_i_q to be non-negative
        non_negativity = (
            to_z3_expr(template[0].dot(self._system.vars) + template[1][0, 0]) >= 0
        )
        lp.add(non_negativity)
        for s_j in enumerate(s, i):
            s_j_constraints, s_j_epsilons = self._v_j_constraint(
                i, s_j, guards, template
            )
            constraints.extend(s_j_constraints)
            epsilons.extend(s_j_epsilons)
            lp.add(constraints)

        if len(epsilons) == 0:
            # No premise is satisfiable, thus the synthesis of the current PSM
            # has finished
            # return 0 function and the set of guards unranked
            return ([[0.0] * len(self._system.vars)], [[0.0]]), guards

        # Add soft constraints for epsilon variables positivity
        for eps in epsilons:
            lp.add_soft(to_z3_expr(eps[0]) > 0)

        if lp.check() == unsat:
            # No solution for linear program
            raise RuntimeError(f"No solution for linear program computing alpha_{i}")

        model = lp.model()
        is_ranked_guard = partial(self._is_ranked_guard, model)
        ranked_guards_idx = list(map(lambda x: x[1], filter(is_ranked_guard, epsilons)))
        updated_guards = list(filter(lambda x: x[0] not in ranked_guards_idx, guards))
        z3_alpha_i_a, z3_alpha_i_b = (
            parse_matrix(template[0]),
            parse_matrix(template[1]),
        )
        alpha_i: LinPSM = (
            [[z3_real_to_float(model[var]) for var in row] for row in z3_alpha_i_a],
            [[z3_real_to_float(model[var]) for var in row] for row in z3_alpha_i_b],
        )
        if len(updated_guards) == len(guards):
            # No guards has been ranked, thus no solution synthesized
            raise RuntimeError(f"No solution for linear program computing alpha_{i}")

        # return alpha_i function and not ranked guards
        return alpha_i, updated_guards

    def _add_dpa_state_evaluation(
        self, dpa_state: int, guards: list[Guard]
    ) -> list[tuple[int, Guard]]:
        return list(
            filter(
                lambda g: self._satisfiable(to_z3_dnf(g[1])),
                enumerate(
                    map(
                        lambda g: And(
                            *(
                                parse_conjunct(g)
                                + [get_symbol_assignment(Symbol("q"), dpa_state)]
                            )
                        ),
                        guards,
                    ),
                ),
            )
        )

    def _get_non_negativity_constraints(
        self, invariant: SPStateBasedLinearFunction, lex_psm: SPLinLexPSM
    ):
        """
        ∀ x. (∀ q. ∀ PSM ∈ LexPSM). I(x,q) (& q == q) => PSM(x, q) >= 0
        """

        # TODO: Add q == q constraint

        def forall_psm(q_inv: tuple[int, SPLinearFunction]):
            q, (inv_a, inv_b) = q_inv
            q_a, q_b = DNF_to_linear_function(
                get_symbol_assignment(Symbol("q"), q), self._system.vars
            )
            return chain.from_iterable(
                map(
                    lambda psm: self._farkas_lemma(
                        inv_a.col_join(q_a),
                        -inv_b.col_join(q_b),
                        -psm[q][0].transpose(),
                        psm[q][1][0, 0],
                    ),
                    lex_psm,
                )
            )

        return list(
            chain.from_iterable(
                map(
                    forall_psm,
                    invariant.items(),
                )
            )
        )

    def _get_invariant_init_contraints(self, invariant: SPStateBasedLinearFunction):
        """
        (∀ init ∈ Init.)
            ⋁{q ∈ Q} (I(init, q) (∧ q==q))
        """

        def get_constraint(init: ProgramState, q_inv: tuple[int, SPLinearFunction]):
            q, (inv_a, inv_b) = q_inv
            return z3_And(
                to_z3_expr(inv_a.dot(init) + inv_b[0, 0]) <= 0,
                *parse_q_assignment(get_symbol_assignment(Symbol("q"), q)),
            )

        return list(
            map(
                lambda init: Or(
                    list(map(partial(get_constraint, init), invariant.items()))
                ),
                self._system.init,
            )
        )

    def _get_invariant_consec_contraints(self, invariant: SPStateBasedLinearFunction):
        """
        ∀ x. (∀ (g,U) ∈ (G,F). ∀ (_,u) ∈ U. ∀ q).
            I(x, q) & g(x) (& q==q) => I(u(x), u[q](x))
        """

        q_index = self._system.vars.index(Symbol("q"))

        def forall_guarded_commands(guarded_command: GuardedCommand):
            g_a, g_b = DNF_to_linear_function(guarded_command[0], self._system.vars)
            return chain.from_iterable(
                map(
                    lambda stoc_update: chain.from_iterable(
                        map(partial(forall_updates, g_a, g_b), stoc_update)
                    ),
                    guarded_command[1],
                )
            )

        def forall_updates(g_a: Matrix, g_b: Matrix, prob_update: ProbabilisticUpdate):
            return chain.from_iterable(
                map(
                    partial(
                        get_constraint,
                        g_a,
                        g_b,
                        prob_update[1],
                    ),
                    invariant.items(),
                )
            )

        def get_constraint(
            g_a: Matrix,
            g_b: Matrix,
            update: SPLinearFunction,
            q_inv: tuple[int, SPLinearFunction],
        ):
            # FIXME:
            # Need to assume that the state variable q is directly assigned by a constant and not
            # by a linear function otherwise we can't compute I(x',q')
            u_a, u_b = update

            assert u_a.row(q_index) == zeros(1, u_a.shape[1])

            next_q: int = u_b[0, 0]

            q, inv = q_inv
            inv_a, inv_b = inv
            next_inv_a, next_inv_b = invariant[next_q]

            q_a, q_b = DNF_to_linear_function(
                get_symbol_assignment(Symbol("q"), q), self._system.vars
            )

            return self._farkas_lemma(
                inv_a.col_join(g_a).col_join(q_a),
                -inv_b.col_join(g_b).col_join(q_b),
                Matrix.transpose(next_inv_a * u_a),
                -next_inv_a.dot(u_b) - next_inv_b[0, 0],
            )

        return list(
            chain.from_iterable(map(forall_guarded_commands, self._system.body))
        )

    def _get_drift_constraints(
        self,
        s_j: ParityObjective,
        guard: Guard,
        actions: NonDeterministicStochasticUpdate,
        epsilon: Symbol,
        psm_template: SPLinPSM,
        inv_template: SPLinearFunction,
    ):
        """
        ∀ x. (∀ s ∈ S. ∀ (g,U) ∈ (G,F). ∀ (p,u) ∈ U. ∀ q).
            I(x, q) & s_j(x) & g(x) (& q==q) => Post V_i(x) <= V_i(x) - epsilon
        """
        v_a, _ = psm_template
        inv_a, inv_b = inv_template
        constraints = []

        s_j_conjuncts = parse_DNF(s_j)

        for s_j_conjunct in s_j_conjuncts:
            s_a, s_b = DNF_to_linear_function(s_j_conjunct, self._system.vars)
            g_a, g_b = DNF_to_linear_function(guard, self._system.vars)

            a = inv_a.col_join(s_a).col_join(g_a)
            b = -inv_b.col_join(s_b).col_join(g_b)

            # Check if the premise is satisfiable, otherwise skip
            z3_ax = parse_matrix(a * Matrix(self._system.vars))
            z3_b = parse_matrix(b)
            if not self._satisfiable(
                z3_And([z3_ax[i][0] <= z3_b[i][0] for i in range(len(z3_ax))])
            ):
                # print("Premise not satisfiable, skipped")
                continue

            for action in actions:
                distribution, updates = unzip(action)
                updates_a, updates_b = unzip(updates)

                # c_t = V_Theta * \sum(p_i * a_i) - V_Theta
                c_t: Matrix = (
                    v_a
                    * sum(
                        map(
                            lambda p_i, a_i: p_i * a_i,
                            distribution,
                            updates_a,
                        ),
                        zeros(len(self._system.vars)),
                    )
                    - v_a
                )

                # d = -V_Theta * \sum(p_i * b_i) - epsilon_ijk
                d = (
                    -v_a.dot(
                        sum(
                            map(
                                lambda p_i, b_i: p_i * b_i,
                                distribution,
                                updates_b,
                            ),
                            zeros(len(self._system.vars), 1),
                        )
                    )
                    - epsilon
                )
                constraints.extend(self._farkas_lemma(a, b, c_t.transpose(), d))
        return constraints

    def _get_epsilon_constraint(
        self, i: int, j: int, k: int, epsilons: list[list[list[Symbol]]]
    ) -> BoolRef:
        if i == 0:
            return get_z3_var(epsilons[i][j][k]) >= 0

        premise = z3_And(
            [
                get_z3_var(epsilon) == 0
                for epsilon in list(map(lambda x: x[j][k], epsilons))[:i]
            ]
        )

        if i == j and i % 2:
            # Enforce strict decrease in expectation for the last possible
            # case of a Parity Objective with odd priority
            return Implies(premise, get_z3_var(epsilons[i][j][k]) > 0)

        return Implies(premise, get_z3_var(epsilons[i][j][k]) >= 0)

    def verification(self, q_states: list[int], s: list[ParityObjective]) -> LinLexPSM:
        """
        Synthesize a LPSM for the given reactive module certifying the
        reactive property encoded as a list of parity objectives `v`
        """
        guards = self._system.guards
        lex_psm: LinLexPSM = [{} for _ in range(len(s))]

        # Fix q and then synthesize an SPPM for q
        for q_state in q_states:
            dpa_state_guards = self._add_dpa_state_evaluation(q_state, guards)

            for i in range(len(s)):
                # print(f"Synthesizing psm_{i}_q{q_state}")
                psm_i, dpa_state_guards = self._alpha(i, dpa_state_guards, s, q_state)
                # print(f"Done synthesizing psm_{i}_q{q_state}")
                lex_psm[i].update({q_state: psm_i})

                if dpa_state_guards == []:
                    # Short circuiting iterative synthesis algorithm if no guards are left
                    break

            if len(dpa_state_guards) > 0:
                print("WARNING: Not all guards have been ranked")
        return lex_psm

    def invariant_synthesis_and_verification(
        self, q_states: list[int], s: list[ParityObjective]
    ):
        # Create a functional template for the LinLexPSM
        lin_lex_psm_template: SPLinLexPSM = [
            {
                q_state: self._get_linear_template(
                    f"V_{i}_q{q_state}", 1, len(self._system.vars)
                )
                for q_state in range(len(q_states))
            }
            for i in range(len(s))
        ]

        # Create a template for the linear invariant to synthesize
        lin_invariant_template: SPStateBasedLinearFunction = {
            q_state: self._get_linear_template("inv", 1, len(self._system.vars))
            for q_state in q_states
        }

        epsilons: dict[int, list[list[list[Symbol]]]] = {
            q_state: [] for q_state in q_states
        }

        solver = Solver()

        # Add non-negativity constraints for each LinPSM of the LexPSM
        solver.add(
            self._get_non_negativity_constraints(
                lin_invariant_template, lin_lex_psm_template
            )
        )

        solver.add(self._get_invariant_init_contraints(lin_invariant_template))

        solver.add(self._get_invariant_consec_contraints(lin_invariant_template))

        for q_state in q_states:
            dpa_state_guards = self._add_dpa_state_evaluation(
                q_state, self._system.guards
            )
            for i in range(len(s)):
                epsilons[q_state].append([])
                for j in range(len(s)):
                    epsilons[q_state][i].append([])
                    for k in range(len(dpa_state_guards)):
                        # Create the decrement variable for the constraint:
                        # S_j \cap G_k \cap I => Post V_i <= V_i - epsilon_q_ijk
                        epsilons[q_state][i][j].append(
                            self._fresh_var(f"epsilon_q{q_state}_{i},{j},{k}")
                        )

                        # For each combination of i, j, k, we need to compute the
                        # Add the post expectation constraints to the solver
                        solver.add(
                            *self._get_drift_constraints(
                                s[j],
                                dpa_state_guards[k][1],
                                self._system.get_nth_command_updates(
                                    dpa_state_guards[k][0]
                                ),
                                epsilons[q_state][i][j][k],
                                lin_lex_psm_template[i][q_state],
                                lin_invariant_template[q_state],
                            )
                        )

                        # Add the epsilon constraint to the solver
                        solver.add(
                            self._get_epsilon_constraint(i, j, k, epsilons[q_state])
                        )

        if solver.check() == unsat:
            # No solution for linear program
            raise RuntimeError("No solution for invariant and LinLexPSM synthesis")

        model = solver.model()
        lin_lex_psm: LinLexPSM = [
            {
                q_state: (
                    [
                        [z3_real_to_float(model[var]) for var in row]
                        for row in parse_matrix(fst(lin_lex_psm_template[i][q_state]))
                    ],
                    [
                        [z3_real_to_float(model[var]) for var in row]
                        for row in parse_matrix(snd(lin_lex_psm_template[i][q_state]))
                    ],
                )
                for q_state in q_states
            }
            for i in range(len(s))
        ]

        lin_invariant: StateBasedLinearFunction = {
            q_state: (
                [
                    [z3_real_to_float(model[var]) for var in row]
                    for row in parse_matrix(fst(lin_invariant_template[q_state]))
                ],
                [
                    [z3_real_to_float(model[var]) for var in row]
                    for row in parse_matrix(snd(lin_invariant_template[q_state]))
                ],
            )
            for q_state in q_states
        }
        return lin_lex_psm, lin_invariant
