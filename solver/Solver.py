from scipy.optimize import minimize
import numpy as np
from HyperDual import HyperDual


class Solver:
    def __init__(self):
        self.x = None     # List  of variables to be solved (hyper duals)
        self.f = None     # List of constraint objects
        self.val = None

    def eval(self, x):
        """ Evaluate the sum of squares used by the minimize function"""
        for i in range(x.shape[0]):
            self.x[i].real = x[i]

        total = HyperDual(0, 0, 0)
        for i in range(self.f.shape[0]):
            total += self.f[i].eval(self.x)**2

        self.val = total
        return self.val.real

    def grad(self, x):
        """ Returns teh gradient of evaluated sum of squares """
        return self.val.grad

    def hess(self, x):
        """ Returns the hessian of evaluated sum of squares """
        return self.val.hess

    def solve(self, initial_x=None, constraints=None):
        """ Tries to solve the sum of squares problem.
            initial_x: list of initial values for the solver (list of reals)
            constraints: list of constraint objects """
        if initial_x:
            self.x = convert_to_hp(initial_x)

        if constraints:
            self.f = constraints

        x0 = np.array(initial_x)
        solution = minimize(self.eval, x0,  method="trust-ncg",
                            jac=self.grad, hess=self.hess,
                            options={"gtol": 1e-8, "disp": True})
        return solution

    def convert_to_hp(self, real_list):
        """ Convert numbers in real list to a list of hyperduals """
        n = len(real_list)
        hd_list = []

        for i in range(len(real_list)):
            hd_list.append()
