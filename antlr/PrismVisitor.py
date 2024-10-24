# Generated from Prism.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .PrismParser import PrismParser
else:
    from PrismParser import PrismParser

# This class defines a complete generic visitor for a parse tree produced by PrismParser.

class PrismVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by PrismParser#expr_neg.
    def visitExpr_neg(self, ctx:PrismParser.Expr_negContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#expr_sub.
    def visitExpr_sub(self, ctx:PrismParser.Expr_subContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#expr_par.
    def visitExpr_par(self, ctx:PrismParser.Expr_parContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#expr_div.
    def visitExpr_div(self, ctx:PrismParser.Expr_divContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#expr_add.
    def visitExpr_add(self, ctx:PrismParser.Expr_addContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#expr_num.
    def visitExpr_num(self, ctx:PrismParser.Expr_numContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#expr_var.
    def visitExpr_var(self, ctx:PrismParser.Expr_varContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#expr_min.
    def visitExpr_min(self, ctx:PrismParser.Expr_minContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#expr_max.
    def visitExpr_max(self, ctx:PrismParser.Expr_maxContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#expr_mul.
    def visitExpr_mul(self, ctx:PrismParser.Expr_mulContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#mdp.
    def visitMdp(self, ctx:PrismParser.MdpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#dtmc.
    def visitDtmc(self, ctx:PrismParser.DtmcContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#range.
    def visitRange(self, ctx:PrismParser.RangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#t_int.
    def visitT_int(self, ctx:PrismParser.T_intContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#t_double.
    def visitT_double(self, ctx:PrismParser.T_doubleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#t_float.
    def visitT_float(self, ctx:PrismParser.T_floatContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#t_bool.
    def visitT_bool(self, ctx:PrismParser.T_boolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#t_range.
    def visitT_range(self, ctx:PrismParser.T_rangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#const_init_expr.
    def visitConst_init_expr(self, ctx:PrismParser.Const_init_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#const_init_type.
    def visitConst_init_type(self, ctx:PrismParser.Const_init_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#var_init_range.
    def visitVar_init_range(self, ctx:PrismParser.Var_init_rangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#var_init_expr.
    def visitVar_init_expr(self, ctx:PrismParser.Var_init_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#var_init_type.
    def visitVar_init_type(self, ctx:PrismParser.Var_init_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#global_var.
    def visitGlobal_var(self, ctx:PrismParser.Global_varContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#label.
    def visitLabel(self, ctx:PrismParser.LabelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#lt.
    def visitLt(self, ctx:PrismParser.LtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#le.
    def visitLe(self, ctx:PrismParser.LeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#eq.
    def visitEq(self, ctx:PrismParser.EqContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#ge.
    def visitGe(self, ctx:PrismParser.GeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#gt.
    def visitGt(self, ctx:PrismParser.GtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#ne.
    def visitNe(self, ctx:PrismParser.NeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#guard_or.
    def visitGuard_or(self, ctx:PrismParser.Guard_orContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#guard_par.
    def visitGuard_par(self, ctx:PrismParser.Guard_parContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#guard_constraint.
    def visitGuard_constraint(self, ctx:PrismParser.Guard_constraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#guard_neg.
    def visitGuard_neg(self, ctx:PrismParser.Guard_negContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#guard_false.
    def visitGuard_false(self, ctx:PrismParser.Guard_falseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#guard_true.
    def visitGuard_true(self, ctx:PrismParser.Guard_trueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#guard_and.
    def visitGuard_and(self, ctx:PrismParser.Guard_andContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#var_update.
    def visitVar_update(self, ctx:PrismParser.Var_updateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#state_update.
    def visitState_update(self, ctx:PrismParser.State_updateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#state_update_single.
    def visitState_update_single(self, ctx:PrismParser.State_update_singleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#state_update_distr.
    def visitState_update_distr(self, ctx:PrismParser.State_update_distrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#guarded_command.
    def visitGuarded_command(self, ctx:PrismParser.Guarded_commandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#module.
    def visitModule(self, ctx:PrismParser.ModuleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#preamble.
    def visitPreamble(self, ctx:PrismParser.PreambleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#init.
    def visitInit(self, ctx:PrismParser.InitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismParser#file.
    def visitFile(self, ctx:PrismParser.FileContext):
        return self.visitChildren(ctx)



del PrismParser