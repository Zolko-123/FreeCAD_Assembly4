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
            # Get linked object name that handles sub-sub-assembly
            subObjName = Asm4.getLinkedObjectName(doc, obj, sub)

            if subObjName != '':
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(doc, obj, subObjName)

observer = asm4SelObserver();

def Activate():
    global observer
    # add the listener, 0 forces to resolve the links
    Gui.Selection.addObserver(observer, 0)

def Deactivate():
    global observer
    Gui.Selection.removeObserver(observer) 
