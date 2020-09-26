import os
from PySide import QtGui
import FreeCAD as App
import FreeCADGui as Gui
import libAsm4 as asm4


class EqualityConstraintCmd:
    """ Adds an equality constraint into the assembly"""

    def GetResources(self):
        return {
            "MenuText": "Add equality constraint",
            "ToolTip": "Creates new equality constraint into the assembly",
            "Pixmap": os.path.join(asm4.iconPath, "Draft_Dimension.svg")
        }

    def IsActive(self):
        if App.ActiveDocument:
            return (True)
        else:
            return (False)

    def Activated(self):
        panel = EqualityPanel()
        Gui.Control.showDialog(panel)


class EqualityPanel:
    def __init__(self):
        self.type = "Equality_Constraint"
        self.form = Gui.PySideUic.loadUi(
            os.path.join(
                asm4.wbPath,
                "Resources/ui/TaskPanel_EqualityConstraint.ui"))
        self.addObjects()

    def accept(self):
        obj1 = self.form.firstObjectList.selectedItems()[0].text()
        obj2 = self.form.secondObjectList.selectedItems()[0].text()
        components = []
        compStatus = []
        if not obj1 or not obj2:
            print("Select first and second objects")
            return
        if obj1 == obj2:
            print("Select two distinct objects")
            return
        if self.form.xCheck.isChecked():
            # We want to set the x-coordinates of both objects equal
            compStatus.append("Base_x")
        if self.form.yCheck.isChecked():
            # we want to set the y-coordinates of both objects equal
            compStatus.append("Base_y")
        if self.form.zCheck.isChecked():
            # we want to set the z-coordinates of both objects equal
            compStatus.append("Base_z")
        if self.form.xrotCheck.isChecked():
            # Set rotation about x-axis equal
            compStatus.append("Rot_x")
        if self.form.yrotCheck.isChecked():
            # set rotation about y-axis equal
            compStatus.append("Rot_y")
        if self.form.zrotCheck.isChecked():
            # Set rotation about z-axis equal
            compStatus.append("Rot_z")

        newConstraint = App.ActiveDocument.addObject("App::FeaturePython", self.type)
        EqualityConstraint(newConstraint, obj1, obj2, self.type, components, compStatus)
        Gui.Control.closeDialog()
        App.ActiveDocument.recompute()

    def addObjects(self):
        # Here we populate the list view widgets
        for obj in App.ActiveDocument.Objects:
            if obj.TypeId not in asm4.datumTypes:
                continue
            newItem = QtGui.QListWidgetItem()
            newItem.setText(obj.Name)
            newItem.setIcon(obj.ViewObject.Icon)
            self.form.firstObjectList.addItem(newItem)
        for obj in App.ActiveDocument.Objects:
            if obj.TypeId not in asm4.datumTypes:
                continue
            newItem = QtGui.QListWidgetItem()
            newItem.setText(asm4.nameLabel(obj))
            newItem.setIcon(obj.ViewObject.Icon)
            self.form.secondObjectList.addItem(newItem)


class EqualityConstraint():
    def __init__(self, obj, obj1, obj2, constraintType, components, compStatus):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "Type", "", "", 1)
        obj.Type = constraintType
        obj.addProperty("App::PropertyString", "Object_1")
        obj.Object_1 = obj1
        obj.addProperty("App::PropertyString", "Object_2")
        obj.Object_2 = obj2
        obj.addProperty("App::PropertyBool", "Base_x", "Placement")
        obj.addProperty("App::PropertyBool", "Base_y", "Placement")
        obj.addProperty("App::PropertyBool", "Base_z", "Placement")
        obj.addProperty("App::PropertyBool", "Rot_x", "Placement")
        obj.addProperty("App::PropertyBool", "Rot_y", "Placement")
        obj.addProperty("App::PropertyBool", "Rot_z", "Placement")
        obj.addProperty("App::PropertyPythonObject", "Components", "", "", 4)
        obj.Components = []
        for comp in compStatus:
            setattr(obj, comp, True)
        App.ActiveDocument.Constraints.addObject(obj)

    def onChanged(self, obj, prop):
        """ Callback for propeties changed. It checks which placement
        components have changed and updates the components list when needed
        """
        if prop == "Base_x":
            self.changeComponent(obj, prop, ".Base.x")
        elif prop == "Base_y":
            self.changeComponent(obj, prop, ".Base.y")
        elif prop == "Base_z":
            self.changeComponent(obj, prop, ".Base.z")
        elif prop == "Rot_x":
            self.changeComponent(obj, prop, ".Rotation.x")
        elif prop == "Rot_y":
            self.changeComponent(obj, prop, ".Rotation.y")
        elif prop == "Rot_z":
            self.changeComponent(obj, prop, ".Rotation.z")

    @staticmethod
    def changeComponent(obj, prop, component):
        """ Function that modifies the equality constriant components list when
        one of the component booleans is modified in the property editor. That
        is, when the user adds or deletes an equality constraint to some
        placement component in the property editor.
        obj: the featurepython object of the equality constraint.
        prop: the property of obj being changed.
        component: the component we are interested. For example ".Base.x"
        component will be used to form each variable so its format is important
        """
        # comp1 and comp2 are the variables names used in the solver
        comp1 = obj.Object_1 + component
        comp2 = obj.Object_2 + component
        compPair = [comp1, comp2]
        # for some reason obj.Components.append() does not modfy the list
        # so copying it solves this problem
        compList = obj.Components
        # only check if comp1 is in the list since both comp1 and comp2 should
        # always be in the list. If they are not the solver will fail anyways.
        if compPair in compList:
            if not getattr(obj, prop):
                compList.remove(compPair)
        else:
            if getattr(obj, prop):
                compList.append(compPair)

        obj.Components = compList


Gui.addCommand("Asm4_EqualityConstraint", EqualityConstraintCmd())
