import numpy as np

class HyperDual:
    def __init__(self, real, grad, hess):
        self.real = real
        if isinstance(grad, np.ndarray):
            self.grad = grad
        else:
            self.grad = np.atleast_1d(grad)
        if isinstance(hess, np.ndarray):
            self.hess = hess
        else:
            self.hess = np.atleast_1d(hess)

    def __add__(self, other):
        if isinstance(other, HyperDual):
            return HyperDual(self.real + other.real,
                             self.grad + other.grad,
                             self.hess + other.hess)
        else:
            return HyperDual(self.real + other,
                             self.grad,
                             self.hess
                             )

    def __radd__(self, other):
        return HyperDual(self.real + other,
                         self.grad,
                         self.hess
                         )

    def __sub__(self, other):
        if isinstance(other, HyperDual):
            return HyperDual(self.real - other.real,
                             self.grad - other.grad,
                             self.hess - other.hess
                             )
        else:
            return HyperDual(self.real - other,
                             self.grad,
                             self.hess
                             )

    def __rsub__(self, other):
        return HyperDual(other - self.real,
                         -self.grad,
                         -self.hess
                         )

    def __mul__(self, other):
        if isinstance(other, HyperDual):
            return HyperDual(self.real * other.real,
                             self.real * other.grad + other.real * self.grad,
                             self.real * other.hess
                             + self.grad * other.grad[:, None]
                             + self.grad[:, None] * other.grad
                             + self.hess * other.real
                             )
        else:
            return HyperDual(self.real * other,
                             self.grad * other,
                             self.hess * other
                             )

    def __rmul__(self, other):
        return HyperDual(self.real * other,
                         self.grad * other,
                         self.hess * other
                         )

    def __truediv__(self, other):
        if isinstance(other, HyperDual):
            # TODO: implement multiplicative inverse as shown on the paper
            # this is just a lazy way of doing division
            return self * other**-1
        else:
            # TODO: another lazy implementation?
            grad = np.zeros_like(self.grad)
            hess = np.zeros_like(self.hess)
            return self * HyperDual(other, grad, hess)**-1

    def __rtruediv__(self, other):
        # TODO: implement multiplicative inverse
        grad = np.zeros_like(self.grad)
        hess = np.zeros_like(self.hess)
        return HyperDual(other, grad, hess) * self**-1

    def __pow__(self, power):
        real = self.real ** power
        grad = self.grad * power * self.real ** (power - 1)
        hess = (power * (power - 1) * self.real ** (power - 2)
                * (self.real * self.hess + self.grad * self.grad[:, None]))
        return HyperDual(real, grad, hess)

    def __repr__(self):
        return repr(self.real) + " + " + repr(self.grad) + " + \n" + repr(self.hess) + "\n"

