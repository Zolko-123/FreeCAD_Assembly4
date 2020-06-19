#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# VariablesLib.py


import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import libAsm4 as Asm4




"""
    +-----------------------------------------------+
    |               add a new Variable              |
    +-----------------------------------------------+
"""
class addVariable():

    def __init__(self):
        super(addVariable,self).__init__()
        self.UI = QtGui.QDialog()
        self.drawUI()
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


    def GetResources(self):
        return {"MenuText": "Add Variable",
                "ToolTip": "Add Variable",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_addVariable.svg')
                }


    def IsActive(self):
        # if there is an Asm4 Model in the ActiveDocument
        if Asm4.checkModel():
            return True
        return False
   

    def Activated(self):
        # retrieve the Variables object
        self.Variables = App.ActiveDocument.getObject('Variables')
        # if it doesn't exist then create it (for older Asm4 documents)
        if not self.Variables:
            self.Variables =  App.ActiveDocument.getObject('Model').newObject('App::FeaturePython','Variables')

        # (re-)initialise the UI
        self.typeList.clear()
        self.varName.clear()
        self.varValue.setValue( 10.0 )
        self.description.clear()
        self.UI.show()

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
        self.UI.close()


    def onCancel(self):
        self.UI.close()


    # defines the UI, only static elements
    def drawUI(self):
        # Our main window will be a QDialog
        # make this dialog stay above the others, always visible
        self.UI.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.UI.setWindowTitle('Add Variable')
        self.UI.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.UI.setMinimumWidth(470)
        self.UI.resize(470,300)
        self.UI.setModal(False)
        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        # Define the fields for the form ( label + widget )
        self.formLayout = QtGui.QFormLayout()
        # Variable Type, combobox showing all available App::PropertyType
        self.typeList = QtGui.QComboBox()
        self.formLayout.addRow(QtGui.QLabel('Type'),self.typeList)
        # Variable Name
        self.varName = QtGui.QLineEdit()
        self.formLayout.addRow(QtGui.QLabel('Name'),self.varName)
        # Variable Value
        self.varValue = QtGui.QDoubleSpinBox()
        self.varValue.setRange( -1000000.0, 1000000.0 )
        self.formLayout.addRow(QtGui.QLabel('Value'),self.varValue)
        # Documentation
        self.description = QtGui.QTextEdit()
        self.formLayout.addRow(QtGui.QLabel('Description'),self.description)
        # apply the layout
        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addStretch()

        # Buttons
        self.buttonLayout = QtGui.QHBoxLayout()
        # Cancel button
        self.CancelButton = QtGui.QPushButton('Cancel')
        # OK button
        self.OkButton = QtGui.QPushButton('OK')
        self.OkButton.setDefault(True)
        # the button layout
        self.buttonLayout.addWidget(self.CancelButton)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.OkButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.CancelButton.clicked.connect(self.onCancel)
        self.OkButton.clicked.connect(self.onOK)



"""
    +-----------------------------------------------+
    |         delete an existing Variable           |
    +-----------------------------------------------+
"""
class delVariable():

    def __init__(self):
        super(delVariable,self).__init__()
        self.UI = QtGui.QDialog()
        self.drawUI()

    def GetResources(self):
        return {"MenuText": "Delete Variable",
                "ToolTip": "Delete a Variable",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_delVariable.svg')
                }

    def IsActive(self):
        # if there is an Asm4 Model in the ActiveDocument
        if Asm4.checkModel():
            return True
        return False


    def Activated(self):
        # retrieve the Variables object
        self.Variables = App.ActiveDocument.getObject('Variables')
        # if it doesn't exist then create it (for older Asm4 documents)
        if not self.Variables:
            self.Variables =  App.ActiveDocument.getObject('Model').newObject('App::FeaturePython','Variables')

        # (re-)initialise the UI
        self.UI.show()
        self.initUI()


    def onSelectProp(self):
        # the currently selected variable
        selectedProp = self.varList.currentText()
        # if it's indeed a property in the Variables object (one never knows)
        if selectedProp in self.Variables.PropertiesList:
            # get its value
            self.varName.setText(selectedProp)
            value = self.Variables.getPropertyByName(selectedProp)
            self.varValue.setText(value)
        return


    def onDel(self):
        # var property type
        selectedProp = self.varList.currentText()
        if selectedProp in self.Variables.PropertiesList:
            self.Variables.removeProperty(selectedProp)
        self.initUI()


    def onCancel(self):
        self.UI.close()


    #
    def initUI(self):
        self.varName.clear()
        self.varValue.clear()
        self.description.clear()
        self.varList.clear()
        self.varList.addItem('Please choose')
        for var in self.Variables.PropertiesList:
            if self.Variables.getGroupOfProperty(var)=='Variables' :
                self.varList.addItem(var)
        

    # defines the UI, only static elements
    def drawUI(self):
        # Our main window will be a QDialog
        # make this dialog stay above the others, always visible
        self.UI.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.UI.setWindowTitle('Delete Variable')
        self.UI.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.UI.setMinimumWidth(470)
        self.UI.resize(470,300)
        self.UI.setModal(False)
        # the layout for the main window is vertical (top to down)
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        # Define the fields for the form ( label + widget )
        self.formLayout = QtGui.QFormLayout()
        # existing Variable
        self.varList = QtGui.QComboBox()
        self.formLayout.addRow(QtGui.QLabel('Variable'),self.varList)
        # Variable Name
        self.varName = QtGui.QLineEdit()
        self.formLayout.addRow(QtGui.QLabel('Name'),self.varName)
        # Variable Value
        self.varValue = QtGui.QLineEdit()
        self.formLayout.addRow(QtGui.QLabel('Value'),self.varValue)
        # Documentation
        self.description = QtGui.QTextEdit()
        self.formLayout.addRow(QtGui.QLabel('Description'),self.description)
        # apply the layout
        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addStretch()

        # Buttons
        self.buttonLayout = QtGui.QHBoxLayout()
        # Cancel button
        self.CancelButton = QtGui.QPushButton('Cancel')
        # Delete button
        self.DelButton = QtGui.QPushButton('Delete')
        self.DelButton.setDefault(True)
        # the button layout
        self.buttonLayout.addWidget(self.CancelButton)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.DelButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.varList.currentIndexChanged.connect( self.onSelectProp )
        self.CancelButton.clicked.connect(self.onCancel)
        self.DelButton.clicked.connect(self.onDel)





"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_addVariable', addVariable() )
Gui.addCommand( 'Asm4_delVariable', delVariable() )
