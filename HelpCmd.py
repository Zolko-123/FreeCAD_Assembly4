#!/usr/bin/env python3
# coding: utf-8
#
# HelpCmd.py


import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import libAsm4 as Asm4




"""
    +-----------------------------------------------+
    |                  main class                   |
    +-----------------------------------------------+
"""
class Asm4Help( QtGui.QDialog ):
    "My tool object"


    def __init__(self):
        super(Asm4Help,self).__init__()


    def GetResources(self):
        return {"MenuText": "Help for Assembly4",
                "ToolTip": "Show basic usage for FreeCAD and Assembly4",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_Help.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if App.ActiveDocument:
            return True
        return False 


    def Activated(self):
        # Now we can draw the UI
        self.drawUI()
        self.show()


    """
    +-----------------------------------------------+
    |                      OK                       |
    +-----------------------------------------------+
    """
    def onOK(self):
        self.close()



    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        self.setWindowTitle('Help for FreeCAD and Assembly4')
        self.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumSize(600, 550)
        self.resize(600,500)
        self.setModal(False)
        # make this dialog stay above the others, always visible
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

        # Version info
        versionPath = os.path.join( Asm4.wbPath, 'VERSION' )
        versionFile = open(versionPath,"r")
        Asm4version = versionFile.readlines()[1]
        FCmajor = App.ConfigGet('ExeVersion')
        FCminor = App.ConfigGet('BuildRevision')
        FCversion = FCmajor+'-'+FCminor
        self.versionFC = QtGui.QLabel(self)
        self.versionFC.setText("FreeCAD version : "+FCversion)
        self.versionFC.move(10,20)
        self.versionAsm4 = QtGui.QLabel(self)
        self.versionAsm4.setText("Assembly4 version : "+Asm4version)
        self.versionAsm4.move(10,50)

        # Help text
        self.helpSource = QtGui.QTextBrowser(self)
        self.helpSource.move(10,90)
        self.helpSource.setMinimumSize(580, 400)
        self.helpSource.setSearchPaths( [os.path.join( Asm4.wbPath, 'Resources' )] )
        self.helpSource.setSource( 'Asm4_Help.html' )

        # OK button
        self.OKButton = QtGui.QPushButton('OK', self)
        self.OKButton.setAutoDefault(True)
        self.OKButton.move(510, 510)
        self.OKButton.setDefault(True)

        # Actions
        self.OKButton.clicked.connect(self.onOK)




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_Help', Asm4Help() )
