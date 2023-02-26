#!/usr/bin/env python3
# coding: utf-8
#
# treeSelectionOverride.py
#
# The code tracks the selections made

import os
from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4


global Asm4_3DselObserver
Asm4_3DselObserver = None


"""
    +-----------------------------------------------+
    |               Selection Filters               |
    +-----------------------------------------------+
    win = Gui.getMainWindow()
    tb = win.findChildren(QtGui.QToolBar)
    for bar in tb:
        bar.objectName()
    for bar in tb:
        if bar.objectName()=='Selection Filter':
            sfbar = bar 
    for button in sfbar.actions():
        button.objectName()
        button.setCheckable(True)
"""
class selectionFilterClearCmd:
    def GetResources(self):
        return {"MenuText": "Clear all selection filters",
                "ToolTip": "Clear all selection filters",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_SelectionAll.svg')
                }
    def IsActive(self):
        return True
    def Activated(self):
        # This function is executed when the command is activated
        Gui.Selection.removeSelectionGate()
        observerDisable()
        uncheckAll()
        FCC.PrintMessage("All selection filters cleared\n")


class selectionFilterVertexCmd:
    def GetResources(self):
        return {"MenuText": "Select only Vertices",
                "ToolTip": "Select only Vertices",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Snap_Vertex.svg')
                }
    def IsActive(self):
        return True
    def Activated(self):
        # This function is executed when the command is activated
        button = 0
        if isChecked(button):
            applyFilter(button)
        else:
            Gui.Selection.removeSelectionGate()


class selectionFilterEdgeCmd:
    def GetResources(self):
        return {"MenuText": "Select only Edges",
                "ToolTip": "Select only Edges",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Snap_Edge.svg')
                }
    def IsActive(self):
        return True
    def Activated(self):
        # This function is executed when the command is activated
        button = 1
        if isChecked(button):
            applyFilter(button)
        else:
            Gui.Selection.removeSelectionGate()


class selectionFilterFaceCmd:
    def GetResources(self):
        return {"MenuText": "Select only Faces",
                "ToolTip": "Select only Faces",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Snap_Face.svg')
                }
    def IsActive(self):
        return True
    def Activated(self):
        # This function is executed when the command is activated
        button = 2
        if isChecked(button):
            applyFilter(button)
        else:
            Gui.Selection.removeSelectionGate()


def getSelectionToolbar():
    mainwin = Gui.getMainWindow()
    sf_tb = None
    for tb in mainwin.findChildren(QtGui.QToolBar):
        if tb.objectName()=='Selection Filter':
            sf_tb = tb
    return sf_tb


def uncheckAll():
    tb = getSelectionToolbar()
    if tb is not None:
        for button in tb.actions()[0:-1]:
            button.setChecked(False)
    Gui.Selection.removeSelectionGate()


def uncheckOthers(button):
    tb = getSelectionToolbar()
    if tb is not None:
        for i in range(len(tb.actions()[0:-1])):
            if i != button:
                tb.actions()[i].setChecked(False)


def isChecked(button):
    tb = getSelectionToolbar()
    status = None
    if tb is not None:
        if len(tb.actions()[0:-1]) >= button:
            status = tb.actions()[button].isChecked()
    return status


def setButton(i,status):
    tb = getSelectionToolbar()
    if tb is not None:
        if len(tb.actions()[0:-1]) >= i:
            tb.actions()[i].setChecked(status)
            

def applyFilter(button):
    subElement = None
    if button == 0:
        subElement = 'Vertex'
    elif button == 1:
        subElement = 'Edge'
    elif button == 2:
        subElement = 'Face'
    if subElement is not None:
        observerDisable()
        filter = Gui.Selection.Filter('SELECT Part::Feature SUBELEMENT '+subElement)
        Gui.Selection.addSelectionGate(filter)
        uncheckOthers(button)




"""
    +-----------------------------------------------+
    |            treeSelectionOverride              |
    +-----------------------------------------------+
"""
class selObserver3DViewCmd( QtGui.QDialog):
    def __init__(self):
        super(selObserver3DViewCmd,self).__init__()
        global Asm4_3DselObserver
        Asm4_3DselObserver = None

    def GetResources(self):
        return {"MenuText": "Enable/Disable 3D View selection mode",
                "ToolTip": "Enable/Disable 3D View selection mode\n\n"    + \
                "Allows to select a Link object in the 3D view\n" + \
                "window instead of the Model tree",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_enableLinkSelection.svg')
                }

    def IsActive(self):
        return True

    def Activated(self):
        global Asm4_3DselObserver
        # This function is executed when the command is activated
        if Asm4_3DselObserver is None:
            uncheckOthers(3)
            observerEnable()
        else:
            observerDisable()



"""
    +-----------------------------------------------+
    |               Asm4_3DselObserver class        |
    +-----------------------------------------------+
"""
class selObserver3DView:
    # Selection object
    def addSelection(self,doc,obj,sub,pnt):
        # Since both 3D view clicks and manual tree selection gets into the same callback
        # we will determine by clicked coordinates, for manual tree selections the coordinates are (0,0,0)
        if pnt != (0,0,0):
            # 3D view click
            objList = App.getDocument(doc).getObject(obj).getSubObjectList(sub)
            # Build the name of the selected sub-object for multiple sub-assembly levels
            subObjName = ''
            # first look for the linked object of the selected entity:
            # Get linked object name that handles sub-sub-assembly
            for subObj in objList:
                if subObj.TypeId=='App::Link':
                    subObjName = subObjName + subObj.Name + '.'
            # if no App::Link found, let's look for other things:
            if subObjName == '':
                for subObj in objList:
                    if subObj.TypeId=='App::Part' or subObj.TypeId=='PartDesign::Body'or subObj.isDerivedFrom('Part::Feature'):
                        # the objList contains also the top-level object, don't count it twice
                        if subObj.Name != obj:
                            subObjName = subObjName + subObj.Name + '.'
            # if we found something, make it the selection
            if subObjName != '':
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(doc, obj, subObjName)
                #FCC.PrintMessage("*"+doc+"*"+obj+"*"+subObjName+"*\n")


def observerEnable():
    # remove any selection filters
    Gui.Selection.removeSelectionGate()
    global Asm4_3DselObserver
    Asm4_3DselObserver = selObserver3DView();
    # add the listener, 0 forces to resolve the links
    Gui.Selection.addObserver(Asm4_3DselObserver, 0)
    setButton(3,True)
    FCC.PrintMessage("Asm4 3D view selection mode is now ENABLED\n")


def observerDisable():
    global Asm4_3DselObserver
    Gui.Selection.removeObserver(Asm4_3DselObserver) 
    setButton(3,False)
    # only print to Console if the Asm4_3DselObserver was there
    if Asm4_3DselObserver:
        FCC.PrintMessage("Asm4 3D view selection mode is now DISABLED\n")
    Asm4_3DselObserver = None


def observerStatus():
    global Asm4_3DselObserver
    status = False
    if Asm4_3DselObserver:
        status = True
    return status




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_SelectionFilterVertexCmd', selectionFilterVertexCmd() )
Gui.addCommand( 'Asm4_SelectionFilterEdgeCmd',   selectionFilterEdgeCmd() )
Gui.addCommand( 'Asm4_SelectionFilterFaceCmd',   selectionFilterFaceCmd() )
Gui.addCommand( 'Asm4_selObserver3DViewCmd',     selObserver3DViewCmd() )
Gui.addCommand( 'Asm4_SelectionFilterClearCmd',  selectionFilterClearCmd() )


