from itertools import chain
import itertools
import re
from typing import Optional
from sympy import (
    And,
    Expr,
    LessThan,
    Matrix,
    StrictLessThan,
    Symbol,
    Unequality,
    false,
    linear_eq_to_matrix,
    true,
)
from sympy.logic.boolalg import Boolean
from reactive_module import (
    GuardedCommand,
    NonDeterministicStochasticUpdate,
    ProbabilisticUpdate,
    ReactiveModule,
    StochasticUpdate,
    Update,
)
from antlr.PrismParser import PrismParser
from antlr.PrismVisitor import PrismVisitor
from utils import (
    equations_to_update,
    first,
    first_with_exception,
    fst,
    negate_constraint,
    satisfiable,
    snd,
    to_z3_dnf,
    update_var_map,
)


class Max:
    def __init__(self, a: Expr, b: Expr):
        self.a = a
        self.b = b

    @property
    def e1(self):
        return self.a

    @property
    def e2(self):
        return self.b


class Min:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    @property
    def e1(self):
        return self.a

    @property
    def e2(self):
        return self.b


class PrismEval(PrismVisitor):
    def __init__(self):
        self.variables: dict[str, float] = {}
        self.constants: dict[str, float] = {}
        self.environment: dict[str, float] = {}
        self.guarded_commands: list[GuardedCommand] = []

    @property
    def vars(self) -> tuple[Symbol, ...]:
        return tuple(map(Symbol, self.variables.keys()))

    def visitExpr_num(self, ctx: PrismParser.Expr_numContext):
        return float(ctx.NUMBER().getText())

    def visitExpr_var(self, ctx: PrismParser.Expr_varContext):
        return self.environment.get(ctx.ID().getText(), Symbol(ctx.ID().getText()))

    def visitExpr_add(self, ctx: PrismParser.Expr_addContext):
        return self.visit(ctx.expr(0)) + self.visit(ctx.expr(1))

    def visitExpr_sub(self, ctx: PrismParser.Expr_subContext):
        return self.visit(ctx.expr(0)) - self.visit(ctx.expr(1))

    def visitExpr_mul(self, ctx: PrismParser.Expr_mulContext):
        return self.visit(ctx.expr(0)) * self.visit(ctx.expr(1))

    def visitExpr_div(self, ctx: PrismParser.Expr_divContext):
        return self.visit(ctx.expr(0)) / self.visit(ctx.expr(1))

    def visitExpr_min(self, ctx: PrismParser.Expr_minContext):
        e1 = self.visit(ctx.expr(0))
        e2 = self.visit(ctx.expr(1))
        if isinstance(e1, float) and isinstance(e2, float):
            return min(e1, e2)
        return Min(e1, e2)

    def visitExpr_max(self, ctx: PrismParser.Expr_maxContext):
        e1 = self.visit(ctx.expr(0))
        e2 = self.visit(ctx.expr(1))
        if isinstance(e1, float) and isinstance(e2, float):
            return min(e1, e2)
        return Max(e1, e2)

    def visitExpr_par(self, ctx: PrismParser.Expr_parContext):
        return self.visit(ctx.expr())

    def visitExpr_neg(self, ctx: PrismParser.Expr_negContext):
        return -self.visit(ctx.expr())

    def visitConst_init_expr(self, ctx: PrismParser.Const_init_exprContext):
        value = self.visit(ctx.expr())
        id = ctx.ID().getText()
        update_var_map([Symbol(id)])
        self.constants[id] = value
        self.environment[id] = value
        return None

    def visitConst_init_type(self, ctx: PrismParser.Const_init_typeContext):
        match ctx.type_().getText():
            case "bool" | "int" | "float":
                value = 0.0
            case _:
                raise ValueError(f"Invalid constant type: {ctx.type_().getText()}")
        id = ctx.ID().getText()
        update_var_map([Symbol(id)])
        self.constants[id] = value
        self.environment[id] = value
        return None

    def visitVar_init_expr(self, ctx: PrismParser.Var_init_exprContext):
        value = self.visit(ctx.expr())
        id = ctx.ID().getText()
        update_var_map([Symbol(id)])
        self.variables[id] = value
        return None

    def visitVar_init_range(self, ctx: PrismParser.Var_init_rangeContext):
        value = self.visit(ctx.range_().expr(0))
        id = ctx.ID().getText()
        update_var_map([Symbol(id)])
        self.variables[id] = value
        return None

    def visitVar_init_type(self, ctx: PrismParser.Var_init_typeContext):
        match ctx.type_().getText():
            case "bool" | "int" | "float":
                value = 0.0
            case _:
                raise ValueError(f"Invalid variable type: {ctx.type_().getText()}")
        id = ctx.ID().getText()
        update_var_map([Symbol(id)])
        self.variables[id] = value
        return None

    def visitGlobal_var(self, ctx: PrismParser.Global_varContext):
        return self.visit(ctx.var_init())

    def visitLabel(self, ctx: PrismParser.LabelContext):
        return [ctx.ID().getText()] if ctx.ID() is not None else []

    def visitGuard_true(self, ctx: PrismParser.Guard_trueContext):
        return [true]

    def visitGuard_false(self, ctx: PrismParser.Guard_falseContext):
        return [false]

    def visitGuard_constraint(self, ctx: PrismParser.Guard_constraintContext):
        match ctx.ordering().getText():
            case "<":
                return [
                    StrictLessThan(self.visit(ctx.expr(0)) - self.visit(ctx.expr(1)), 0)
                ]
            case "<=":
                return [LessThan(self.visit(ctx.expr(0)) - self.visit(ctx.expr(1)), 0)]
            case ">":
                return [
                    StrictLessThan(self.visit(ctx.expr(1)) - self.visit(ctx.expr(0)), 0)
                ]
            case ">=":
                return [LessThan(self.visit(ctx.expr(1)) - self.visit(ctx.expr(0)), 0)]
            case "=":
                return [
                    And(
                        LessThan(self.visit(ctx.expr(0)) - self.visit(ctx.expr(1)), 0),
                        LessThan(self.visit(ctx.expr(1)) - self.visit(ctx.expr(0)), 0),
                    )
                ]
            case "!=":
                return [
                    And(
                        LessThan(self.visit(ctx.expr(0)) - self.visit(ctx.expr(1)), 0),
                        LessThan(self.visit(ctx.expr(1)) - self.visit(ctx.expr(0)), 0),
                    )
                ]
            case _:
                print(ctx.ordering().getText())
                print(ctx.ordering())
                raise ValueError(f"Invalid ordering: {ctx.ordering().getText()}")

    def visitGuard_neg(self, ctx: PrismParser.Guard_negContext):
        guard: list[And] = self.visit(ctx.guard())
        cnf = list(
            map(
                lambda conjunction: list(
                    map(
                        negate_constraint,
                        conjunction.args,
                    )
                ),
                guard,
            )
        )
        dnf = cnf[0]
        for disjunction in cnf[1:]:
            dnf = list(
                filter(
                    lambda g: satisfiable(to_z3_dnf(g)),
                    map(
                        lambda g_constr: And(fst(g_constr), snd(g_constr)),
                        itertools.product(dnf, disjunction),
                    ),
                )
            )
        return dnf

    def visitGuard_and(self, ctx: PrismParser.Guard_andContext):
        g1 = self.visit(ctx.guard(0))
        g2 = self.visit(ctx.guard(1))
        return [And(g1c, g2c) for (g1c, g2c) in itertools.product(g1, g2)]

    def visitGuard_or(self, ctx: PrismParser.Guard_orContext):
        g1 = self.visit(ctx.guard(0))
        g2 = self.visit(ctx.guard(1))
        return g1 + g2

    def visitGuard_par(self, ctx: PrismParser.Guard_parContext):
        return self.visit(ctx.guard())

    def visitVar_update(self, ctx: PrismParser.Var_updateContext):
        return {ctx.ID().getText(): self.visit(ctx.expr())}

    def visitState_update(self, ctx: PrismParser.State_updateContext):
        var_updates: dict[str, Expr | Min | Max] = {
            k: v
            for var_update in ctx.var_update()
            for k, v in self.visit(var_update).items()
        }
        return [
            var_updates.get(name, Symbol(name)) for name, _ in self.variables.items()
        ]

    def visitState_update_single(self, ctx: PrismParser.State_update_singleContext):
        return [(1.0, self.visit(ctx.state_update()))]

    def visitState_update_distr(self, ctx: PrismParser.State_update_distrContext):
        return list(
            map(
                lambda ctx: (self.visit(ctx[0]), self.visit(ctx[1])),
                zip(ctx.expr(), ctx.state_update()),
            )
        )

    def _replace_var_update(
        self, state_update: list[Expr | Min | Max], var: int, expr: Expr
    ):
        return state_update[:var] + [expr] + state_update[var + 1 :]

    def _replace_state_update(
        self,
        distribution: list[tuple[float, list[Expr | Min | Max]]],
        index: int,
        update: tuple[float, list[Expr | Min | Max]],
    ):
        return distribution[:index] + [update] + distribution[index + 1 :]

    def _add_constraint(self, guard, constraint):
        return list(map(lambda g: And(g, constraint), guard))

    def visitGuarded_command(self, ctx: PrismParser.Guarded_commandContext):
        label = self.visit(ctx.label())
        guard = self.visit(ctx.guard())
        state_update_distribution: list[tuple[float, list[Expr | Min | Max]]] = (
            self.visit(ctx.state_update_distribution())
        )
        guarded_commands = [(guard, state_update_distribution)]
        for i, (prob, state_update) in enumerate(state_update_distribution):
            for j, var_update in enumerate(state_update):
                if isinstance(var_update, Max):
                    guarded_commands = list(
                        chain.from_iterable(
                            map(
                                lambda gc: [
                                    # e2 - e1 <= 0 -> e1
                                    (
                                        self._add_constraint(
                                            fst(gc),
                                            LessThan(var_update.e2 - var_update.e1, 0),
                                        ),
                                        self._replace_state_update(
                                            snd(gc),
                                            i,
                                            (
                                                prob,
                                                self._replace_var_update(
                                                    snd(gc)[i][1], j, var_update.e1
                                                ),
                                            ),
                                        ),
                                    ),
                                    # e1 - e2 < 0: e2
                                    (
                                        self._add_constraint(
                                            fst(gc),
                                            LessThan(var_update.e1 - var_update.e2, 0),
                                        ),
                                        self._replace_state_update(
                                            snd(gc),
                                            i,
                                            (
                                                prob,
                                                self._replace_var_update(
                                                    snd(gc)[i][1], j, var_update.e2
                                                ),
                                            ),
                                        ),
                                    ),
                                ],
                                guarded_commands,
                            )
                        )
                    )
                elif isinstance(var_update, Min):
                    guarded_commands = list(
                        chain.from_iterable(
                            map(
                                lambda gc: [
                                    # e1 - e2 <= 0: e1
                                    (
                                        self._add_constraint(
                                            fst(gc),
                                            LessThan(var_update.e1 - var_update.e2, 0),
                                        ),
                                        self._replace_state_update(
                                            snd(gc),
                                            i,
                                            (
                                                prob,
                                                self._replace_var_update(
                                                    snd(gc)[i][1], j, var_update.e1
                                                ),
                                            ),
                                        ),
                                    ),
                                    # e2 - e1 < 0 -> e2
                                    (
                                        self._add_constraint(
                                            fst(gc),
                                            LessThan(var_update.e2 - var_update.e1, 0),
                                        ),
                                        self._replace_state_update(
                                            snd(gc),
                                            i,
                                            (
                                                prob,
                                                self._replace_var_update(
                                                    snd(gc)[i][1], j, var_update.e2
                                                ),
                                            ),
                                        ),
                                    ),
                                ],
                                guarded_commands,
                            )
                        )
                    )

        guarded_commands = list(
            map(
                lambda gc: (fst(gc), self._to_stochastic_update(snd(gc))),
                guarded_commands,
            )
        )

        return list(
            chain.from_iterable(
                map(
                    lambda gc: map(
                        lambda conjunction: GuardedCommand(label, conjunction, [gc[1]]),
                        filter(
                            lambda conjunction: satisfiable(to_z3_dnf(conjunction)),
                            gc[0],
                        ),
                    ),
                    guarded_commands,
                ),
            )
        )

    def _to_stochastic_update(
        self,
        state_update_distribution: list[tuple[float, list[Expr | Min | Max]]],
    ) -> StochasticUpdate:
        return list(
            map(
                lambda x: (
                    fst(x),
                    equations_to_update(
                        snd(x),
                        self.vars,
                    ),
                ),
                state_update_distribution,
            )
        )

    def visitModule(self, ctx: PrismParser.ModuleContext):
        for var in ctx.var_init():
            self.visit(var)
        guarded_commands = list(
            chain.from_iterable(map(self.visit, ctx.guarded_command()))
        )
        return ReactiveModule(
            [tuple(self.variables.values())],
            tuple(map(lambda var: Symbol(var), self.variables.keys())),
            guarded_commands,
        )

    def visitPreamble(self, ctx: PrismParser.PreambleContext):
        for const in ctx.const_init():
            self.visit(const)
        for var in ctx.global_var():
            self.visit(var)
        return None

    def visitFile(self, ctx: PrismParser.FileContext):
        self.visit(ctx.preamble())
        return self.visit(ctx.module())
