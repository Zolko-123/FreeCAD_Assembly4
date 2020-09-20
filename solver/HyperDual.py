import numpy as np
from math import sin, cos

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


class HyperDualQuaternion:
    def __init__(self, q0, q1, q2, q3):
        """ Quaternion in which each component is a hyper dual number.
        q0 = x, q1 = y, q2 = z, q3 = w,
        where the quaternion is q = w + xi + yj +zk
        """

        self.q0 = q0
        self.q1 = q1
        self.q2 = q2
        self.q3 = q3
        return
        if isinstance(q0, HyperDual):
            self.q0 = q0
        else:
            raise TypeError("q0 has to be HyperDual")
        if isinstance(q1, HyperDual):
            self.q1 = q1
        else:
            raise TypeError("q1 has to be HyperDual")
        if isinstance(q2, HyperDual):
            self.q2 = q2
        else:
            raise TypeError("q2 has to be HyperDual")
        if isinstance(q3, HyperDual):
            self.q3 = q3
        else:
            raise TypeError("q3 has to be HyperDual")

    def __add__(self, other):
        """ Quaternion addition. Assuming only quaternions are used,
        no quaternions and floats.
        """
        q0 = self.q0 + other.q0
        q1 = self.q1 + other.q1
        q2 = self.q2 + other.q2
        q3 = self.q3 + other.q3
        return HyperDualQuaternion(q0, q1, q2, q3)

    def __sub__(self, other):
        """ Quaternion substraction. Assuming only quternions are used.
        """
        q0 = self.q0 - other.q0
        q1 = self.q1 - other.q1
        q2 = self.q2 - other.q2
        q3 = self.q3 - other.q3
        return HyperDualQuaternion(q0, q1, q2, q3)

    def __matmul__(self, other):
        q0 = self.q3*other.q0 + self.q0*other.q3 + self.q1*other.q2 - self.q2*other.q1
        q1 = self.q3*other.q1 - self.q0*other.q2 + self.q1*other.q3 + self.q2*other.q0
        q2 = self.q3*other.q2 + self.q0*other.q1 - self.q1*other.q0 + self.q2*other.q3
        q3 = self.q3*other.q3 - self.q0*other.q0 - self.q1*other.q1 - self.q2*other.q2
        return HyperDualQuaternion(q0, q1, q2, q3)

    def __pow__(self, other):
        if other == -1:
            # Note that we are assuming unit quaternion here
            q0 = -1*self.q0
            q1 = -1*self.q1
            q2 = -1*self.q2
            q3 = self.q3
            return HyperDualQuaternion(q0, q1, q2, q3)
        else:
            raise NotImplementedError

    def __repr__(self):
        try:
            return repr("(" + repr(self.q0.real) + "i + "
                        + repr(self.q1.real) + "j + "
                        + repr(self.q2.real) + "k + "
                        + repr(self.q3.real) + ")")
        except AttributeError:
            return repr("(" + repr(self.q0) + "i + "
                        + repr(self.q1) + "j + "
                        + repr(self.q2) + "k + "
                        + repr(self.q3) + ")")


def hdsin(x):
    """ sin function but with hyperduals """
    if not isinstance(x, HyperDual):
        return sin(x)
    real = sin(x.real)
    grad = x.grad * cos(x.real)
    hess = x.hess * cos(x.real) - x.grad * x.grad[:, None] * sin(x.real)
    return HyperDual(real, grad, hess)


def hdcos(x):
    """ cos function but with hyperduals """
    if not isinstance(x, HyperDual):
        return cos(x)
    real = cos(x.real)
    grad = -x.grad * sin(x.real)
    hess = -x.hess * sin(x.real) - x.grad * x.grad[:, None] * cos(x.real)
    return HyperDual(real, grad, hess)
