# Generated from Prism.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .PrismParser import PrismParser
else:
    from PrismParser import PrismParser

# This class defines a complete listener for a parse tree produced by PrismParser.
class PrismListener(ParseTreeListener):

    # Enter a parse tree produced by PrismParser#expr_neg.
    def enterExpr_neg(self, ctx:PrismParser.Expr_negContext):
        pass

    # Exit a parse tree produced by PrismParser#expr_neg.
    def exitExpr_neg(self, ctx:PrismParser.Expr_negContext):
        pass


    # Enter a parse tree produced by PrismParser#expr_sub.
    def enterExpr_sub(self, ctx:PrismParser.Expr_subContext):
        pass

    # Exit a parse tree produced by PrismParser#expr_sub.
    def exitExpr_sub(self, ctx:PrismParser.Expr_subContext):
        pass


    # Enter a parse tree produced by PrismParser#expr_par.
    def enterExpr_par(self, ctx:PrismParser.Expr_parContext):
        pass

    # Exit a parse tree produced by PrismParser#expr_par.
    def exitExpr_par(self, ctx:PrismParser.Expr_parContext):
        pass


    # Enter a parse tree produced by PrismParser#expr_div.
    def enterExpr_div(self, ctx:PrismParser.Expr_divContext):
        pass

    # Exit a parse tree produced by PrismParser#expr_div.
    def exitExpr_div(self, ctx:PrismParser.Expr_divContext):
        pass


    # Enter a parse tree produced by PrismParser#expr_add.
    def enterExpr_add(self, ctx:PrismParser.Expr_addContext):
        pass

    # Exit a parse tree produced by PrismParser#expr_add.
    def exitExpr_add(self, ctx:PrismParser.Expr_addContext):
        pass


    # Enter a parse tree produced by PrismParser#expr_num.
    def enterExpr_num(self, ctx:PrismParser.Expr_numContext):
        pass

    # Exit a parse tree produced by PrismParser#expr_num.
    def exitExpr_num(self, ctx:PrismParser.Expr_numContext):
        pass


    # Enter a parse tree produced by PrismParser#expr_var.
    def enterExpr_var(self, ctx:PrismParser.Expr_varContext):
        pass

    # Exit a parse tree produced by PrismParser#expr_var.
    def exitExpr_var(self, ctx:PrismParser.Expr_varContext):
        pass


    # Enter a parse tree produced by PrismParser#expr_min.
    def enterExpr_min(self, ctx:PrismParser.Expr_minContext):
        pass

    # Exit a parse tree produced by PrismParser#expr_min.
    def exitExpr_min(self, ctx:PrismParser.Expr_minContext):
        pass


    # Enter a parse tree produced by PrismParser#expr_max.
    def enterExpr_max(self, ctx:PrismParser.Expr_maxContext):
        pass

    # Exit a parse tree produced by PrismParser#expr_max.
    def exitExpr_max(self, ctx:PrismParser.Expr_maxContext):
        pass


    # Enter a parse tree produced by PrismParser#expr_mul.
    def enterExpr_mul(self, ctx:PrismParser.Expr_mulContext):
        pass

    # Exit a parse tree produced by PrismParser#expr_mul.
    def exitExpr_mul(self, ctx:PrismParser.Expr_mulContext):
        pass


    # Enter a parse tree produced by PrismParser#mdp.
    def enterMdp(self, ctx:PrismParser.MdpContext):
        pass

    # Exit a parse tree produced by PrismParser#mdp.
    def exitMdp(self, ctx:PrismParser.MdpContext):
        pass


    # Enter a parse tree produced by PrismParser#dtmc.
    def enterDtmc(self, ctx:PrismParser.DtmcContext):
        pass

    # Exit a parse tree produced by PrismParser#dtmc.
    def exitDtmc(self, ctx:PrismParser.DtmcContext):
        pass


    # Enter a parse tree produced by PrismParser#range.
    def enterRange(self, ctx:PrismParser.RangeContext):
        pass

    # Exit a parse tree produced by PrismParser#range.
    def exitRange(self, ctx:PrismParser.RangeContext):
        pass


    # Enter a parse tree produced by PrismParser#t_int.
    def enterT_int(self, ctx:PrismParser.T_intContext):
        pass

    # Exit a parse tree produced by PrismParser#t_int.
    def exitT_int(self, ctx:PrismParser.T_intContext):
        pass


    # Enter a parse tree produced by PrismParser#t_double.
    def enterT_double(self, ctx:PrismParser.T_doubleContext):
        pass

    # Exit a parse tree produced by PrismParser#t_double.
    def exitT_double(self, ctx:PrismParser.T_doubleContext):
        pass


    # Enter a parse tree produced by PrismParser#t_float.
    def enterT_float(self, ctx:PrismParser.T_floatContext):
        pass

    # Exit a parse tree produced by PrismParser#t_float.
    def exitT_float(self, ctx:PrismParser.T_floatContext):
        pass


    # Enter a parse tree produced by PrismParser#t_bool.
    def enterT_bool(self, ctx:PrismParser.T_boolContext):
        pass

    # Exit a parse tree produced by PrismParser#t_bool.
    def exitT_bool(self, ctx:PrismParser.T_boolContext):
        pass


    # Enter a parse tree produced by PrismParser#t_range.
    def enterT_range(self, ctx:PrismParser.T_rangeContext):
        pass

    # Exit a parse tree produced by PrismParser#t_range.
    def exitT_range(self, ctx:PrismParser.T_rangeContext):
        pass


    # Enter a parse tree produced by PrismParser#const_init_expr.
    def enterConst_init_expr(self, ctx:PrismParser.Const_init_exprContext):
        pass

    # Exit a parse tree produced by PrismParser#const_init_expr.
    def exitConst_init_expr(self, ctx:PrismParser.Const_init_exprContext):
        pass


    # Enter a parse tree produced by PrismParser#const_init_type.
    def enterConst_init_type(self, ctx:PrismParser.Const_init_typeContext):
        pass

    # Exit a parse tree produced by PrismParser#const_init_type.
    def exitConst_init_type(self, ctx:PrismParser.Const_init_typeContext):
        pass


    # Enter a parse tree produced by PrismParser#var_init_range.
    def enterVar_init_range(self, ctx:PrismParser.Var_init_rangeContext):
        pass

    # Exit a parse tree produced by PrismParser#var_init_range.
    def exitVar_init_range(self, ctx:PrismParser.Var_init_rangeContext):
        pass


    # Enter a parse tree produced by PrismParser#var_init_expr.
    def enterVar_init_expr(self, ctx:PrismParser.Var_init_exprContext):
        pass

    # Exit a parse tree produced by PrismParser#var_init_expr.
    def exitVar_init_expr(self, ctx:PrismParser.Var_init_exprContext):
        pass


    # Enter a parse tree produced by PrismParser#var_init_type.
    def enterVar_init_type(self, ctx:PrismParser.Var_init_typeContext):
        pass

    # Exit a parse tree produced by PrismParser#var_init_type.
    def exitVar_init_type(self, ctx:PrismParser.Var_init_typeContext):
        pass


    # Enter a parse tree produced by PrismParser#global_var.
    def enterGlobal_var(self, ctx:PrismParser.Global_varContext):
        pass

    # Exit a parse tree produced by PrismParser#global_var.
    def exitGlobal_var(self, ctx:PrismParser.Global_varContext):
        pass


    # Enter a parse tree produced by PrismParser#label.
    def enterLabel(self, ctx:PrismParser.LabelContext):
        pass

    # Exit a parse tree produced by PrismParser#label.
    def exitLabel(self, ctx:PrismParser.LabelContext):
        pass


    # Enter a parse tree produced by PrismParser#lt.
    def enterLt(self, ctx:PrismParser.LtContext):
        pass

    # Exit a parse tree produced by PrismParser#lt.
    def exitLt(self, ctx:PrismParser.LtContext):
        pass


    # Enter a parse tree produced by PrismParser#le.
    def enterLe(self, ctx:PrismParser.LeContext):
        pass

    # Exit a parse tree produced by PrismParser#le.
    def exitLe(self, ctx:PrismParser.LeContext):
        pass


    # Enter a parse tree produced by PrismParser#eq.
    def enterEq(self, ctx:PrismParser.EqContext):
        pass

    # Exit a parse tree produced by PrismParser#eq.
    def exitEq(self, ctx:PrismParser.EqContext):
        pass


    # Enter a parse tree produced by PrismParser#ge.
    def enterGe(self, ctx:PrismParser.GeContext):
        pass

    # Exit a parse tree produced by PrismParser#ge.
    def exitGe(self, ctx:PrismParser.GeContext):
        pass


    # Enter a parse tree produced by PrismParser#gt.
    def enterGt(self, ctx:PrismParser.GtContext):
        pass

    # Exit a parse tree produced by PrismParser#gt.
    def exitGt(self, ctx:PrismParser.GtContext):
        pass


    # Enter a parse tree produced by PrismParser#ne.
    def enterNe(self, ctx:PrismParser.NeContext):
        pass

    # Exit a parse tree produced by PrismParser#ne.
    def exitNe(self, ctx:PrismParser.NeContext):
        pass


    # Enter a parse tree produced by PrismParser#guard_or.
    def enterGuard_or(self, ctx:PrismParser.Guard_orContext):
        pass

    # Exit a parse tree produced by PrismParser#guard_or.
    def exitGuard_or(self, ctx:PrismParser.Guard_orContext):
        pass


    # Enter a parse tree produced by PrismParser#guard_par.
    def enterGuard_par(self, ctx:PrismParser.Guard_parContext):
        pass

    # Exit a parse tree produced by PrismParser#guard_par.
    def exitGuard_par(self, ctx:PrismParser.Guard_parContext):
        pass


    # Enter a parse tree produced by PrismParser#guard_constraint.
    def enterGuard_constraint(self, ctx:PrismParser.Guard_constraintContext):
        pass

    # Exit a parse tree produced by PrismParser#guard_constraint.
    def exitGuard_constraint(self, ctx:PrismParser.Guard_constraintContext):
        pass


    # Enter a parse tree produced by PrismParser#guard_neg.
    def enterGuard_neg(self, ctx:PrismParser.Guard_negContext):
        pass

    # Exit a parse tree produced by PrismParser#guard_neg.
    def exitGuard_neg(self, ctx:PrismParser.Guard_negContext):
        pass


    # Enter a parse tree produced by PrismParser#guard_false.
    def enterGuard_false(self, ctx:PrismParser.Guard_falseContext):
        pass

    # Exit a parse tree produced by PrismParser#guard_false.
    def exitGuard_false(self, ctx:PrismParser.Guard_falseContext):
        pass


    # Enter a parse tree produced by PrismParser#guard_true.
    def enterGuard_true(self, ctx:PrismParser.Guard_trueContext):
        pass

    # Exit a parse tree produced by PrismParser#guard_true.
    def exitGuard_true(self, ctx:PrismParser.Guard_trueContext):
        pass


    # Enter a parse tree produced by PrismParser#guard_and.
    def enterGuard_and(self, ctx:PrismParser.Guard_andContext):
        pass

    # Exit a parse tree produced by PrismParser#guard_and.
    def exitGuard_and(self, ctx:PrismParser.Guard_andContext):
        pass


    # Enter a parse tree produced by PrismParser#var_update.
    def enterVar_update(self, ctx:PrismParser.Var_updateContext):
        pass

    # Exit a parse tree produced by PrismParser#var_update.
    def exitVar_update(self, ctx:PrismParser.Var_updateContext):
        pass


    # Enter a parse tree produced by PrismParser#state_update.
    def enterState_update(self, ctx:PrismParser.State_updateContext):
        pass

    # Exit a parse tree produced by PrismParser#state_update.
    def exitState_update(self, ctx:PrismParser.State_updateContext):
        pass


    # Enter a parse tree produced by PrismParser#state_update_single.
    def enterState_update_single(self, ctx:PrismParser.State_update_singleContext):
        pass

    # Exit a parse tree produced by PrismParser#state_update_single.
    def exitState_update_single(self, ctx:PrismParser.State_update_singleContext):
        pass


    # Enter a parse tree produced by PrismParser#state_update_distr.
    def enterState_update_distr(self, ctx:PrismParser.State_update_distrContext):
        pass

    # Exit a parse tree produced by PrismParser#state_update_distr.
    def exitState_update_distr(self, ctx:PrismParser.State_update_distrContext):
        pass


    # Enter a parse tree produced by PrismParser#guarded_command.
    def enterGuarded_command(self, ctx:PrismParser.Guarded_commandContext):
        pass

    # Exit a parse tree produced by PrismParser#guarded_command.
    def exitGuarded_command(self, ctx:PrismParser.Guarded_commandContext):
        pass


    # Enter a parse tree produced by PrismParser#module.
    def enterModule(self, ctx:PrismParser.ModuleContext):
        pass

    # Exit a parse tree produced by PrismParser#module.
    def exitModule(self, ctx:PrismParser.ModuleContext):
        pass


    # Enter a parse tree produced by PrismParser#preamble.
    def enterPreamble(self, ctx:PrismParser.PreambleContext):
        pass

    # Exit a parse tree produced by PrismParser#preamble.
    def exitPreamble(self, ctx:PrismParser.PreambleContext):
        pass


    # Enter a parse tree produced by PrismParser#init.
    def enterInit(self, ctx:PrismParser.InitContext):
        pass

    # Exit a parse tree produced by PrismParser#init.
    def exitInit(self, ctx:PrismParser.InitContext):
        pass


    # Enter a parse tree produced by PrismParser#file.
    def enterFile(self, ctx:PrismParser.FileContext):
        pass

    # Exit a parse tree produced by PrismParser#file.
    def exitFile(self, ctx:PrismParser.FileContext):
        pass



del PrismParser