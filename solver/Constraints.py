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

    @classmethod
    def makeConstraint(cls, f, x_names, x_list):
        """
        Looks for new variables to be added to the variable lists.
        f: is a particular equality constraint between two datum objects. It
        includes data about which objects are being constrained and which
        parameters of their placements are being set equal.
        x_names: is a list of the current variables already accounted. Note
        that variables need to be unique so this list is needed in order to
        avoid repeated variables in the lists
        x_list: a list of the values of all the variables. The values are
        either a real value or None. This method modifies x_list in place
        (values of the variables are put on x_list in their corresponding
        place)
        returns: an Equality object created with data from f
        """
        x1_name = f.Obj1Name
        x2_name = f.Obj2Name
        x1_val = None
        x2_val = None
        x1_index = x_names.index(x1_name)
        x2_index = x_names.index(x2_name)

        if f.Placement == "Placement":
            if f.Component == "x":
                x1_val = App.ActiveDocument.getObject(f.Object_1) \
                            .Placement.Rotation.toEuler()[2]
                x2_val = App.ActiveDocument.getObject(f.Object_2) \
                            .Placement.Rotation.toEuler()[2]
            elif f.Component == "y":
                x1_val = App.ActiveDocument.getObject(f.Object_1) \
                            .Placement.Rotation.toEuler()[1]
                x2_val = App.ActiveDocument.getObject(f.Object_2) \
                            .Placement.Rotation.toEuler()[1]
            elif f.Component == "z":
                x1_val = App.ActiveDocument.getObject(f.Object_1) \
                            .Placement.Rotation.toEuler()[0]
                x2_val = App.ActiveDocument.getObject(f.Object_2) \
                            .Placement.Rotation.toEuler()[0]
        elif f.Placement == "Base":
            x1_val = getattr(App.ActiveDocument.getObject(f.Object_1)
                                .Placement.Base, f.Component)
            x2_val = getattr(App.ActiveDocument.getObject(f.Object_2)
                                .Placement.Base, f.Component)

        # Modify x_list in place
        if x_list[x1_index] is None:
            x_list[x1_index] = x1_val
        if x_list[x2_index] is None:
            x_list[x2_index] = x2_val

        # Now we create the constraint object
        constraint = cls(x1_index, x2_index)
        return constraint


class Fix:
    """ A variable is fixed to a value """
    def __init__(self, a, c):
        # a is the postion of variable to fix
        # c is the value we want for the variable
        self.a = a
        self.c = c

    def eval(self, x):
        return x[self.a] - self.c
