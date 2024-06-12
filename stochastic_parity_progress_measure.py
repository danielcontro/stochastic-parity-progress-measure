from functools import partial
from sympy.logic.boolalg import Boolean
from reactive_module import Guard, ProgramVariables, ReactiveModule

import itertools

from z3 import (
    And,
    BoolRef,
    ExprRef,
    ModelRef,
    Optimize,
    Solver,
    sat,
    unsat,
)
from sympy import Expr, Symbol, Matrix, linear_eq_to_matrix, zeros

from utils import (
    VarMap,
    get_z3_var_map,
    parse_DNF,
    parse_conjunct,
    parse_constraint,
    parse_expr,
    parse_matrix,
    unzip,
    update_var_map,
)

PriorityCondition = Boolean


class SPPM:
    def __init__(self, rm: ReactiveModule, v: list[PriorityCondition]) -> None:
        """
        Methods for computing the stochastic parity progress measure for a
        given reactive module and a given property (passed as boolean indicator
        functions for priority levels).
        """
        self._counter = 0
        self._system = rm
        update_var_map(rm._vars)
        self._fresh_vars = []
        self._v = v

    def fresh_var(self, prefix: str) -> Symbol:
        self._counter += 1
        self._fresh_vars.append(Symbol(prefix + "_(" + str(self._counter) + ")"))
        update_var_map([self._fresh_vars[-1]])
        return self._fresh_vars[-1]

    def fresh_var_vec(self, prefix: str, n: int, row=False) -> Matrix:
        row, col = (1, n) if row else (n, 1)
        return Matrix(
            row, col, lambda i, j: self.fresh_var(prefix + "_" + str(j if row else i))
        )

    def fresh_var_mat(
        self, prefix: str, shape: tuple[int, int]
    ) -> tuple[Matrix, list[Symbol]]:
        return Matrix(
            *shape, lambda i, j: self.fresh_var(prefix + "_" + str(i) + "_" + str(j))
        ), self._fresh_vars[-shape[0] * shape[1] :]

    def satisfiable(self, query) -> bool:
        solver = Solver()
        solver.add(query)
        return solver.check() == sat

    def farkas_constraint(
        self, a_t: Matrix, b_t: Matrix, c: Matrix, d: Expr, z: Matrix
    ) -> BoolRef:
        # If there's only one program variable there are only two constraints
        # (c and a_t*z are simple expressions)
        if len(self._system.vars) == 1:
            assert isinstance(c, Expr)
            return And(
                parse_expr(a_t * z) == parse_expr(c),
                parse_expr(b_t.dot(z)) <= parse_expr(d),
            )

        z3_at_z = parse_matrix(a_t * z)
        z3_c = parse_matrix(c)

        return And(
            [z3_at_z[i][0] == z3_c[i][0] for i in range(len(z3_at_z))]
            + [parse_expr(b_t.dot(z)) <= parse_expr(d)]
        )

    def farkas_lemma(
        self, a: Matrix, b: Matrix, c: Matrix, d: Expr, simplified: bool = True
    ):
        z = self.fresh_var_vec("z", a.shape[0])
        if not simplified:
            pass
        farkas_constraint: ExprRef = self.farkas_constraint(
            a.transpose(), b.transpose(), c, d, z
        )
        return farkas_constraint

    def v_j_constraint(
        self,
        j: int,
        guards: list[tuple[int, Guard]],
        template: tuple[Matrix, Symbol],
        prog_vars: ProgramVariables,
    ) -> tuple[list[ExprRef], list[tuple[Symbol, int]]]:
        print()
        print("V[", j, "]:", self._v[j])
        a_template, _ = template
        constraints: list[ExprRef] = []
        decrement_vars: list[tuple[Symbol, int]] = []
        v_j_conjuncts = list(enumerate(parse_DNF(self._v[j])))
        print("V_j conjuncts:", v_j_conjuncts)
        print("Guards :", [g for g in guards])

        for guard in guards:
            print()
            print()
            print("Guard:", guard)
            guard_conjuncts = parse_DNF(guard[1])
            print("Guard conjuncts:", guard_conjuncts)
            print("V_j conjuncts:", v_j_conjuncts)

            for guard_conjunct, v_j_conjunct in itertools.product(
                guard_conjuncts, v_j_conjuncts
            ):
                print()
                print("Guard_conj:", guard_conjunct)
                print("V_j_conj:", v_j_conjunct)
                parsed_guard_conj = parse_conjunct(guard_conjunct)
                parsed_v_j_conj = parse_conjunct(v_j_conjunct[1])
                print("Parsed guard conjunct:", parsed_guard_conj)
                print("Parsed V_j conjunct:", parsed_v_j_conj)
                print("Constraints", (parsed_guard_conj + parsed_v_j_conj))
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
                print("Premise constraints:", premise_constraints)
                a, b = linear_eq_to_matrix(premise_constraints, prog_vars)
                print("A:", a)
                print("b:", b)
                assert isinstance(a, Matrix) and isinstance(b, Matrix)

                ax_z3 = parse_matrix(a * Matrix(prog_vars))
                b_z3 = parse_matrix(b)

                # Check if the premise is satisfiable, otherwise skip
                premise = And([ax_z3[i][0] <= b_z3[i][0] for i in range(len(ax_z3))])
                print("Premise:", premise)
                if not self.satisfiable(premise):
                    print("Premise not satisfiable, skipped V_" + str(j))
                    continue

                actions_transitions = self._system.transitions(guard[0])

                if j % 2:
                    # same epsilon decrease for all the possible actions
                    eps = self.fresh_var(
                        "epsilon_" + str(j) + "_" + str(v_j_conjunct[0])
                    )
                    decrement_vars.append((eps, guard[0]))
                    print("New decrement var:", eps)
                    z3_eps = get_z3_var_map()[eps.name]
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
                            zeros(len(prog_vars)),
                        )
                        - a_template
                    )

                    # d = -a_template * \sum(p_i * b_i) (- epsilon_g if j is odd
                    d = -a_template.dot(
                        sum(
                            map(
                                lambda p_i, b_i: p_i * b_i,
                                distribution,
                                updates_b,
                            ),
                            zeros(len(prog_vars), 1),
                        )
                    )

                    if j % 2:
                        # Odd priority level, add epsilon decrease to constraint
                        d = d - eps

                    constraints.append(self.farkas_lemma(a, b, c_t.transpose(), d))
        print("V[", j, "] done")
        return constraints, decrement_vars

    def _is_ranked_guard(
        self, var_map: VarMap, model: ModelRef, eps: tuple[Symbol, int]
    ) -> bool:
        z3_symb = var_map[eps[0].name]
        return (
            float(model[z3_symb].as_string()) > 0.0
            if model[z3_symb] is not None
            else False
        )

    def alpha(self, i: int, guards: list[tuple[int, Guard]]):
        print("Synthesizing alpha_" + str(i))
        epsilons: list[tuple[Symbol, int]] = []
        constraints: list[ExprRef] = []
        template = (
            self.fresh_var_vec("alpha_" + str(i) + "_a", len(self._system.vars), True),
            self.fresh_var("alpha_" + str(i) + "_b"),
        )
        print("Template a: ", template[0])
        lp = Optimize()
        # force alpha to be non-negative
        lp.add(parse_expr(template[0].dot(self._system.vars) + template[1]) >= 0)
        for j in range(i, len(self._v)):
            v_j_constraints, v_j_epsilons = self.v_j_constraint(
                j, guards, template, self._system.vars
            )
            constraints.extend(v_j_constraints)
            epsilons.extend(v_j_epsilons)
            lp.add(constraints)

        print("Constraints:", constraints)
        print("Epsilons:", epsilons)
        objective_f = sum(map(parse_expr, map(lambda e: e[0], epsilons)), 0.0)
        print("objective function:", objective_f)
        lp.maximize(objective_f)
        if lp.check() == unsat:
            # No solution for linear program
            raise RuntimeError(
                "No solution for linear program computing alpha_" + str(i)
            )

        model = lp.model()
        print("Model:", model)
        var_map = get_z3_var_map()
        is_ranked_guard = partial(self._is_ranked_guard, var_map, model)
        ranked_guards_idx = list(map(lambda x: x[1], filter(is_ranked_guard, epsilons)))
        print("Ranked guards:", ranked_guards_idx)
        updated_guards = list(filter(lambda x: x[0] not in ranked_guards_idx, guards))
        z3_alpha_i_a, z3_alpha_i_b = parse_matrix(template[0]), parse_expr(template[1])
        alpha_i_a = [
            [float(model[var].as_string()) for var in row] for row in z3_alpha_i_a
        ]
        alpha_i_b = float(model[z3_alpha_i_b].as_string())

        print("Z3 alpha_i_a:", z3_alpha_i_a)
        print("Z3 alpha_i_b:", z3_alpha_i_b)
        print("Alpha_i_a:", alpha_i_a)
        print("Alpha_i_b:", alpha_i_b)
        # return alpha_i function and updated_guards (not ranked ones)
        print("alpha_" + str(i), "done")
        return (alpha_i_a, alpha_i_b), updated_guards

    def synthesize(self):
        guards = list(enumerate(self._system.guards))
        alpha = []
        for i in range(len(self._v)):
            alpha_i, guards = self.alpha(i, guards)
            alpha.append(alpha_i)

            if guards == []:
                break
        return alpha
