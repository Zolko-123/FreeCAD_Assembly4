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
        constraints = []
        for compPair in f.Components:
            x1Name = compPair[0]
            x2Name = compPair[1]
            x1Val = None
            x2Val = None
            x1Index = x_names.index(x1Name)
            x2Index = x_names.index(x2Name)
            component = x1Name.split(".")[2]
            placement = x1Name.split(".")[1]

            if placement == "Rotation":
                if component == "x":
                    x1Val = App.ActiveDocument.getObject(f.Object_1) \
                                .Placement.Rotation.toEuler()[2]
                    x2Val = App.ActiveDocument.getObject(f.Object_2) \
                               .Placement.Rotation.toEuler()[2]
                elif component == "y":
                    x1Val = App.ActiveDocument.getObject(f.Object_1) \
                               .Placement.Rotation.toEuler()[1]
                    x2Val = App.ActiveDocument.getObject(f.Object_2) \
                               .Placement.Rotation.toEuler()[1]
                elif component == "z":
                    x1Val = App.ActiveDocument.getObject(f.Object_1) \
                               .Placement.Rotation.toEuler()[0]
                    x2Val = App.ActiveDocument.getObject(f.Object_2) \
                               .Placement.Rotation.toEuler()[0]
            elif placement == "Base":
                x1Val = getattr(App.ActiveDocument.getObject(f.Object_1)
                                   .Placement.Base, component)
                x2Val = getattr(App.ActiveDocument.getObject(f.Object_2)
                                   .Placement.Base, component)

            # Modify x_list in place
            if x_list[x1Index] is None:
                x_list[x1Index] = x1Val
            if x_list[x2Index] is None:
                x_list[x2Index] = x2Val

            # Now we create the constraint object
            constraints.append(cls(x1Index, x2Index))
        return constraints

    @staticmethod
    def getVariables(f, xNames):
        """ Adds unique variables names to the x names list for the solver
        """
        for comp in f.Components:
            if comp[0] not in xNames:
                xNames.append(comp[0])
            if comp[1] not in xNames:
                xNames.append(comp[1])


class Fix:
    """ A variable is fixed to a value """
    def __init__(self, a, c):
        # a is the postion of variable to fix
        # c is the value we want for the variable
        self.a = a
        self.c = c

    def eval(self, x):
        return x[self.a] - self.c

    @classmethod
    def makeConstraint(cls, f, xNames, xList):
        """
        Looks for new vairaibles to be added to the variable list.
        f: a particular fix constraint containing information about the
        object to be fixed.
        xList: list containing the values of all the variables.
        returns: a list of  Fix objects created with data from f.
        """
        # Note that there is only one variable being fixed
        constraints = []
        for component in f.Components:
            if not f.Components[component]["enable"]:
                continue
            xName = f.Components[component]["objName"]
            xVal = None
            xIndex = xNames.index(xName)
            placement = xName.split(".")[1]
            placementComp = xName.split(".")[2]
            c = f.Components[component]["value"]
            if placement == "Rotation":
                if placementComp == "x":
                    xVal = App.ActiveDocument.getObject(f.Object) \
                              .Placement.Rotation.toEuler()[2]
                elif placementComp == "y":
                    xVal = App.ActiveDocument.getObject(f.Object) \
                              .Placement.Rotation.toEuler()[1]
                elif placementComp == "z":
                    xVal = App.ActiveDocument.getObject(f.Object) \
                              .Placement.Rotation.toEuler()[0]
            elif placement == "Base":
                xVal = getattr(App.ActiveDocument.getObject(f.Object)
                                  .Placement.Base, placementComp)
            if xList[xIndex] is None:
                xList[xIndex] = xVal

            constraint = cls(xIndex, c)
            constraints.append(constraint)
        return constraints

    @staticmethod
    def getVariables(f, xNames):
        """ Adds unique variables names to the x names list for the solver
        """
        for component in f.Components:
            if not f.Components[component]["enable"]:
                continue
            objName = f.Components[component]["objName"]
            if objName not in xNames:
                xNames.append(objName)
