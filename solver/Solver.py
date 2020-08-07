import functools
from scipy.optimize import minimize
import numpy as np
from .HyperDual import HyperDual
from .Constraints import Equality

class Solver:
    def __init__(self, x=None, f=None):
        self.x = x          # List  of variables to be solved (hyper duals)
        self.f = f          # List of constraint objects
        self.val = None

    def eval(self, x):
        """ Evaluate the sum of squares used by the minimize function"""
        for i in range(x.shape[0]):
            self.x[i].real = x[i]

        total = HyperDual(0, 0, 0)
        for i in range(len(self.f)):
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
        #if initial_x:
        #    self.x = convert_to_hp(initial_x)

        #if constraints:
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


import FreeCAD as App

def get_lists():
    # Assuming that constraints are only between exactly two objects
    f_list = []
    x_list = []
    x_names = []
    # First we try to find the unique variables 
    for f in App.ActiveDocument.Constraints.Group:
        x_names.append(f.Object_1)
        x_names.append(f.Object_2)
 
    print(x_names)
    unique_variables = set(x_names)
    print(unique_variables)
    x_names = []

    i = 0
    n = len(unique_variables)
    initial_grad = np.zeros(n)
    initial_hess = np.zeros((n,n))
    for f in App.ActiveDocument.Constraints.Group:
        if f.Type == "Equality_Constraint":
            x1_real = None
            x2_real = None
            # Rotations are a little bit more complicated than placements
            if "Rotation" in f.Object_1:
                if "x" in f.Object_1.split(".")[3]:
                    x1_real = App.ActiveDocument.getObject(f.Object_1.split(".")[0]).Placement.Rotation.toEuler()[2]
                    x2_real = App.ActiveDocument.getObject(f.Object_2.split(".")[0]).Placement.Rotation.toEuler()[2]
                elif "y" in f.Object_1.split(".")[3]:
                    x1_real = App.ActiveDocument.getObject(f.Object_1.split(".")[0]).Placement.Rotation.toEuler()[1]
                    x2_real = App.ActiveDocument.getObject(f.Object_2.split(".")[0]).Placement.Rotation.toEuler()[1]
                elif "z" in f.Object_1.split(".")[3]:
                    x1_real = App.ActiveDocument.getObject(f.Object_1.split(".")[0]).Placement.Rotation.toEuler()[0]
                    x2_real = App.ActiveDocument.getObject(f.Object_2.split(".")[0]).Placement.Rotation.toEuler()[0]
            else:
                x1_real = rgetattr(App.ActiveDocument, f.Object_1)
                x2_real = rgetattr(App.ActiveDocument, f.Object_2)
            x1_grad = np.zeros_like(initial_grad)
            x2_grad = np.zeros_like(initial_grad)

            # Check if variables are already in the list (we don't want to put
            # the same variable twice)
            if f.Object_1 in x_names and not f.Object_2 in x_names:
                # since x1 is already in the list, we skip it
                x1_index = x_names.index(f.Object_1)
                x2_grad[i] = 1.
                constraint = Equality(x1_index, i)
                x2 = HyperDual(x2_real, x2_grad, initial_hess)
                f_list.append(constraint)
                x_list.append(x2)
                x_names.append(f.Object_2)
                i += 1  # We only added one new variable
            elif f.Object_2 in x_names and not f.Object_1 in x_names:
                # since x2 is already in the list, we skip it
                x2_index = x_names.index(f.Object_2)
                x1_grad[i] = 1.
                constraint = Equality(i, x2_index)
                x1 = HyperDual(x1_real, x1_grad, initial_hess)
                f_list.append(constraint)
                x_list.append(x1)
                x_names.append(f.Object_1)
                i += 1  # Only one new variable
            elif f.Object_1 in x_names and f.Object_2 in x_names:
                # Both x1 and x2 are in the list, we just get their indeces
                x1_index = x_names.index(f.Object_1)
                x2_index = x_names.index(f.Object_2)
                constraint = Equality(x1_index, x2_index)
                f_list.append(constraint)
                # No new variables to append 
            else:
                # neither x1 nor x2 are in the list
                x1_grad[i] = 1.
                x2_grad[i+1] = 1.
                constraint = Equality(i, i+1)
                x1 = HyperDual(x1_real, x1_grad, initial_hess)
                x2 = HyperDual(x2_real, x2_grad, initial_hess)
                f_list.append(constraint)
                x_list.append(x1)
                x_list.append(x2)
                x_names.append(f.Object_1)
                x_names.append(f.Object_2)
                i += 2  # we added two new variables

#            x1 = HyperDual(x1_real, x1_grad, initial_hess)
#            x2 = HyperDual(x2_real, x2_grad, initial_hess)
#            f_list.append(constraint)
#            x_list.append(x1)
#            x_list.append(x2)
#            x_names.append(f.Object_1)
#            x_names.append(f.Object_2)
    return f_list, x_list, x_names

def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split("."))
