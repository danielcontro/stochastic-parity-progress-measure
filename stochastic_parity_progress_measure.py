from functools import partial
from sympy.logic.boolalg import Boolean
from reactive_module import Guard, ReactiveModule

import itertools

from z3 import (
    BoolRef,
    ExprRef,
    ModelRef,
    Optimize,
    Solver,
    sat,
    unsat,
)
from sympy import Add, And, Eq, Expr, Symbol, Matrix, linear_eq_to_matrix, zeros

from utils import (
    get_z3_var,
    get_z3_var_map,
    parse_DNF,
    parse_conjunct,
    parse_constraint,
    to_z3_dnf,
    to_z3_expr,
    parse_matrix,
    unzip,
    update_var_map,
    z3_real_to_float,
)

ParityObjective = Boolean


class SPPM:
    def __init__(
        self,
        system: ReactiveModule,
    ) -> None:
        """
        Methods for computing the stochastic parity progress measure for a
        given reactive module and a given property (passed as boolean indicator
        functions for priority levels).
        """
        self._counter = 0
        self._system = system
        update_var_map(system._vars)
        self._fresh_vars = []

    def fresh_var(self, prefix: str) -> Symbol:
        self._counter += 1
        self._fresh_vars.append(Symbol(f"{prefix}_({self._counter})"))
        update_var_map([self._fresh_vars[-1]])
        return self._fresh_vars[-1]

    def fresh_var_vec(self, prefix: str, n: int, row=False) -> Matrix:
        row, col = (1, n) if row else (n, 1)
        return Matrix(
            row, col, lambda i, j: self.fresh_var(f"{prefix}_{j if row else i}")
        )

    def fresh_var_mat(
        self, prefix: str, shape: tuple[int, int]
    ) -> tuple[Matrix, list[Symbol]]:
        return Matrix(
            *shape, lambda i, j: self.fresh_var(f"{prefix}_{i},{j}")
        ), self._fresh_vars[-shape[0] * shape[1] :]

    def satisfiable(self, query) -> bool:
        solver = Solver()
        solver.add(query)
        return solver.check() == sat

    def farkas_constraint(
        self, a_t: Matrix, b_t: Matrix, c: Matrix, d: Expr, z: Matrix
    ) -> list[BoolRef]:
        z3_at_z = parse_matrix(a_t * z)
        z3_c = parse_matrix(c)

        return [z3_at_z[i][0] == z3_c[i][0] for i in range(len(z3_at_z))] + [
            to_z3_expr(b_t.dot(z)) <= to_z3_expr(d)
        ]

    def farkas_lemma(
        self, a: Matrix, b: Matrix, c: Matrix, d: Expr, simplified: bool = True
    ):
        z = self.fresh_var_vec("z", a.shape[0])
        z_non_neg: list[BoolRef] = [to_z3_expr(z[i, 0]) >= 0 for i in range(z.shape[0])]

        if not simplified:
            # TODO: Implement Gale constraint for Farkas lemma
            pass

        farkas_constraint = self.farkas_constraint(
            a.transpose(), b.transpose(), c, d, z
        )
        return z_non_neg + farkas_constraint

    def v_j_constraint(
        self,
        i: int,
        v_j: tuple[int, ParityObjective],
        guards: list[tuple[int, Guard]],
        template: tuple[Matrix, Symbol],
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

            for guard_conjunct, v_j_conjunct in itertools.product(
                guard_conjuncts, v_j_conjuncts
            ):
                premise_constraints = list(
                    # Convert conjunct of constraints to z3 representation
                    itertools.chain.from_iterable(
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
                premise = z3.And([ax_z3[i][0] <= b_z3[i][0] for i in range(len(ax_z3))])
                if not self.satisfiable(premise):
                    print("Premise not satisfiable, skipped premise:", premise)
                    continue

                actions_transitions = self._system.transitions(guard[0])

                # same epsilon decrease for all non-deterministic actions
                eps = self.fresh_var(
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

                    constraints.extend(self.farkas_lemma(a, b, c_t.transpose(), d))
        return constraints, decrement_vars

    def _get_linear_template(self, prefix: str, n: int) -> tuple[Matrix, Symbol]:
        return (
            self.fresh_var_vec(f"{prefix}_a", n, True),
            self.fresh_var(f"{prefix}_b"),
        )

    def _is_ranked_guard(self, model: ModelRef, eps: tuple[Symbol, int]) -> bool:
        z3_symb = get_z3_var(eps[0])
        return model.eval(z3_symb > 0)

    def alpha(
        self, i: int, guards: list[tuple[int, Guard]], v: list[ParityObjective], q
    ):
        epsilons: list[tuple[Symbol, int]] = []
        constraints: list[ExprRef] = []
        template = self._get_linear_template(f"alpha{i}_q{q}", len(self._system.vars))
        lp = Optimize()
        # force alpha_i_q to be non-negative
        non_negativity = (
            to_z3_expr(template[0].dot(self._system.vars) + template[1]) >= 0
        )
        lp.add(non_negativity)
        for v_j in enumerate(v, i):
            v_j_constraints, v_j_epsilons = self.v_j_constraint(
                i, v_j, guards, template
            )
            constraints.extend(v_j_constraints)
            epsilons.extend(v_j_epsilons)
            lp.add(constraints)

        if len(epsilons) == 0:
            # No premise is satisfiable, thus the synthesis has finished,
            # return 0 function and empty set of guards
            return ([[0.0] * len(self._system.vars)], 0.0), []

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
        z3_alpha_i_a, z3_alpha_i_b = parse_matrix(template[0]), to_z3_expr(template[1])
        alpha_i_a = [
            [z3_real_to_float(model[var]) for var in row] for row in z3_alpha_i_a
        ]
        alpha_i_b = z3_real_to_float(model[z3_alpha_i_b])

        if len(updated_guards) == len(guards):
            # No guards has been ranked, thus no solution synthesized
            raise RuntimeError(f"No solution for linear program computing alpha_{i}")

        # return alpha_i function and not ranked guards
        return (alpha_i_a, alpha_i_b), updated_guards

    # def synthesize(self, v: list[ParityObjective]):
    #     guards = list(enumerate(self._system.guards))
    #     alpha = []
    #     print("Alpha:", alpha)
    #     for i in range(len(v)):
    #         print(f"Synthesizing alpha_{i}")
    #         alpha_i, guards = self.alpha(i, guards)
    #         print(f"Done synthesizing alpha_{i}")
    #         alpha.append(alpha_i)
    #
    #         if guards == []:
    #             break
    #
    #     if len(guards) > 0:
    #         print("WARNING: Not all guards have been ranked")
    #
    #     return alpha

    def synthesize_dpa_based(self, q: list[int], v: list[ParityObjective]):
        guards = self._system.guards
        alpha = [{} for _ in range(len(v))]
        print("Alpha:", alpha)
        for s in q:
            # Fix q and then synthesize an SPPM for q
            # TODO: Include in guards:
            # - q assignment
            # - invariant
            # - finite state space for variables
            q_guards: list[tuple[int, Guard]] = list(
                enumerate(
                    filter(
                        lambda g: self.satisfiable(to_z3_dnf(g)),
                        map(
                            lambda g: And(
                                parse_conjunct(g).append(Eq(Add(Symbol("q"), -s), 0))
                            ),
                            guards,
                        ),
                    )
                )
            )
            for i in range(len(v)):
                print(f"Synthesizing alpha_{i}_q{s}")
                alpha_i, q_guards = self.alpha(i, q_guards, v, s)
                print(f"Done synthesizing alpha_{i}_q{s}")
                alpha[i].update({s: alpha_i})

                if q_guards == []:
                    break

            if len(q_guards) > 0:
                print("WARNING: Not all guards have been ranked")
        return alpha
