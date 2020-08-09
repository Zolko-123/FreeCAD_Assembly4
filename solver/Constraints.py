

class Equality:
    """ Two variables have the same value """
    def __init__(self, a, b):
        # a and b are the positions of the variables to be set equal in the
        # variable array
        self.a = a
        self.b = b

    def eval(self, x):
        return x[self.a] - x[self.b]


class Fix:
    """ A variable is fixed to a value """
    def __init__(self, a, c):
        # a is the postion of variable to fix
        # c is the value we want for the variable
        self.a = a
        self.c = c

    def eval(self, x):
        return x[self.a] - self.c
