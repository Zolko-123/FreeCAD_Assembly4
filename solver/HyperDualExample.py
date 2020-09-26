import time
import numpy as np
from scipy.optimize import minimize
from HyperDual import HyperDual
from HyperDual import hdsin
from HyperDual import hdcos


# Here are the discrete functions (from scipy optimize page)
def rosen(x):
    """The Rosenbrock function"""
    return sum(100.0*(x[1:]-x[:-1]**2.0)**2.0 + (1-x[:-1])**2.0)


def rosen_der(x):
    xm = x[1:-1]
    xm_m1 = x[:-2]
    xm_p1 = x[2:]
    der = np.zeros_like(x)
    der[1:-1] = 200*(xm-xm_m1**2) - 400*(xm_p1 - xm**2)*xm - 2*(1-xm)
    der[0] = -400*x[0]*(x[1]-x[0]**2) - 2*(1-x[0])
    der[-1] = 200*(x[-1]-x[-2]**2)
    return der


def rosen_hess(x):
    x = np.asarray(x)
    H = np.diag(-400*x[:-1],1) - np.diag(400*x[:-1],-1)
    diagonal = np.zeros_like(x)
    diagonal[0] = 1200*x[0]**2-400*x[1]+2
    diagonal[-1] = 200
    diagonal[1:-1] = 202 + 1200*x[1:-1]**2 - 400*x[2:]
    H = H + np.diag(diagonal)
    return H


class Rosen:
    def __init__(self, hyper_dual_array):
        self.hp = hyper_dual_array
        self.val = None

    def rosen(self, x):
        for i in range(x.shape[0]):
            self.hp[i].real = x[i]

        self.val = sum(100.0*(self.hp[1:]-self.hp[:-1]**2.0)**2.0 + (1-self.hp[:-1])**2.0)
        return self.val.real

    def grad(self, x):
        return self.val.grad

    def hess(self, x):
        return self.val.hess


t = time.time()
initial_hess = np.zeros((5, 5))
x01 = HyperDual(1.3, [1., 0., 0., 0., 0.], initial_hess)
x02 = HyperDual(0.7, [0., 1., 0., 0., 0.], initial_hess)
x03 = HyperDual(0.8, [0., 0., 1., 0., 0.], initial_hess)
x04 = HyperDual(1.9, [0., 0., 0., 1., 0.], initial_hess)
x05 = HyperDual(1.2, [0., 0., 0., 0., 1.], initial_hess)

print(hdcos(x01))

x0 = np.array([1.3, 0.7, 0.8, 1.9, 1.2])
x0hd = np.array([x01, x02, x03, x04, x05])
ros = Rosen(x0hd)
res = minimize(ros.rosen, x0, method="trust-ncg",
               jac=ros.grad, hess=ros.hess,
               options={"gtol": 1e-8, "disp": True})
print("Time taken while using hyper duals: {}".format(time.time() - t))
print("The resulting vector is: {}".format(res.x))


t = time.time()
x0 = np.array([1.3, 0.7, 0.8, 1.9, 1.2])
res = minimize(rosen, x0, method='trust-ncg',
               jac=rosen_der, hess=rosen_hess,
               options={'gtol': 1e-8, 'disp': True})
print("Time taken while using discrete gradent and hessian functions: {}".format(time.time() - t))
print("The resulting vector is: {}".format(res.x))

