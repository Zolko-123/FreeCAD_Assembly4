#!/usr/bin/env python3
# coding: utf-8
#
# VariablesLib.py


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
class addVariable( QtGui.QDialog ):
    "My tool object"


    def __init__(self):
        super(addVariable,self).__init__()
        self.Variables = []
        self.allowedProperties = [  'App::PropertyBool',
                                    'App::PropertyBoolList',
                                    'App::PropertyInteger',
                                    'App::PropertyIntegerList',
                                    'App::PropertyFloat',
                                    'App::PropertyFloatList',
                                    'App::PropertyString',
                                    'App::PropertyEnumeration',
                                    #'App::PropertyLink',
                                    'App::PropertyXLink',
                                    'App::PropertyVector',
                                    'App::PropertyMatrix', 
                                    'App::PropertyPlacement',
                                    'App::PropertyColor',
                                    'App::PropertyFile']
        self.drawUI()



    def GetResources(self):
        return {"MenuText": "Add Variable",
                "ToolTip": "Add Variable",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_Variables.svg')
                }


    def IsActive(self):
        # is there an active document ?
        if App.ActiveDocument:
            # is something selected ?
            selObj = self.checkSelection()
            if selObj != None:
                return True
        return False 


    def checkSelection(self):
        selectedObj = None
        # check that it's an Assembly4 'Model'
        if App.ActiveDocument.getObject('Model') and App.ActiveDocument.getObject('Model').TypeId=='App::Part':
            model = App.ActiveDocument.getObject('Model')
            # check that something is selected
            if Gui.Selection.getSelection():
            # set the (first) selected object as global variable
                selection = Gui.Selection.getSelection()[0]
                # if the root Model is selected it's OK
                if selection == model:
                    selectedObj = model
                # check that the selected object is a Datum CS or Point type
                if selection.TypeId=='App::FeaturePython' and selection.Name=='Variables':
                    selectedObj = selection
            # if nothing is selected then it's also OK
            else:
                selectedObj = model
        # now we should be safe
        return selectedObj
    

    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # retriev the Variables object
        self.Variables = App.ActiveDocument.getObject('Variables')
        # if it doesn't exist then create it (for older Asm4 documents)
        if not self.Variables:
            self.Variables =  App.ActiveDocument.getObject('Model').newObject('App::FeaturePython','Variables')

        # (re-)initialise the UI
        self.typeList.clear()
        self.varName.clear()
        self.varValue.setValue( 10.0 )
        self.description.clear()
        self.show()

        # get all supported Property types
        for prop in self.Variables.supportedProperties():
            if prop in self.allowedProperties:
                # remove the leading 'App::Property' for clarity
                self.typeList.addItem(prop[13:])

        # find the Float property
        # propFloat = self.typeList.findText( 'App::PropertyFloat' )
        propFloat = self.typeList.findText( 'Float' )
        # if not found
        if propFloat == -1:
            self.typeList.setCurrentIndex( 0 )
        else:
            self.typeList.setCurrentIndex( propFloat )



    """
    +-----------------------------------------------+
    |                      OK                       |
    +-----------------------------------------------+
    """
    def onOK(self):
        # var property type
        propType = self.typeList.currentText()
        # if the variable's name is defined
        varName = self.varName.text()
        if varName:
            # add it to the Variables group of the Variables FeaturePython object
            var = self.Variables.addProperty( 'App::Property'+propType, varName, 'Variables', self.description.toPlainText() )
            # if the variable's value is defined and it's a float
            varValue = self.varValue.value()
            #if varValue and propType=='App::PropertyFloat':
            if varValue and propType=='Float':
                setattr( self.Variables, varName, varValue )
            self.close()
        else:
            self.close()


    """
    +-----------------------------------------------+
    |                     Cancel                    |
    +-----------------------------------------------+
    """
    def onCancel(self):
        self.close()



    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        # make this dialog stay above the others, always visible
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.setWindowTitle('Add Variable')
        self.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumSize(470, 300)
        self.resize(470,300)
        self.setModal(False)
        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self)

        # Define the fields for the form ( label + widget )
        self.formLayout = QtGui.QFormLayout(self)
        # Variable Type, combobox showing all available App::PropertyType
        self.typeList = QtGui.QComboBox(self)
        self.formLayout.addRow(QtGui.QLabel('Type'),self.typeList)
        # Variable Name
        self.varName = QtGui.QLineEdit(self)
        self.formLayout.addRow(QtGui.QLabel('Name'),self.varName)
        # Variable Value
        self.varValue = QtGui.QDoubleSpinBox(self)
        self.varValue.setRange( -1000000.0, 1000000.0 )
        self.formLayout.addRow(QtGui.QLabel('Value'),self.varValue)
        # Documentation
        self.description = QtGui.QTextEdit(self)
        self.formLayout.addRow(QtGui.QLabel('Description'),self.description)
        # apply the layout
        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addStretch()

        # Buttons
        self.buttonLayout = QtGui.QHBoxLayout(self)
        # Cancel button
        self.CancelButton = QtGui.QPushButton('Cancel', self)
        # OK button
        self.OkButton = QtGui.QPushButton('OK', self)
        self.OkButton.setDefault(True)
        # the button layout
        self.buttonLayout.addWidget(self.CancelButton)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.OkButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.setLayout(self.mainLayout)

        # Actions
        self.CancelButton.clicked.connect(self.onCancel)
        self.OkButton.clicked.connect(self.onOK)



"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_addVariable', addVariable() )
