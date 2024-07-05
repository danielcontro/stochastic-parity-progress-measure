from sympy import And, Or, Eq, Add, Symbol, Matrix, zeros

from reactive_module import ReactiveModule

coin = Symbol("coin")
c = Symbol("c")
x = Symbol("x")

vars = (coin, c, x)

init = (0.0, 0.0)

guards = [
    Eq(Add(c, -1), 0),
    Eq(Add(coin, -1), 0),
    Eq(c, 0),
]

coin_1 = Matrix([[1], [0], [0]])
coin_0 = zeros(3, 1)

double_x_0 = Matrix([[0, 0, 0], [0, 1, 0], [0, 0, 2]]), coin_0
double_x_1 = Matrix([[0, 0, 0], [0, 1, 0], [0, 0, 2]]), coin_1
c_1_coin_0_1 = Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 1]]), Matrix([[0], [0], [0]])
c_0_1 = Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 1]]), Matrix([[0], [0], [-1]])
c_0_2 = Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 1]]), Matrix([[1], [0], [-1]])

body = [(Eq(Add(c, -1), 0), [[(0.5,), (0.5,)]])]
