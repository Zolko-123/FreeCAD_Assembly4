#!/usr/bin/env python3
# coding: utf-8
#
# treeSelectionOverride.py
#
# The code tracks the selections made

import FreeCADGui as Gui
import FreeCAD as App
import libAsm4 as Asm4


class asm4SelObserver:
    def addSelection(self,doc,obj,sub,pnt):               # Selection object
        # Since both 3D view clicks and manual tree selection gets into the same callback
        # we will determine by clicked coordinates, for manual tree selections the coordinates are (0,0,0)
        if pnt != (0,0,0):
            # 3D view click
            # Get list of objects from the top document to the clicked feature
            objList = App.getDocument(doc).getObject(obj).getSubObjectList(sub)
            # Look for the link from bottom of the list up to the top document
            for subObj in reversed(objList):
                if Asm4.isLinkToPart(subObj):
                    Gui.Selection.clearSelection()
                    # Have to add the '.' at the end to distinguish between features and sub-objects
                    Gui.Selection.addSelection(doc, obj, subObj.Name + '.')
                    break

observer = asm4SelObserver();

def Activate():
    global observer
    # add the listener, 0 forces to resolve the links
    Gui.Selection.addObserver(observer, 0)

def Deactivate():
    global observer
    Gui.Selection.removeObserver(observer) 
