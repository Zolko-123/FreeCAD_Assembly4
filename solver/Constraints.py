import FreeCAD as App
from .HyperDual import HyperDualQuaternion, hdsin, hdcos
from math import pi


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
    def __init__(self, indexList, fixType):
        # indexList contains the indeces of the variables needed to
        # create the placements of the object and the reference
        # fixType is the type of fix (Rotation or Base)
        self.xPlacement = App.Placement
        self.rPlacement = App.Placement
        self.indexList = indexList
        self.fixType = fixType

    def eval(self, x):
        # quaternion representing the reference rotation
        rqrotxIndex = None
        rqrotyIndex = None
        rqrotzIndex = None
        # quaternion representing the object rotation
        oqrotxIndex = None
        oqrotyIndex = None
        oqrotzIndex = None
        # quaternion representing the position of the object
        pxIndex = None
        pyIndex = None
        pzIndex = None
        # quaternion representing the fix rotation
        fqrotxIndex = None
        fqrotyIndex = None
        fqrotzIndex = None
        fqrotx = None
        fqroty = None
        fqrotz = None
        # quaternion representing the fix base
        fqbasexIndex = None
        fqbaseyIndex = None
        fqbasezIndex = None
        fqbasex = None
        fqbasey = None
        fqbasez = None

        rqrotxIndex = self.indexList["Rotation_x"]["Reference"]
        oqrotxIndex = self.indexList["Rotation_x"]["Object"]
        rqrotyIndex = self.indexList["Rotation_y"]["Reference"]
        oqrotyIndex = self.indexList["Rotation_y"]["Object"]
        rqrotzIndex = self.indexList["Rotation_z"]["Reference"]
        oqrotzIndex = self.indexList["Rotation_z"]["Object"]
        pxIndex = self.indexList["Base_x"]["Object"]
        pyIndex = self.indexList["Base_y"]["Object"]
        pzIndex = self.indexList["Base_z"]["Object"]
        if self.indexList["Rotation_x"]["Enable"]:
            val = self.indexList["Rotation_x"]["FixVal"]
            fqrotx = HyperDualQuaternion(hdsin(val/2),
                                         0,
                                         0,
                                         hdcos(val/2))
        else:
            fqrotxIndex = self.indexList["Rotation_x"]["Object"]
            fqrotx = HyperDualQuaternion(hdsin(x[fqrotxIndex]/2),
                                         0,
                                         0,
                                         hdcos(x[fqrotxIndex]/2))
        if self.indexList["Rotation_y"]["Enable"]:
            val = self.indexList["Rotation_y"]["FixVal"]
            fqroty = HyperDualQuaternion(0,
                                         hdsin(val/2),
                                         0,
                                         hdcos(val/2))
        else:
            fqrotyIndex = self.indexList["Rotation_y"]["Object"]
            fqroty = HyperDualQuaternion(0,
                                         hdsin(x[fqrotyIndex]/2),
                                         0,
                                         hdcos(x[fqrotyIndex]/2))
        if self.indexList["Rotation_z"]["Enable"]:
            val = self.indexList["Rotation_z"]["FixVal"]
            fqrotz = HyperDualQuaternion(0,
                                         0,
                                         hdsin(val/2),
                                         hdcos(val/2))
        else:
            fqrotzIndex = self.indexList["Rotation_z"]["Object"]
            fqrotz = HyperDualQuaternion(0,
                                         0,
                                         hdsin(x[fqrotzIndex]/2),
                                         hdcos(x[fqrotzIndex]/2))

        if self.indexList["Base_x"]["Enable"]:
            fqbasex = self.indexList["Base_x"]["FixVal"]
        else:
            fqbasexIndex = self.indexList["Base_x"]["Object"]
            fqbasex = x[fqbasexIndex]
        if self.indexList["Base_y"]["Enable"]:
            fqbasey = self.indexList["Base_y"]["FixVal"]
        else:
            fqbaseyIndex = self.indexList["Base_y"]["Object"]
            fqbasey = x[fqbaseyIndex]
        if self.indexList["Base_z"]["Enable"]:
            fqbasez = self.indexList["Base_z"]["FixVal"]
        else:
            fqbasezIndex = self.indexList["Base_z"]["Object"]
            fqbasez = x[fqbasezIndex]

        rqx = HyperDualQuaternion(hdsin((x[rqrotxIndex]).real/2),
                                  0,
                                  0,
                                  hdcos((x[rqrotxIndex]).real/2))
        rqy = HyperDualQuaternion(0,
                                  hdsin((x[rqrotyIndex]).real/2),
                                  0,
                                  hdcos((x[rqrotyIndex]).real/2))
        rqz = HyperDualQuaternion(0,
                                  0,
                                  hdsin((x[rqrotzIndex]).real/2),
                                  hdcos((x[rqrotzIndex]).real/2))
        oqx = HyperDualQuaternion(hdsin(x[oqrotxIndex]/2),
                                  0,
                                  0,
                                  hdcos(x[oqrotxIndex]/2))
        oqy = HyperDualQuaternion(0,
                                  hdsin(x[oqrotyIndex]/2),
                                  0,
                                  hdcos(x[oqrotyIndex]/2))
        oqz = HyperDualQuaternion(0,
                                  0,
                                  hdsin(x[oqrotzIndex]/2),
                                  hdcos(x[oqrotzIndex]/2))
        rq = rqz@rqy@rqx
        oq = oqz@oqy@oqx
        fqrot = fqrotz@fqroty@fqrotx
        p = HyperDualQuaternion(x[pxIndex], x[pyIndex], x[pzIndex], 0)
        fqbase = HyperDualQuaternion(fqbasex, fqbasey, fqbasez, 0)
        if self.fixType == "Base":
            result = rq**-1@p@rq - fqbase
            print(fqbase)
            print(result)
            print(rq)
            print(p)
            return result.q0**2 + result.q1**2 + result.q2**2
        # First, fill up the rotation objects
        elif self.fixType == "Rotation":
            result = fqrot**-1@rq**-1@oq
            return result.q0**2 + result.q1**2 + result.q2**2

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
        # Stores the indices of the variables used to construct the
        # placements of the object and the reference
        indexList = {
                "Base_x": {
                    "Object": None,
                    "Reference": None,
                    "Enable": False,
                    "FixVal": None,
                },
                "Base_y": {
                    "Object": None,
                    "Reference": None,
                    "Enable": False,
                    "FixVal": None,
                },
                "Base_z": {
                    "Object": None,
                    "Reference": None,
                    "Enable": False,
                    "FixVal": None,
                },
                "Rotation_x": {
                    "Object": None,
                    "Reference": None,
                    "Enable": False,
                    "FixVal": None,
                },
                "Rotation_y": {
                    "Object": None,
                    "Reference": None,
                    "Enable": False,
                    "FixVal": None,
                },
                "Rotation_z": {
                    "Object": None,
                    "Reference": None,
                    "Enable": False,
                    "FixVal": None,
                },
        }

        for component in f.Components:
            xName = f.Components[component]["objName"]
            rName = f.Components[component]["refName"]
            xVal = None
            rVal = None
            xIndex = xNames.index(xName)
            rIndex = xNames.index(rName)
            xplacement = xName.split(".")[1]
            xplacementComp = xName.split(".")[2]
            if xplacement == "Rotation":
                if xplacementComp == "x":
                    xVal = App.ActiveDocument.getObject(f.Object) \
                              .Placement.Rotation.toEuler()[2] * pi/180
                    rVal = App.ActiveDocument.getObject(f.Reference) \
                              .Placement.Rotation.toEuler()[2] * pi/180
                    indexList["Rotation_x"]["Object"] = xIndex
                    indexList["Rotation_x"]["Reference"] = rIndex
                    indexList["Rotation_x"]["Enable"] = f.Components[component]["enable"]
                    indexList["Rotation_x"]["FixVal"] = f.Components[component]["value"] * pi/180
                elif xplacementComp == "y":
                    xVal = App.ActiveDocument.getObject(f.Object) \
                              .Placement.Rotation.toEuler()[1] * pi/180
                    rVal = App.ActiveDocument.getObject(f.Reference) \
                              .Placement.Rotation.toEuler()[1] * pi/180
                    indexList["Rotation_y"]["Object"] = xIndex
                    indexList["Rotation_y"]["Reference"] = rIndex
                    indexList["Rotation_y"]["Enable"] = f.Components[component]["enable"]
                    indexList["Rotation_y"]["FixVal"] = f.Components[component]["value"] * pi/180
                elif xplacementComp == "z":
                    xVal = App.ActiveDocument.getObject(f.Object) \
                              .Placement.Rotation.toEuler()[0] * pi/180
                    rVal = App.ActiveDocument.getObject(f.Reference) \
                              .Placement.Rotation.toEuler()[0] * pi/180
                    indexList["Rotation_z"]["Object"] = xIndex
                    indexList["Rotation_z"]["Reference"] = rIndex
                    indexList["Rotation_z"]["Enable"] = f.Components[component]["enable"]
                    indexList["Rotation_z"]["FixVal"] = f.Components[component]["value"] * pi/180
            elif xplacement == "Base":
                xVal = getattr(App.ActiveDocument.getObject(f.Object)
                                  .Placement.Base, xplacementComp)
                rVal = getattr(App.ActiveDocument.getObject(f.Reference)
                                  .Placement.Base, xplacementComp)
                if xplacementComp == "x":
                    indexList["Base_x"]["Object"] = xIndex
                    indexList["Base_x"]["Reference"] = rIndex
                    indexList["Base_x"]["Enable"] = f.Components[component]["enable"]
                    indexList["Base_x"]["FixVal"] = f.Components[component]["value"]
                if xplacementComp == "y":
                    indexList["Base_y"]["Object"] = xIndex
                    indexList["Base_y"]["Reference"] = rIndex
                    indexList["Base_y"]["Enable"] = f.Components[component]["enable"]
                    indexList["Base_y"]["FixVal"] = f.Components[component]["value"]
                if xplacementComp == "z":
                    indexList["Base_z"]["Object"] = xIndex
                    indexList["Base_z"]["Reference"] = rIndex
                    indexList["Base_z"]["Enable"] = f.Components[component]["enable"]
                    indexList["Base_z"]["FixVal"] = f.Components[component]["value"]

            if xList[xIndex] is None:
                xList[xIndex] = xVal
            if xList[rIndex] is None:
                xList[rIndex] = rVal

        # Now, we make two fix constraints. One for the base and the other for
        # the rotation of the object
        BaseConstraint = cls(indexList, "Base")
        constraints.append(BaseConstraint)
        RotConstraint = cls(indexList, "Rotation")
        constraints.append(RotConstraint)

        return constraints

    @staticmethod
    def getVariables(f, xNames):
        """ Adds unique variables names to the x names list for the solver
        """
        for component in f.Components:
            # We need all the components in order to compute the inverse
            # placement of the reference object
            objName = f.Components[component]["objName"]
            refName = f.Components[component]["refName"]
            if objName not in xNames:
                xNames.append(objName)
            if refName not in xNames:
                xNames.append(refName)
