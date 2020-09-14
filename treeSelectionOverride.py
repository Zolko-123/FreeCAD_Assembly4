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

            # Build the name of the selected sub-object for multiple sub-assembly levels
            subObjName = ''
            for subObj in objList:
                if subObj.TypeId == 'App::Link':
                    subObjName = subObjName + subObj.Name + '.'

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
