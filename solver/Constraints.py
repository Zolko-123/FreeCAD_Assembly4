import FreeCAD as App


class Equality:
    """ Two variables have the same value """
    def __init__(self, a, b):
        # a and b are the positions of the variables to be set equal in the
        # variable array
        self.a = a
        self.b = b

    def eval(self, x):
        return x[self.a] - x[self.b]

    @staticmethod
    def getLists(f, x_names):
        """
        Looks for new variables to be added to the variable lists.
        f: is a particular equality constraint between two datum objects. It
        includes data about which objects are being constrained and which
        parameters of their placements are being set equal.
        x_names: is a list of the current variables already accounted. Note
        that variables need to be unique so this list is needed in order to
        avoid repeated variables in the lists
        returns: a list of the variables being constrained and their respective
        names
        """
        x_new_vals = []     # Values of variables being constrained
        x_new_id = [
            f.Obj1Name,
            f.Obj2Name,
        ]                   # Names of variables being constrained

        if f.Placement == "Placement":
            if f.Component == "x":
                x_new_vals[0] = App.ActiveDocument.getObject(f.Object_1) \
                                    .Placement.Rotation.toEuler()[2]
                x_new_vals[1] = App.ActiveDocument.getObject(f.Object_2) \
                                   .Placement.Rotation.toEuler()[2]
            elif f.Component == "y":
                x_new_vals[0] = App.ActiveDocument.getObject(f.Object_1) \
                                   .Placement.Rotation.toEuler()[1]
                x_new_vals[1] = App.ActiveDocument.getObject(f.Object_2) \
                                   .Placement.Rotation.toEuler()[1]
            elif f.Component == "z":
                x_new_vals[0] = App.ActiveDocument.getObject(f.Object_1) \
                                   .Placement.Rotation.toEuler()[0]
                x_new_vals[1] = App.ActiveDocument.getObject(f.Object_2) \
                                   .Placement.Rotation.toEuler()[0]
        elif f.Placement == "Base":
            x_new_vals[0] = getattr(App.ActiveDocument.getObject(f.Object_1)
                                       .Placement.Base, f.Component)
            x_new_vals[1] = getattr(App.ActiveDocument.getObject(f.Object_2)
                                       .Placement.Base, f.Component)

        return x_new_vals, x_new_id


class Fix:
    """ A variable is fixed to a value """
    def __init__(self, a, c):
        # a is the postion of variable to fix
        # c is the value we want for the variable
        self.a = a
        self.c = c

    def eval(self, x):
        return x[self.a] - self.c
