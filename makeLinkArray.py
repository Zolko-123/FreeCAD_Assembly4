#!/usr/bin/env python3
# coding: utf-8
#
# makeLinkArray.py



import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, Draft

import libAsm4 as asm4



# see whether the Fasteners Workbench is installed
if asm4.checkWorkbench('FastenersWorkbench'):
    from FastenerBase import FSBaseObject



class newLinkArray():
    """Creating a link array from Draft Workbench"""

    def GetResources(self):
        return {"MenuText": "New Link Array",
                "ToolTip": "Create a new orthogonal or polar array from links",
                "Pixmap": os.path.join(asm4.iconPath, 'Asm4_LinkArray.svg')
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
                            App.Vector(0, 1, 0), 2, 1, useLink=True, name=arrayName)
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



#---------------------------------------------------------------------------
# Python Features definitions
# from Draft/Draft.py
#---------------------------------------------------------------------------

class _DraftObject:
    """The base class for Draft objects"""
    def __init__(self,obj,tp="Unknown"):
        if obj:
            obj.Proxy = self
        self.Type = tp

    def __getstate__(self):
        return self.Type

    def __setstate__(self,state):
        if state:
            self.Type = state

    def execute(self,obj):
        pass

    def onChanged(self, obj, prop):
        pass


class _ViewProviderDraftLink:
    "a view provider for link type object"

    def __init__(self,vobj):
        self.Object = vobj.Object
        vobj.Proxy = self

    def attach(self,vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def getIcon(self):
        tp = self.Object.Proxy.Type
        if tp == 'Array':
            return ":/icons/Draft_LinkArray.svg"
        elif tp == 'PathArray':
            return ":/icons/Draft_PathLinkArray.svg"

    def claimChildren(self):
        obj = self.Object
        if hasattr(obj,'ExpandArray'):
            expand = obj.ExpandArray
        else:
            expand = obj.ShowElement
        if not expand:
            return [obj.Base]
        else:
            return obj.ElementList

#---------------------------------------------------------------------------
# end
#---------------------------------------------------------------------------



# add the command to the workbench
Gui.addCommand('Asm4_makeLinkArray', makeLinkArray())
