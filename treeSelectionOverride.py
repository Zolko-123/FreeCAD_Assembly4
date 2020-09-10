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
                    # TODO: Check why do we have to add '.' at the end to have the selection work
                    Gui.Selection.addSelection(doc, obj, subObj.Name + '.')
                    break

# add the listener, 0 forces to resolve the links
s = asm4SelObserver()
Gui.Selection.addObserver(s, 0)

