#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# newPartCmd.py 




import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4



"""
    +-----------------------------------------------+
    |    a class to create all container objects    |
    |         App::Part or PartDesign::Body         |
    +-----------------------------------------------+
"""
class mirrorPartCmd:

    def __init__(self):
        super(mirrorPartCmd,self).__init__()
        self.UI = QtGui.QDialog()
        self.drawUI()

    def GetResources(self):
        tooltip  = 'Create a mirrored part of a part. Use only on individual parts, not assemblies\n'
        tooltip += 'You must re-create the attachment datums in the resulting part'
        iconFile = os.path.join( Asm4.iconPath , 'Asm4_Mirror.svg') 
        return {"MenuText" : 'Create symmetric of part', "ToolTip" : tooltip, "Pixmap" : iconFile }

    def IsActive(self):
        # this works on Parts and Bodies, and links to such
        if Asm4.getSelectedLink() or Asm4.getSelectedContainer():
            return(True)
        else:
            return(False)

    def Activated(self):
        self.selObj = None
        # get the selected object
        if Asm4.getSelectedContainer():
            self.selObj = Asm4.getSelectedContainer()
        elif Asm4.getSelectedLink():
            self.selObj = Asm4.getSelectedLink()
        # should be unnecessary, but who knows
        if self.selObj:
            # initialise the UI
            self.selectedPart.setText(self.selObj.Name)
            proposedName = self.selObj.Label+'_sym'
            self.mirroredPartName.setText(proposedName)
            self.UI.show()

        
    def onOK(self):
        if self.mirroredPartName != '':
            # the mirrored object's name
            symPartName = self.mirroredPartName.text()
            symObjName  = self.selObj.Label+'_mirrored'
            linkObjName = self.selObj.Label+'_link'
            # create Part
            symPart = App.ActiveDocument.addObject( 'App::Part', symPartName )
            # add an LCS at the root of the Part, and attach it to the 'Origin'
            lcs = symPart.newObject('PartDesign::CoordinateSystem','LCS_'+symPart.Name)
            lcs.Support = [(symPart.Origin.OriginFeatures[0],'')]
            lcs.MapMode = 'ObjectXY'
            lcs.MapReversed = False
            # if there is a Parts group, put the symmetrical part there
            partsGroup = Asm4.getPartsGroup()
            if partsGroup:
                partsGroup.addObject(symPart)
            # create a link to the original
            link = symPart.newObject('App::Link',linkObjName)
            link.LinkedObject = self.selObj
            link.Label        = linkObjName
            link.Visibility   = False
            # create the mirrored object
            symObj = symPart.newObject('Part::Mirroring',symObjName)
            symObj.Source = link
            # set the symmetry plane
            if self.symPlane.currentText() == 'X-Y':
                symObj.Normal = App.Vector(0,0,1)
            elif self.symPlane.currentText() == 'X-Z':
                symObj.Normal = App.Vector(0,1,0)
            elif self.symPlane.currentText() == 'Y-Z':
                symObj.Normal = App.Vector(1,0,0)
            else:
                FCC.PrintMessage("ERROR : You shouldn't see this message from mirrorPartCmd()\n")
            # recompute
            symPart.recompute()
            App.ActiveDocument.recompute()
        self.UI.close()


    def onCancel(self):
        self.UI.close()


    # defines the UI, only static elements
    def drawUI(self):
        # Our main window will be a QDialog
        # make this dialog stay above the others, always visible
        self.UI.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.UI.setWindowTitle('Create mirrored Part')
        self.UI.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.UI.setMinimumWidth(300)
        self.UI.setModal(False)
        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self.UI)
        
        # the selected (original) part
        self.mainLayout.addWidget(QtGui.QLabel("Selected Part :"))
        self.selectedPart = QtGui.QLineEdit()
        self.selectedPart.setReadOnly(True)
        self.mainLayout.addWidget(self.selectedPart)
        
        # the symmetry plane
        self.mainLayout.addWidget(QtGui.QLabel("Select the symmetry plane :"))
        self.symPlane = QtGui.QComboBox()
        self.symPlane.addItem('X-Y')
        self.symPlane.addItem('X-Z')
        self.symPlane.addItem('Y-Z')
        self.symPlane.setCurrentIndex( 1 )
        self.mainLayout.addWidget(self.symPlane)

        # the mirrored part's name
        self.mainLayout.addWidget(QtGui.QLabel("Mirrored part's name :"))
        self.mirroredPartName = QtGui.QLineEdit()
        self.mainLayout.addWidget(self.mirroredPartName)

        # Buttons
        self.CancelButton = QtGui.QPushButton('Cancel')
        self.OkButton = QtGui.QPushButton('OK')
        self.OkButton.setDefault(True)
        # the button layout
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.addWidget(self.CancelButton)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.OkButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.CancelButton.clicked.connect(self.onCancel)
        self.OkButton.clicked.connect(self.onOK)


# add the command to the workbench
Gui.addCommand( 'Asm4_mirrorPart', mirrorPartCmd() )

