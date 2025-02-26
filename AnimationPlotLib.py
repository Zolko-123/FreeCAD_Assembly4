#!/usr/bin/env python3
# coding: utf-8
# 
# makeBomCmd.py 
#
# parses the Asm4 Model tree and creates a list of parts



import os
import json

from PySide import QtGui, QtCore
from Asm4_Translate import _atr, QT_TRANSLATE_NOOP
import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4

from AnimationLib import animationProvider
import Asm4_locator


"""
    +-----------------------------------------------+
    |   Plot trajectories in an animation sequence  |
    +-----------------------------------------------+

class animationExporter():
    def __init__(self, animProvider: animationProvider):
        self.animProvider = animProvider
"""


class animationPlotter():
    def __init__(self, animProvider: animationProvider):
        self.animProvider = animProvider
        super(animationPlotter,self).__init__()
        self.UI = QtGui.QDialog()
        # number of points for which to calculate trajectories
        self.nbPts   = 0
        self.nbSteps = 0


    def GetResources(self):
        tooltip  = App.Qt.translate("Asm4_Plot", "Plot trajectories of Points\n\nOnly visible Datum Points are shown")
        iconFile = os.path.join( Asm4.iconPath, 'Asm4_PartsList.svg' )
        return {"MenuText": App.Qt.translate("Asm4_Plot", "Plot Animation"), "ToolTip": tooltip, "Pixmap": iconFile }


    #def Activated(self):
    def openUI(self):
        # get the current active document to avoid errors if user changes tab
        self.modelDoc = App.ActiveDocument
        self.varName  = '?'
        self.varVal   = None
        # for the compatibility with the old Model
        try :
            self.model = self.modelDoc.Model
        except:
            try:
                self.model = self.modelDoc.Assembly
            except:
                print(App.Qt.translate("Asm4_Plot", "Unrecognized assembly type, this might not work"))
        # get the Variables holder
        try : 
            self.Variables = self.model.getObject('Variables')
            # the animated variable
            self.varName = str(self.animProvider.varList.currentText())
            self.varVal = self.Variables.getPropertyByName(self.varName)
        except :
            print(App.Qt.translate("Asm4_Plot", "This Model deosn't seem to have compatible Variables"))
            return

        # show initially the UI
        self.drawUI()
        self.UI.show()
        self.CSV.clear()
        csvtext = App.Qt.translate("Asm4_Plot", '# Running animation sequence on variable \"')+self.varName+App.Qt.translate("Asm4_Plot", '\", please wait... \n')
        self.CSV.setPlainText(csvtext)
        Gui.updateGui()
        
        # Datum points to be plotted
        self.plotPoints = self.getPoints()
        # Title of the CSV document
        title = App.Qt.translate("Asm4_Plot", '# CVS output')
        header1 = App.Qt.translate("Asm4_Plot", 'Iter;Variable;')
        header2 = ' # ;' +self.varName+ ';'
        for i in range(self.nbPts):
            pt = self.plotPoints[i]
            header1 += pt.Name + ';;;'
            header2 += ' X ; Y ; Z ;'
        self.CSV.setPlainText(title)
        self.CSV.appendPlainText(header1)
        self.CSV.appendPlainText(header2)
        # Calculate all the trajectories
        trajectories = self.grabFrames(self.plotPoints, True)
        self.CSV.appendPlainText(App.Qt.translate("Asm4_Plot", 'Finished ')+str(self.nbSteps)+App.Qt.translate("Asm4_Plot", ' iterations'))


    # store the intermediate points
    def grabFrames( self,points=[], printCSV=False ):
        # create empty lists for each points
        trajectories = []
        for i in range(len(points)+1):
            trajectories.append([])         
        firstFrame = True
        endOfCycle = False
        nbFrame    = 0
        # run the animation sequence
        while not endOfCycle:
            endOfCycle = self.animProvider.nextFrame(firstFrame)
            firstFrame = False
            nbFrame += 1;
            Gui.updateGui()
            # current variable value
            varVal = self.Variables.getPropertyByName(self.varName)
            trajectories[0].append(varVal)
            csvtext = str(nbFrame)+';'+str(varVal)+';'
            for i in range(len(points)):
                pt = points[i]
                pla = pt.Placement
                pos = pla.Base
                trajectories[i+1].append(pla)
                csvtext += str(pos.x) +';'+ str(pos.y) +';'+ str(pos.z) +';'
            if printCSV:
                self.CSV.appendPlainText(csvtext)
        # Summary
        self.nbSteps = len(trajectories[0])
        return trajectories


    # gather a table of all visible Datum Points
    def getPoints(self):
        pts = []
        for objName in self.model.getSubObjects():
            obj = self.model.getObject(objName[:-1])
            # we only consider Datum Points that are *visible* 
            if obj.TypeId == 'PartDesign::Point' and obj.Visibility:
                pts.append(obj)
        self.nbPts = len(pts)     
        return pts
        

    def onCancel(self):
        self.animProvider.onStop()
        #document = App.ActiveDocument
        #Gui.Selection.addSelection(document.Name,'BOM')
        self.UI.close()

    def onOK(self):
        self.animProvider.onStop()
        #document = App.ActiveDocument
        #Gui.Selection.addSelection(document.Name,'BOM')
        self.UI.close()

    def close(self):
        self.animProvider.onStop()
        self.UI.close()
    
    def onRefresh(self):
        self.animProvider.onStop()
        self.CSV.clear()
        self.CSV.setPlainText('# CVS output \n')
        trajectories = self.grabFrames(self.plotPoints)
        self.CSV.setPlainText('All trajectories calculated')


    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        self.UI.setWindowTitle(App.Qt.translate("Asm4_Plot", 'Plot trajectories of the animation'))
        self.UI.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.UI.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.UI.setModal(False)
        self.UI.setMinimumWidth(680)
        self.UI.resize(800,600)

        # set main window widgets layout
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        # Help and Log :
        self.winLabel = QtGui.QLabel()
        text = App.Qt.translate("Asm4_Plot", 'Animation Plotter: this tool plots the values of all the variables ' + \
        'and the X,Y,Z coordinates of each *visible* Datum Point ' + \
        'for each step of the animation sequence')
        self.winLabel.setText(text)
        self.winLabel.setWordWrap(True)
        self.mainLayout.addWidget(self.winLabel)
        
        # The CSV file is a plain text field
        self.CSV = QtGui.QPlainTextEdit()
        self.CSV.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        self.mainLayout.addWidget(self.CSV)

        # the button row definition
        self.buttonLayout = QtGui.QHBoxLayout()
        
        # Cancel button
        self.CancelButton = QtGui.QPushButton(App.Qt.translate("Asm4_Plot", 'Cancel'))
        self.CancelButton.setToolTip(App.Qt.translate("Asm4_Plot", "Remove trajectories and Exit"))
        self.buttonLayout.addWidget(self.CancelButton)
        self.buttonLayout.addStretch()
        
        # Refresh button
        self.RefreshButton = QtGui.QPushButton(App.Qt.translate("Asm4_Plot", 'Refresh'))
        self.RefreshButton.setToolTip(App.Qt.translate("Asm4_Plot", "Recalculate animation sequence"))
        self.buttonLayout.addWidget(self.RefreshButton)
        #self.buttonLayout.addStretch()

        # Export button
        self.ExportButton = QtGui.QPushButton(App.Qt.translate("Asm4_Plot", 'Export'))
        self.ExportButton.setToolTip(App.Qt.translate("Asm4_Plot", "Save data as plain text *.CSV file"))
        self.buttonLayout.addWidget(self.ExportButton)
        self.buttonLayout.addStretch()

        # OK button
        self.OkButton = QtGui.QPushButton(App.Qt.translate("Asm4_Plot", 'OK'))
        self.OkButton.setToolTip(App.Qt.translate("Asm4_Plot", 'Close animation widget and keep plots'))
        self.OkButton.setDefault(True)
        self.buttonLayout.addWidget(self.OkButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.OkButton.clicked.connect(self.onOK)
        self.CancelButton.clicked.connect(self.onCancel)





"""
    +-----------------------------------------------+
    |               Helper functions                |
    +-----------------------------------------------+
"""

# usage:
# object = App.ActiveDocument.addObject('App::FeaturePython','objName')
# object.ViewObject.Proxy = setCustomIcon(object,'Icon.svg')
# import base64
# encoded = base64.b64encode(open("filename.png", "rb").read())
class setCustomIcon():
    def __init__( self, obj, iconFile ):
        icon = os.path.join( iconDir , iconFile )
        self.customIcon = icon

    def getIcon(self):
        return self.customIcon
    
    
    
# add the command to the workbench
# Gui.addCommand( 'Asm4_makeBOM', makeBOM() )
