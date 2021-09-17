#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# infoPartCmd.py



import os, shutil

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4

### to have the dir of external configuration file
#wbPath = os.path.dirname(__file__)
wbPath = Asm4.wbPath
InfoKeysFile       = os.path.join( wbPath, 'InfoKeys.py' )
InfoScript         = os.path.join( wbPath, 'InfoScript.py' )
InfoKeysFileInit   = os.path.join( wbPath, 'InfoKeysInit.py' )
InfoScriptInit     = os.path.join( wbPath, 'InfoScriptInit.py' )


### try to open existing external configuration file of user
try :
    fichier = open(InfoKeysFile, 'r')
    fichier.close()
    import InfoKeys as InfoKeys
### else make the default external configuration file
except :
    shutil.copyfile( InfoKeysFileInit , InfoKeysFile )
    import InfoKeys as InfoKeys
### try to open existing external configuration file of user
try :
    fichier = open(InfoScript, 'r')
    fichier.close()
    import InfoScript as autoInfo
### else make the default external configuration file
except :
    shutil.copyfile( InfoScriptInit ,InfoScript)
    import InfoScript as autoInfo



"""
    +-----------------------------------------------+
    |               Helper functions                |
    +-----------------------------------------------+
"""

'''
def checkPart():
    # allowed types to edit info
    partTypes = [ 'App::Part', 'PartDesign::Body']
    selectedPart = None
    # if an App::Part is selected
    if len(Gui.Selection.getSelection())==1:
        selObj = Gui.Selection.getSelection()[0]
        if selObj.TypeId in partTypes:
            selectedPart = selObj
    return selectedPart
'''


"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class infoPartCmd():
    def __init__(self):
        super(infoPartCmd,self).__init__()

    def GetResources(self):
        tooltip  = "Edit part information. "
        tooltip += "The default part information keys are in the file "
        tooltip += "\"FreeCAD/Mod/Assembly4/InfoKeys.py\", edit as you need"
        iconFile = os.path.join( Asm4.iconPath, 'Asm4_PartInfo.svg' )
        return {"MenuText": "Edit Part Information", "ToolTip": tooltip, "Pixmap": iconFile }

    def IsActive(self):
        # We only add infos for some objects
        # if App.ActiveDocument and checkPart():
        if App.ActiveDocument and Asm4.getSelectedContainer():
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
        self.form.setWindowTitle("Edit Part Information")
       
        # hey-ho, let's go
        self.part = Asm4.getSelectedContainer()
        self.infoKeys = InfoKeys.partInfo
        self.makePartInfo()
        self.infoTable = []
        self.getPartInfo()

        # the GUI objects are defined later down
        self.drawUI()


    def getPartInfo(self):
        self.infoTable.clear()
        for prop in self.part.PropertiesList:
            if self.part.getGroupOfProperty(prop)=='PartInfo' :
                if self.part.getTypeIdOfProperty(prop)=='App::PropertyString' :
                    value = self.part.getPropertyByName(prop)
                    self.infoTable.append([prop,value])

    # add the default part information
    def makePartInfo( self, reset=False ):
        for info in self.infoKeys:
            try :
                self.part
                if not hasattr(self.part,info):
                    #object with part
                    self.part.addProperty( 'App::PropertyString', info, 'PartInfo' )
            except AttributeError :
                if self.TypeId == 'App::Part' :
                    #object part
                    self.addProperty( 'App::PropertyString', info, 'PartInfo' )    
        return
    
    # AddNew
    def addNew(self):
        for i,prop in enumerate(self.infoTable):
            if self.part.getGroupOfProperty(prop[0])=='PartInfo' :
                if self.part.getTypeIdOfProperty(prop[0])=='App::PropertyString' :
                    text=self.infos[i].text()
                    setattr(self.part,prop[0],str(text))

    # InfoDefault
    def infoDefault(self):
        autoInfo.infoDefault(self)    

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
        self.addNew()
        self.finish()


    # Define the iUI, only static elements
    def drawUI(self):
        # Place the widgets with layouts
        self.mainLayout = QtGui.QVBoxLayout(self.form)
        self.formLayout = QtGui.QFormLayout()
        self.infos=[]
        for i,prop in enumerate(self.infoTable):
            checkLayout = QtGui.QHBoxLayout()
            propValue = QtGui.QLineEdit()
            propValue.setText( prop[1] )
            checked     = QtGui.QCheckBox()
            checkLayout.addWidget(propValue)
            checkLayout.addWidget(checked)
            self.formLayout.addRow(QtGui.QLabel(prop[0]),checkLayout)
            self.infos.append(propValue)

        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(QtGui.QLabel())
        
        # Buttons
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.editFields = QtGui.QPushButton('Edit Fields')
        self.loadTemplate = QtGui.QPushButton('Load Template')
        self.buttonsLayout.addWidget(self.editFields)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.loadTemplate)

        self.mainLayout.addLayout(self.buttonsLayout)
        self.form.setLayout(self.mainLayout)

        # Actions
        self.editFields.clicked.connect(self.addNew)
        self.loadTemplate.clicked.connect(self.infoDefault)





"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_infoPart', infoPartCmd() )

