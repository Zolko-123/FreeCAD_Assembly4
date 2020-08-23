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

#    unique_variables = set(x_names)
#    x_names = []
#    i = 0
    n = len(x_names)
    x_list = [None]*n
    #initial_grad = np.zeros(n)
    initial_hess = np.zeros((n, n))
    for f in App.ActiveDocument.Constraints.Group:
        if f.Type == "Equality_Constraint":
            f_list.append(Equality.makeConstraint(f, x_names, x_list))
        if f.Type == "Fix_Constraint":
            f_list.append(Fix.makeConstraint(f, x_names, x_list))
#            i += len(x_new)
#        if f.Type == "Fix_Constraint":
#            f_new, x_new, x_names_new = get_fix_lists(f, x_names, n, i)
#            if f_new:
#                f_list.extend(f_new)
#            if x_new:
#                x_list.extend(x_new)
#            if x_names_new:
#                x_names.extend(x_names_new)
#            i += len(x_new
    i = 0
    for x in x_list:
        new_grad = np.zeros(n)
        new_grad[i] = 1
        new_hd = HyperDual(x, new_grad, initial_hess)
        x_hd.append(new_hd)
        i += 1
    return f_list, x_hd, x_names


def get_equality_lists(f, x_names, n, i):
    """
    Gets lists for Equality Constraints
    """
    f_new = []
    x_new = []
    x_names_new = []
    x1_real = None
    x2_real = None
    x1_name = f.Obj1Name
    x2_name = f.Obj2Name
    x1_index = None
    x2_index = None
    x1_grad = np.zeros(n)
    x2_grad = np.zeros(n)
    initial_hess = np.zeros((n,n))

    # Rotations are a little bit more complicated than placements
    if "Rotation" == f.Placement:
        if f.Component == "x":
            x1_real = App.ActiveDocument.getObject(f.Object_1).Placement.Rotation.toEuler()[2]
            x2_real = App.ActiveDocument.getObject(f.Object_2).Placement.Rotation.toEuler()[2]
        elif f.Component == "y":
            x1_real = App.ActiveDocument.getObject(f.Object_1).Placement.Rotation.toEuler()[1]
            x2_real = App.ActiveDocument.getObject(f.Object_2).Placement.Rotation.toEuler()[1]
        elif f.Component == "z":
            x1_real = App.ActiveDocument.getObject(f.Object_1).Placement.Rotation.toEuler()[0]
            x2_real = App.ActiveDocument.getObject(f.Object_2).Placement.Rotation.toEuler()[0]
    elif f.Placement == "Base":
        x1_real = getattr(App.ActiveDocument.getObject(f.Object_1).Placement.Base, f.Component)
        x2_real = getattr(App.ActiveDocument.getObject(f.Object_2).Placement.Base, f.Component)

    # Check if variables are already in the list (we don't want to put
    # the same variable twice)
    if x1_name in x_names:
        # skip x1 since it already is in the list 
        # we only need its index in the list
        x1_index = x_names.index(x1_name)
    else:
        # x1 not in the list, therefore we add it
        x1_grad[i] = 1.
        x1 = HyperDual(x1_real, x1_grad, initial_hess)
        x1_index = i
        x_new.append(x1)
        x_names_new.append(x1_name)
        i += 1

    if x2_name in x_names:
        # Now do the same we did for x1 to x2
        x2_index = x_names.index(x2_name)
    else:
        x2_grad[i] = 1.
        x2 = HyperDual(x2_real, x2_grad, initial_hess)
        x2_index = i
        x_new.append(x2)
        x_names_new.append(x2_name)
        i += 1

    constraint = Equality(x1_index, x2_index)
    f_new.append(constraint)
    return f_new, x_new, x_names_new

def get_fix_lists(f, x_names, n, i):
    """
    Gets lists for Fix Constraints
    """
    f_new = []
    x_new = []
    x_names_new = []
    x1_real = None
    x1_name = f.ObjName
    x1_index = None
    x1_grad = np.zeros(n)
    initial_hess = np.zeros((n, n))
    c = f.Value

    if f.Placement == "Rotation":
        if f.Component == "x":
            x1_real = App.ActiveDocument.getObject(f.Object).Placement.Rotation.toEuler()[2]
        elif f.Component == "y":
            x1_real = App.ActiveDocument.getObject(f.Object).Placement.Rotation.toEuler()[1]
        elif f.Component == "z":
            x1_real = App.ActiveDocument.getObject(f.Object).Placement.Rotation.toEuler()[0]
    elif f.Placement == "Base":
        x1_real = getattr(App.ActiveDocument.getObject(f.Object).Placement.Base, f.Component)

    # We don't want to put the same variable twice
    if x1_name in x_names:
        x1_index = x_names.index(x1_name)
    else:
        # x1 not in the list, so we add it
        x1_grad[i] = 1.
        x1 = HyperDual(x1_real, x1_grad, initial_hess)
        x1_index = i
        x_new.append(x1)
        x_names_new.append(x1_name)
        i += 1
    constraint = Fix(x1_index, c)
    f_new.append(constraint)
    return f_new, x_new, x_names_new
