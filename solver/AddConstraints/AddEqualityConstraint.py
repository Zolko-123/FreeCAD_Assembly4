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
        self.form = Gui.PySideUic.loadUi(
            os.path.join(asm4.wbPath,
            "Resources/ui/TaskPanel_EqualityConstraint.ui"))
        # Fill the objects lists
        self.addObjects()

    def accept(self):
        obj1Name = self.form.firstObjectList.selectedItems()[0].text()
        obj2Name = self.form.secondObjectList.selectedItems()[0].text()
        if not obj1Name or not obj2Name:
            print("Select first and second object")
            return
        if self.form.xCheck.isChecked():
            # We want to set the x-coordinates of both objects equal
            obj1 = obj1Name + ".Placement.Base.x"
            obj2 = obj2Name + ".Placement.Base.x"
            self.addConstraintObject(obj1, obj2, "Equality_Constraint")
        if self.form.yCheck.isChecked():
            # we want to set the y-coordinates of both objects equal
            obj1 = obj1Name + ".Placement.Base.y"
            obj2 = obj2Name + ".Placement.Base.y"
            self.addConstraintObject(obj1, obj2, "Equality_Constraint")
        if self.form.zCheck.isChecked():
            # we want to set the z-coordinates of both objects equal
            obj1 = obj1Name + ".Placement.Base.z"
            obj2 = obj2Name + ".Placement.Base.z"
            self.addConstraintObject(obj1, obj2, "Equality_Constraint")
        if self.form.xrotCheck.isChecked():
            # Set rotation about x-axis equal
            obj1 = obj1Name + ".Placement.Rotation.x"
            obj2 = obj2Name + ".Placement.Rotation.x"
            self.addConstraintObject(obj1, obj2, "Equality_Constraint")
        if self.form.yrotCheck.isChecked():
            # set rotation about y-axis equal
            obj1 = obj1Name + ".Placement.Rotation.y"
            obj2 = obj2Name + ".Placement.Rotation.y"
            self.addConstraintObject(obj1, obj2, "Equality_Constraint")
        if self.form.zrotCheck.isChecked():
            # Set rotation about z-axis equal
            obj1 = obj1Name + ".Placement.Rotation.z"
            obj2 = obj2Name + ".Placement.Rotation.z"
            self.addConstraintObject(obj1, obj2, "Equality_Constraint")

        Gui.Control.closeDialog()
        App.ActiveDocument.recompute()

    def addObjects(self):
        for obj in App.ActiveDocument.Objects:
            newItem = QtGui.QListWidgetItem()
            newItem.setText(asm4.nameLabel(obj))
            newItem.setIcon(obj.ViewObject.Icon)
            self.form.firstObjectList.addItem(newItem)
        for obj in App.ActiveDocument.Objects:
            newItem = QtGui.QListWidgetItem()
            newItem.setText(asm4.nameLabel(obj))
            newItem.setIcon(obj.ViewObject.Icon)
            self.form.secondObjectList.addItem(newItem)

    def addConstraintObject(self, obj1, obj2, constraintType):
        newConstraint = App.ActiveDocument.addObject(
            "App::FeaturePython",
            constraintType)
        newConstraint.addProperty("App::PropertyString", "Type", "", "", 1).Type = constraintType
        newConstraint.addProperty("App::PropertyString", "Object_1").Object_1 = obj1
        newConstraint.addProperty("App::PropertyString", "Object_2").Object_2 = obj2
        App.ActiveDocument.Constraints.addObject(newConstraint)

Gui.addCommand("Asm4_EqualityConstraint", EqualityConstraint())
