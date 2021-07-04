#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# HelpCmd.py


import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4
from Asm4_Translate import QT_TRANSLATE_NOOP as Qtranslate




"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class Asm4Help():

    def __init__(self):
        super(Asm4Help, self).__init__()
        self.UI = QtGui.QDialog()
        self.drawUI()


    def GetResources(self):
        return {"MenuText": Qtranslate("Asm4_Help", "Help for Assembly4"),
                "ToolTip": Qtranslate("Asm4_Help", "Show basic usage for FreeCAD and Assembly4"),
                "Pixmap": os.path.join(Asm4.iconPath, 'Asm4_Help.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if App.ActiveDocument:
            return True
        return False 


    def Activated(self):
        # Now we can draw the UI
        self.UI.show()


    """
    +-----------------------------------------------+
    |                      OK                       |
    +-----------------------------------------------+
    """
    def onOK(self):
        self.UI.close()



    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        self.UI.setWindowTitle('Help for FreeCAD and Assembly4')
        self.UI.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.UI.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.UI.setMinimumSize(600, 600)
        self.UI.setModal(False)
        # set main window widgets layout
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        # FreeCAD version info
        FCmajor = App.ConfigGet('ExeVersion')
        FCminor = App.ConfigGet('BuildRevision')
        FCversion = FCmajor+'-'+FCminor
        self.mainLayout.addWidget(QtGui.QLabel('FreeCAD version : \t'+FCversion))

        # Assembly4 version info
        versionPath = os.path.join( Asm4.wbPath, 'VERSION' )
        versionFile = open(versionPath,"r")
        Asm4version = versionFile.readlines()[1]
        versionFile.close()
        self.mainLayout.addWidget(QtGui.QLabel('Assembly4 version : \t'+Asm4version))

        # Help text
        self.helpSource = QtGui.QTextBrowser()
        self.helpSource.setSearchPaths( [os.path.join( Asm4.wbPath, 'Resources' )] )
        self.helpSource.setSource( 'Asm4_Help.html' )
        self.mainLayout.addWidget(self.helpSource)
        self.mainLayout.addWidget(QtGui.QLabel(' '))

        # the button row definition
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.addStretch()
        # OK button
        self.OkButton = QtGui.QPushButton('OK')
        self.OkButton.setDefault(True)
        self.buttonLayout.addWidget(self.OkButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.OkButton.clicked.connect(self.onOK)




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_Help', Asm4Help() )
