import os
from PySide import QtGui
import FreeCAD as App
import FreeCADGui as Gui
import libAsm4 as asm4


class FixConstraint:
    """
    Adds a fix constraint into the assembly
    """

    def GetResources(self):
        return {
            "MenuText": "Add fix constraint",
            "ToolTip": "Creates a fix constraint into the assembly",
            "Pixmap": os.path.join(asm4.iconPath, "Draft_Dimension.svg")
        }

    def IsActive(self):
        if App.ActiveDocument:
            return (True)
        else:
            return (False)

    def Activated(self):
        panel = FixPanel()
        Gui.Control.showDialog(panel)


class FixPanel:
    def __init__(self):
        self.type = "Fix_Constraint"
        self.form = Gui.PySideUic.loadUi(
            os.path.join(asm4.wbPath,
                "Resources/ui/TaskPanel_FixConstraint.ui"))
        self.addObjects()

    def accept(self):
        obj = self.form.objectList.selectedItems()[0].text()
        qty = App.Units.Quantity
        if self.form.xCheck.isChecked():
            # Fix x coordinate of object
            value = qty(self.form.xVal.text()).Value
            self.addConstraintObject(obj, value, self.type, "Base", "x")
        if self.form.yCheck.isChecked():
            # Fix y coordinate of object
            value = qty(self.form.yVal.text()).Value
            self.addConstraintObject(obj, value, self.type, "Base", "y")
        if self.form.zCheck.isChecked():
            # Fix z coordinate of object
            value = qty(self.form.zVal.text()).Value
            self.addConstraintObject(obj, value, self.type, "Base", "z")
        if self.form.xrotCheck.isChecked():
            # fix rotation about x axis
            value = qty(self.form.xrotVal.text()).Value
            self.addConstraintObject(obj, value, self.type, "Rotation", "x")
        if self.form.yrotCheck.isChecked():
            # fix rotation about y axis
            value = qty(self.form.yrotVal.text()).Value
            self.addConstraintObject(obj, value, self.type, "Rotation", "y")
        if self.form.zrotCheck.isChecked():
            # Fix rotation about z axis
            value = qty(self.form.zrotVal.text()).Value
            self.addConstraintObject(obj, value, self.type, "Rotation", "z")
        Gui.Control.closeDialog()
        App.ActiveDocument.recompute()

    def addObjects(self):
        for obj in App.ActiveDocument.Objects:
            if not obj.TypeId in asm4.datumTypes:
                continue
            newItem = QtGui.QListWidgetItem()
            newItem.setText(obj.Name)
            newItem.setIcon(obj.ViewObject.Icon)
            self.form.objectList.addItem(newItem)

    def addConstraintObject(self, obj, value, constraintType, placement, component):
        newConstraint = App.ActiveDocument.addObject("App::FeaturePython", constraintType)
        newConstraint.addProperty("App::PropertyString", "Type", "", "", 1).Type = constraintType
        newConstraint.addProperty("App::PropertyString", "Object").Object = obj
        newConstraint.addProperty("App::PropertyFloat", "Value").Value = value
        newConstraint.addProperty("App::PropertyString", "Placement").Placement = placement
        newConstraint.addProperty("App::PropertyString", "Component").Component = component
        newConstraint.addProperty("App::PropertyString", "ObjName", "", "", 4)
        newConstraint.ObjName = obj + "." + placement + "." + component
        App.ActiveDocument.Constraints.addObject(newConstraint)

Gui.addCommand("Asm4_FixConstraint", FixConstraint())
