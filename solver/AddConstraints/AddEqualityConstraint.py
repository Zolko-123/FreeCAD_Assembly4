import os
from PySide import QtGui
import FreeCAD as App
import FreeCADGui as Gui
import libAsm4 as asm4


class EqualityConstraint:
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
            os.path.join(asm4.wbPath,
            "Resources/ui/TaskPanel_EqualityConstraint.ui"))
        self.addObjects()

    def accept(self):
        obj1 = self.form.firstObjectList.selectedItems()[0].text()
        obj2 = self.form.secondObjectList.selectedItems()[0].text()
        if not obj1 or not obj2:
            print("Select first and second objects")
            return
        if obj1 == obj2:
            print("Select two distinct objects")
            return
        if self.form.xCheck.isChecked():
            # We want to set the x-coordinates of both objects equal
            self.addConstraintObject(obj1, obj2, self.type, "Base", "x")
        if self.form.yCheck.isChecked():
            # we want to set the y-coordinates of both objects equal
            self.addConstraintObject(obj1, obj2, self.type, "Base", "y")
        if self.form.zCheck.isChecked():
            # we want to set the z-coordinates of both objects equal
            self.addConstraintObject(obj1, obj2, self.type, "Base", "z")
        if self.form.xrotCheck.isChecked():
            # Set rotation about x-axis equal
            self.addConstraintObject(obj1, obj2, self.type, "Rotation", "x")
        if self.form.yrotCheck.isChecked():
            # set rotation about y-axis equal
            self.addConstraintObject(obj1, obj2, self.type, "Rotation", "y")
        if self.form.zrotCheck.isChecked():
            # Set rotation about z-axis equal
            self.addConstraintObject(obj1, obj2, self.type, "Rotation", "z")

        Gui.Control.closeDialog()
        App.ActiveDocument.recompute()

    def addObjects(self):
        # Her we populate the list view widgets
        for obj in App.ActiveDocument.Objects:
            if not obj.TypeId in asm4.datumTypes:
                continue
            newItem = QtGui.QListWidgetItem()
            newItem.setText(obj.Name)
            newItem.setIcon(obj.ViewObject.Icon)
            self.form.firstObjectList.addItem(newItem)
        for obj in App.ActiveDocument.Objects:
            if not obj.TypeId in asm4.datumTypes:
                continue
            newItem = QtGui.QListWidgetItem()
            newItem.setText(asm4.nameLabel(obj))
            newItem.setIcon(obj.ViewObject.Icon)
            self.form.secondObjectList.addItem(newItem)

    def addConstraintObject(self, obj1, obj2, constraintType, placement, component):
        newConstraint = App.ActiveDocument.addObject("App::FeaturePython", constraintType)
        newConstraint.addProperty("App::PropertyString", "Type", "", "", 1).Type = constraintType
        newConstraint.addProperty("App::PropertyString", "Object_1").Object_1 = obj1
        newConstraint.addProperty("App::PropertyString", "Object_2").Object_2 = obj2
        newConstraint.addProperty("App::PropertyString", "Placement").Placement = placement
        newConstraint.addProperty("App::PropertyString", "Component").Component = component
        # Obj1Name and Obj2Name are used as a sort of id for each variable 
        # since the same variable could be on multiple constraints
        newConstraint.addProperty("App::PropertyString", "Obj1Name", "", "", 4)
        newConstraint.Obj1Name = obj1 + "." + placement + "." + component
        newConstraint.addProperty("App::PropertyString", "Obj2Name", "", "", 4)
        newConstraint.Obj2Name = obj2 + "." + placement + "." + component
        App.ActiveDocument.Constraints.addObject(newConstraint)

Gui.addCommand("Asm4_EqualityConstraint", EqualityConstraint())
