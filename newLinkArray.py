#!/usr/bin/env python3
# coding: utf-8
#
# newLinkArray.py

import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Draft

import libAsm4 as Asm4


# see whether the Fasteners Workbench is installed
if Asm4.checkWorkbench('FastenersWorkbench'):
    from FastenerBase import FSBaseObject



class newLinkArray():
    """Creating a link array from Draft Workbench"""

    def GetResources(self):
        return {"MenuText": "New Link Array",
                "ToolTip": "Create a new orthogonal or polar array from links",
                "Pixmap": os.path.join(Asm4.iconPath, 'Asm4_LinkArray.svg')
                }


    def IsActive(self):
        if App.ActiveDocument:
            # Only active when a App::Link is selected
            selectObj = self.checkPart()
            if selectObj:
                return (True)
        else:
            return (False)


    def Activated(self):
        # get the selected object
        selectObject = self.checkPart()
        model = App.ActiveDocument.getObject('Model')
        # if something valid has been returned:
        if selectObject:
            # Now is time to create the array
            arrayName = 'array_'+selectObject.Name
            #text, ok = QtGui.QInputDialog.getText(None, 'Create new Link Array', 'Enter new Link Array name: ',
            #                                        text=arrayName)
            #if ok and text:
            #    Draft.makeArray(App.ActiveDocument.getObject(selectObject.Name), App.Vector(1, 0, 0),
            #                    App.Vector(0, 1, 0), 2, 2, useLink=True, name=text)
            createdArray = Draft.makeArray(App.ActiveDocument.getObject(selectObject.Name), App.Vector(10, 0, 0),
                            App.Vector(0, 1, 0), 2, 1, use_link=True, name=arrayName)
            model.addObject(createdArray)
            createdArray.recompute()
            model.recompute()
            App.ActiveDocument.recompute()



    def checkPart(self):
        selectedObj = None
        # check that it's an Assembly4 'Model'
        if App.ActiveDocument.getObject('Model') and App.ActiveDocument.getObject('Model').TypeId=='App::Part':
            if Gui.Selection.getSelection():
                selection = Gui.Selection.getSelection()[0]
                # Only create arrays of links ...
                if selection.TypeId == 'App::Link':
                    selectedObj = selection
                else:
                    # ... and Ffasteners from the FastenersWorkbench
                    for selObj in Gui.Selection.getSelectionEx():
                        obj = selObj.Object
                        if (hasattr(obj,'Proxy') and isinstance(obj.Proxy, FSBaseObject)):
                            selectedObj = obj
        # return what we have found
        return selectedObj



# add the command to the workbench
Gui.addCommand('Asm4_newLinkArray', newLinkArray())


import draftguitools.gui_circulararray
import draftguitools.gui_polararray
import draftguitools.gui_orthoarray
import draftguitools.gui_arrays

class A4OrthoArray(draftguitools.gui_orthoarray.OrthoArray):

    def __init__(self):
        super().__init__()

    def IsActive(self):
        if App.ActiveDocument and self.checkPart():
            # Only active when an App::Link
            # or a Fastener from the Fasteners Workbench is selected
            return True
        else:
            return False

    def Activated(self):
        selectObject = self.checkPart()
        model = App.ActiveDocument.getObject('Model')
        # if something valid has been returned:
        if selectObject:
            # Now is time to create the array
            arrayName = 'array_' + selectObject.Name
            super().Activated()

            # This code is run by the original command.
            # It needs to be integrated somehow into this newer code.
            # Essentially, it just provides a new Label to the link array,
            # and then the Model absorbs it into itself, and it finally
            # recomputes the model.
            #
            # Absorbing into the model could be done manually, by dragging
            # the newly created array.
            # Do we really need to rename and absorb into the model
            # automatically?

            # Gui.doCommand("createdArray = obj")
            # Gui.doCommand("App.ActiveDocument.getObject('Model').addObject(createdArray)")
            # Gui.doCommand("createdArray.Label = " + arrayName)
            # App.ActiveDocument.recompute()

    def checkPart(self):
        """Check that the selection is an App::Link or Fastener."""
        selectedObj = None
        # check that it's an Assembly4 'Model'
        self.doc = App.activeDocument()

        if (self.doc.getObject('Model')
                and self.doc.getObject('Model').TypeId == 'App::Part'):
            if Gui.Selection.getSelection():
                selection = Gui.Selection.getSelection()[0]

                # Only create arrays of App::Links
                # and Fasteners from the Fasteners Workbench
                if selection.TypeId == 'App::Link':
                    selectedObj = selection
                else:
                    for selObj in Gui.Selection.getSelectionEx():
                        obj = selObj.Object
                        if (hasattr(obj, 'Proxy')
                                and isinstance(obj.Proxy, FSBaseObject)):
                            selectedObj = obj

        return selectedObj


Gui.addCommand('Asm4_OrthoArray', A4OrthoArray())


class A4PolarArray(draftguitools.gui_polararray.PolarArray):

    def __init__(self):
        super().__init__()

    def IsActive(self):
        if App.ActiveDocument and self.checkPart():
            # Only active when an App::Link
            # or a Fastener from the Fasteners Workbench is selected
            return True
        else:
            return False

    def Activated(self):
        selectObject = self.checkPart()
        model = App.ActiveDocument.getObject('Model')
        # if something valid has been returned:
        if selectObject:
            # Now is time to create the array
            arrayName = 'array_' + selectObject.Name
            super().Activated()

            # This code is run by the original command.
            # It needs to be integrated somehow into this newer code.
            # Essentially, it just provides a new Label to the link array,
            # and then the Model absorbs it into itself, and it finally
            # recomputes the model.
            #
            # Absorbing into the model could be done manually, by dragging
            # the newly created array.
            # Do we really need to rename and absorb into the model
            # automatically?

            # Gui.doCommand("createdArray = obj")
            # Gui.doCommand("App.ActiveDocument.getObject('Model').addObject(createdArray)")
            # Gui.doCommand("createdArray.Label = " + arrayName)
            # App.ActiveDocument.recompute()

    def checkPart(self):
        """Check that the selection is an App::Link or Fastener."""
        selectedObj = None
        # check that it's an Assembly4 'Model'
        self.doc = App.activeDocument()

        if (self.doc.getObject('Model')
                and self.doc.getObject('Model').TypeId == 'App::Part'):
            if Gui.Selection.getSelection():
                selection = Gui.Selection.getSelection()[0]

                # Only create arrays of App::Links
                # and Fasteners from the Fasteners Workbench
                if selection.TypeId == 'App::Link':
                    selectedObj = selection
                else:
                    for selObj in Gui.Selection.getSelectionEx():
                        obj = selObj.Object
                        if (hasattr(obj, 'Proxy')
                                and isinstance(obj.Proxy, FSBaseObject)):
                            selectedObj = obj

        return selectedObj


Gui.addCommand('Asm4_PolarArray', A4PolarArray())


class A4CircularArray(draftguitools.gui_circulararray.CircularArray):

    def __init__(self):
        super().__init__()

    def IsActive(self):
        if App.ActiveDocument and self.checkPart():
            # Only active when an App::Link
            # or a Fastener from the Fasteners Workbench is selected
            return True
        else:
            return False

    def Activated(self):
        selectObject = self.checkPart()
        model = App.ActiveDocument.getObject('Model')
        # if something valid has been returned:
        if selectObject:
            # Now is time to create the array
            arrayName = 'array_' + selectObject.Name
            super().Activated()

            # This code is run by the original command.
            # It needs to be integrated somehow into this newer code.
            # Essentially, it just provides a new Label to the link array,
            # and then the Model absorbs it into itself, and it finally
            # recomputes the model.
            #
            # Absorbing into the model could be done manually, by dragging
            # the newly created array.
            # Do we really need to rename and absorb into the model
            # automatically?

            # Gui.doCommand("createdArray = obj")
            # Gui.doCommand("App.ActiveDocument.getObject('Model').addObject(createdArray)")
            # Gui.doCommand("createdArray.Label = " + arrayName)
            # App.ActiveDocument.recompute()

    def checkPart(self):
        """Check that the selection is an App::Link or Fastener."""
        selectedObj = None
        # check that it's an Assembly4 'Model'
        self.doc = App.activeDocument()

        if (self.doc.getObject('Model')
                and self.doc.getObject('Model').TypeId == 'App::Part'):
            if Gui.Selection.getSelection():
                selection = Gui.Selection.getSelection()[0]

                # Only create arrays of App::Links
                # and Fasteners from the Fasteners Workbench
                if selection.TypeId == 'App::Link':
                    selectedObj = selection
                else:
                    for selObj in Gui.Selection.getSelectionEx():
                        obj = selObj.Object
                        if (hasattr(obj, 'Proxy')
                                and isinstance(obj.Proxy, FSBaseObject)):
                            selectedObj = obj

        return selectedObj


Gui.addCommand('Asm4_CircularArray', A4CircularArray())
