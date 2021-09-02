#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# infoPartCmd.py



import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4



"""
    +-----------------------------------------------+
    |               Helper functions                |
    +-----------------------------------------------+
"""

# allowed types to edit info
partTypes = [ 'App::Part', 'PartDesign::Body']

def checkPart():
    selectedPart = None
    # if an App::Part is selected
    if len(Gui.Selection.getSelection())==1:
        selectedObj = Gui.Selection.getSelection()[0]
        if selectedObj.TypeId in partTypes:
            selectedPart = selectedObj
    return selectedPart



"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class infoPartCmd():
    def __init__(self):
        super(infoPartCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Edit Part Information",
                "ToolTip": "Edit Part Information",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_PartInfo.svg')
                }

    def IsActive(self):
        # We only insert a link into an Asm4  Model
        if App.ActiveDocument and checkPart():
            return True
        return False

    def Activated(self):
        Gui.Control.showDialog( infoPartUI() )




"""
    +-----------------------------------------------+
    |    The UI and functions in the Task panel     |
    +-----------------------------------------------+
"""
class infoPartUI():

    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base        
        iconFile = os.path.join( Asm4.iconPath , 'Asm4_PartInfo.svg')
        self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle("Edit Part Information (Doesn't work yet)")
       
        # hey-ho, let's go
        self.part = checkPart()
        self.makePartInfo()
        self.infoTable = []
        self.getPartInfo()

        # the GUI objects are defined later down
        self.drawUI()


    def getPartInfo(self):
        for prop in self.part.PropertiesList:
            if self.part.getGroupOfProperty(prop)=='PartInfo' :
                if self.part.getTypeIdOfProperty(prop)=='App::PropertyString' :
                    value = self.part.getPropertyByName(prop)
                    self.infoTable.append([prop,value])

    def makePartInfo( self, reset=False ):
        # add the default part information
        for info in Asm4.partInfo:
            if not hasattr(self.part,info):
                self.part.addProperty( 'App::PropertyString', info, 'PartInfo' )
        return

    # close
    def finish(self):
        Gui.Control.closeDialog()

    # standard panel UI buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)

    # Cancel
    def reject(self):
        self.finish()

    # OK: we insert the selected part
    def accept(self):
        for prop in self.infoTable:
            prop[1] = str()
        self.finish()


    # Define the iUI, only static elements
    def drawUI(self):
        # Place the widgets with layouts
        self.mainLayout = QtGui.QVBoxLayout(self.form)
        self.formLayout = QtGui.QFormLayout()

        for prop in self.infoTable:
            checkLayout = QtGui.QHBoxLayout()
            propValue   = QtGui.QLineEdit()
            propValue.setText( str(prop[1]) )
            checked     = QtGui.QCheckBox()
            checkLayout.addWidget(propValue)
            checkLayout.addWidget(checked)
            self.formLayout.addRow(QtGui.QLabel(prop[0]),checkLayout)

        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(QtGui.QLabel())
        
        # Buttons
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.AddNew = QtGui.QPushButton('Add New Info')
        self.Delete = QtGui.QPushButton('Delete Selected')
        self.buttonsLayout.addWidget(self.AddNew)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.Delete)

        self.mainLayout.addLayout(self.buttonsLayout)
        self.form.setLayout(self.mainLayout)

        # Actions





"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_infoPart', infoPartCmd() )

