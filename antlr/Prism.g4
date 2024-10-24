grammar Prism;

// Lexer rules


// Operators
AND     : '&'   ;
OR      : '|'   ;
EQ      : '='   ;
NE      : '!='  ;
LT      : '<'   ;
LE      : '<='  ;
GT      : '>'   ;
GE      : '>='  ;
MINUS   : '-'   ;
PLUS    : '+'   ;
TIMES   : '*'   ;
DIV     : '/'   ;
NOT     : '!'   ;


// Model types
MDP   : 'mdp'   ;
DTMC  : 'dtmc'  ;

// Types
INT     : 'int'     ;
BOOL    : 'bool'    ;
DOUBLE  : 'double'  ;
FLOAT   : 'float'   ;

// Delimiters
LBRA      : '['   ;
RBRA      : ']'   ;
LPAR      : '('   ;
RPAR      : ')'   ;
TO        : '->'  ;
SEMICOLON : ';'   ;
COLON     : ':'   ;
RANGE     : '..'  ;
COMMA     : ','   ;
DOUBLE_QUOTE     : '"'   ;


// Keywords
CONST       : 'const'       ;
MODULE      : 'module'      ;
ENDMODULE   : 'endmodule'   ;
GLOBAL      : 'global'      ;
MIN         : 'min'         ;
MAX         : 'max'         ;
PRIME       : '\''          ;
TRUE        : 'true'        ;
FALSE       : 'false'       ;
INIT        : 'init'        ;
ENDINIT     : 'endinit'     ;
// REWARDS     : 'rewards'     ;
// ENDREWARDS  : 'endrewards'  ;
// FORMULA     : 'formula'     ;
// LABEL       : 'label'       ;

REWARDS : 'rewards' .*? 'endrewards' -> skip ;
FORMULA : 'formula' ~[;]* ';' -> skip ;
LABEL   : 'label' ~[;]* ';' -> skip ;
COMMENT : '//' ~[\r\n]* '\r'? '\n' -> skip ;
WS : [ \t\r\n]+ -> skip ;
ID  : [a-zA-Z] [a-zA-Z0-9_]* ;
NUMBER : [0-9]+ ('.'[0-9]+)? ;

// Parser rules

expr  : MIN LPAR expr COMMA expr RPAR # expr_min
      | MAX LPAR expr COMMA expr RPAR # expr_max
      | expr TIMES expr               # expr_mul
      | expr DIV expr                 # expr_div
      | expr PLUS expr                # expr_add
      | expr MINUS expr               # expr_sub
      | LPAR expr RPAR                # expr_par
      | MINUS expr                    # expr_neg
      | ID                            # expr_var
      | NUMBER                        # expr_num
      ;

model_type  : MDP   # mdp
            | DTMC  # dtmc
            ;

range : LBRA expr RANGE expr RBRA ;
type  : INT     # t_int
      | DOUBLE  # t_double
      | FLOAT   # t_float
      | BOOL    # t_bool
      | range   # t_range
      ;

const_init  : CONST type ID EQ expr SEMICOLON # const_init_expr
            | CONST type ID SEMICOLON         # const_init_type
            ;

var_init  : ID COLON range SEMICOLON            # var_init_range
          | ID COLON type INIT expr SEMICOLON   # var_init_expr
          | ID COLON type SEMICOLON             # var_init_type
          ;

global_var : GLOBAL var_init ;


label : LBRA (ID)? RBRA ;

ordering  : LT  # lt
          | LE  # le
          | EQ  # eq
          | GE  # ge
          | GT  # gt
          | NE  # ne
          ;

guard : TRUE                # guard_true
      | FALSE               # guard_false
      | expr ordering expr  # guard_constraint
      | NOT guard           # guard_neg
      | guard AND guard     # guard_and
      | guard OR guard      # guard_or
      | LPAR guard RPAR     # guard_par
      ;

var_update : LPAR ID PRIME EQ expr RPAR ;
state_update : var_update (AND var_update)*   ;
state_update_distribution : state_update                                              # state_update_single
                          | distribution+=expr COLON state_update (PLUS expr COLON state_update)*   # state_update_distr
                          ;

guarded_command : label guard TO state_update_distribution SEMICOLON ;

module : MODULE ID var_init* guarded_command+ ENDMODULE ;

preamble : (const_init | global_var)* ;
init  : INIT TRUE ENDINIT ;
file : model_type preamble module init? EOF ;
