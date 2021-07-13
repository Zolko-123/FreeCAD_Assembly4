#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# VariablesLib.py


import os, re

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4



# get the Variables feature
def getVariables():
    retval = None
    if App.ActiveDocument:
        variables = App.ActiveDocument.getObject('Variables')
        if variables and variables.TypeId=='App::FeaturePython':
            retval = variables
    return retval

# check whether an App::Part is selected
def checkPart():
    retval = None
    # if an App::Part is selected
    if Gui.Selection.getSelection():
        selectedObj = Gui.Selection.getSelection()[0]
        if selectedObj.TypeId == 'App::Part':
            retval = selectedObj
    return retval


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
        tooltip  = "Adds a variable into the \"Variables\" placeholder in the document.\n"
        tooltip += "This variable can then be used in any formula using the ExpressionEngine\n"
        tooltip += "of any compatible input field. These are marked with a \"f(x)\" symbol."
        iconFile = os.path.join( Asm4.iconPath , 'Asm4_addVariable.svg')
        return {"MenuText": "Add Variable",
                "ToolTip": tooltip,
                "Pixmap" : iconFile }


    def IsActive(self):
        # if there is an Asm4 Model in the ActiveDocument, or if an App::Part is selected
        if App.ActiveDocument:
            return True
        return False
   

    def Activated(self):
        # retrieve the Variables object
        self.Variables = App.ActiveDocument.getObject('Variables')
        # if it doesn't exist then create it (for older Asm4 documents)
        if not self.Variables:
            self.Variables = Asm4.createVariables()
            part = None
            # if an App::Part is selected:
            if checkPart():
                part = checkPart()
            # if an Asm4 Model is present:
            elif Asm4.getAssembly():
                part = Asm4.getAssembly()
            if part:
                part.addObject(self.Variables)
                #self.Variables =  part.newObject('App::FeaturePython','Variables')
                #self.Variables.ViewObject.Proxy = Asm4.setCustomIcon(object,'Asm4_Variables.svg')
            # create the Variables in the document
            #else:
                #self.Variables = App.ActiveDocument.addObject('App::FeaturePython','Variables')
                #self.Variables.ViewObject.Proxy = Asm4.setCustomIcon(object,'Asm4_Variables.svg')

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
        
        # set focus on the variable name
        self.varName.setFocus()


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
        # select the Variables placeholder so we can see our entry
        self.Variables.recompute()
        Gui.Selection.addSelection(self.Variables)
        self.UI.close()


    def onCancel(self):
        self.UI.close()


    # Verify and handle bad names similar to the spreadsheet workbench
    def onNameEdited(self):
        pattern = re.compile("^[A-Za-z][_A-Za-z0-9]*$")
        if pattern.match(self.varName.text()):
            self.varName.setStyleSheet("color: black;")
            self.OkButton.setEnabled(True)
        else:
            self.varName.setStyleSheet("color: red;")
            self.OkButton.setEnabled(False)


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
        self.varName.textEdited.connect(self.onNameEdited)



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
        if getVariables():
            return True
        return False


    def Activated(self):
        # retrieve the Variables object
        self.Variables = App.ActiveDocument.getObject('Variables')
        # if it doesn't exist then create it (for older Asm4 documents)
        if not self.Variables:
            Asm4.messageBox('There are no variables here')
            return
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
            self.varValue.setText(str(value))
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

variablesCmdList = [ 'Asm4_addVariable', 'Asm4_delVariable' ]
tooltip  = "Adds a variable into the \"Variables\" placeholder in the document.\n"
tooltip += "This variable can then be used in any formula using the ExpressionEngine\n"
tooltip += "of any compatible input field. These are marked with a \"f(x)\" symbol."
Gui.addCommand( 'Asm4_variablesCmd', Asm4.dropDownCmd( variablesCmdList, 'Variables', tooltip ))
