

class Equality:
    """ Two variables have the same value """
    def __init__(self, a, b):
        # a and b are the positions of the variables to be set equal in the
        # variable array
        self.a = a
        self.b = b

    def eval(self, x):
        return x[self.a] - x[self.b]


