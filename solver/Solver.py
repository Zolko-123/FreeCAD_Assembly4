from scipy.optimize import minimize
import numpy as np
import FreeCAD as App
from .HyperDual import HyperDual
from .Constraints import Equality, Fix


class Solver:
    def __init__(self, x=None, f=None):
        self.x = x              # List  of variables to be solved (hyper duals)
        self.f = f              # List of constraint objects
        self.val = None         # Value of function at current point
        self.current_x = None   # Current point

    def eval(self, x):
        """ Evaluate the sum of squares used by the minimize function"""
        for i in range(x.shape[0]):
            self.x[i].real = x[i]

        total = HyperDual(0, 0, 0)
        for i in range(len(self.f)):
            total += self.f[i].eval(self.x)**2

        self.val = total
        self.current_x = x
        return self.val.real

    def grad(self, x):
        """ Returns teh gradient of evaluated sum of squares """
        # Checks that we have evaluated the fuction at point x
        if not np.array_equal(self.current_x, x):
            self.eval(x)
        return self.val.grad

    def hess(self, x):
        """ Returns the hessian of evaluated sum of squares """
        # Checks that we have evaluated the function at point x
        if not np.array_equal(self.current_x, x):
            self.eval(x)
        return self.val.hess

    def solve(self, initial_x=None, constraints=None):
        """ Tries to solve the sum of squares problem.
            initial_x: list of initial values for the solver (list of reals)
            constraints: list of constraint objects """
        # if initial_x:
        #    self.x = convert_to_hp(initial_x)

        # if constraints:
        #    self.f = constraints

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


def get_lists():
    """
    Gets 3 lists. A list containing the constraint functions. A list
    containing the independent variables. And a list containing the
    ids of the independent variables.
    """
    f_list = []
    x_list = []
    x_names = []
    x_hd = []   # List of hyper duals
    # First we try to find the unique variables 
    for f in App.ActiveDocument.Constraints.Group:
        if f.Type == "Equality_Constraint":
            if f.Obj1Name not in x_names:
                x_names.append(f.Obj1Name)
            if f.Obj2Name not in x_names:
                x_names.append(f.Obj2Name)
        elif f.Type == "Fix_Constraint":
            if f.ObjName not in x_names:
                x_names.append(f.ObjName)

    n = len(x_names)
    x_list = [None]*n
    initial_hess = np.zeros((n, n))
    for f in App.ActiveDocument.Constraints.Group:
        if f.Type == "Equality_Constraint":
            f_list.append(Equality.makeConstraint(f, x_names, x_list))
        if f.Type == "Fix_Constraint":
            f_list.append(Fix.makeConstraint(f, x_names, x_list))
    i = 0
    for x in x_list:
        new_grad = np.zeros(n)
        new_grad[i] = 1
        new_hd = HyperDual(x, new_grad, initial_hess)
        x_hd.append(new_hd)
        i += 1
    return f_list, x_hd, x_names
