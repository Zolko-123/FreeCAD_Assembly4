#!/usr/bin/env python3
# coding: utf-8
#
# placeDatumCmd.py


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part, math, re

from libAsm4 import *



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


    def GetResources(self):
        return {"MenuText": "Add Variable",
                "ToolTip": "Add Variable",
                "Pixmap" : os.path.join( iconPath , 'Asm4_Variables.svg')
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

        # check that we have selected a PartDesign::CoordinateSystem
        self.Variables = App.ActiveDocument.getObject('Variables')

        # Now we can draw the UI
        self.drawUI()
        self.show()

        # get all supported Property types
        for prop in self.Variables.supportedProperties():
            if prop in self.allowedProperties:
                self.typeList.addItem(prop)

        # find the Float property
        propFloat = self.typeList.findText( 'App::PropertyFloat' )
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
            var = self.Variables.addProperty( propType, varName, 'Variables' )
            # if the variable's value is defined and it's a float
            varValue = self.varValue.value()
            if varValue and propType=='App::PropertyFloat':
                setattr( self.Variables, varName, varValue )
            self.close()
        else:
            return


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
        self.setWindowTitle('Add Variable')
        self.setWindowIcon( QtGui.QIcon( os.path.join( iconPath , 'FreeCad.svg' ) ) )
        self.setMinimumSize(470, 330)
        self.resize(470,330)
        self.setModal(False)
        # make this dialog stay above the others, always visible
        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )

        # Variable Type
        self.typeLabel = QtGui.QLabel(self)
        self.typeLabel.setText("Type")
        self.typeLabel.move(10,25)
        # combobox showing all available App::PropertyType
        self.typeList = QtGui.QComboBox(self)
        self.typeList.move(110,20)
        self.typeList.setMinimumSize(350, 1)

        # Variable Name
        self.nameLabel = QtGui.QLabel(self)
        self.nameLabel.setText("Name")
        self.nameLabel.move(10,65)
        # the document containing the linked object
        self.varName = QtGui.QLineEdit(self)
        self.varName.setMinimumSize(350, 1)
        self.varName.move(110,60)

        # Variable Value
        self.valueLabel = QtGui.QLabel(self)
        self.valueLabel.setText("Value")
        self.valueLabel.move(10,105)
        # the document containing the linked object
        self.varValue = QtGui.QDoubleSpinBox(self)
        self.varValue.setMinimumSize(350, 1)
        self.varValue.setRange( -10000.0, 10000.0 )
        self.varValue.setValue( 10.0 )
        self.varValue.move(110,100)

        # Documentation
        self.docLabel = QtGui.QLabel(self)
        self.docLabel.setText("Document")
        self.docLabel.move(10,145)
        # Create a line that will contain full expression for the expression engine
        self.expression = QtGui.QLineEdit(self)
        self.expression.setMinimumSize(350, 100)
        self.expression.move(110, 140)

        # Buttons
        #
        # Cancel button
        self.CancelButton = QtGui.QPushButton('Cancel', self)
        self.CancelButton.setAutoDefault(False)
        self.CancelButton.move(10, 290)

        # OK button
        self.OKButton = QtGui.QPushButton('OK', self)
        self.OKButton.setAutoDefault(True)
        self.OKButton.move(380, 290)
        self.OKButton.setDefault(True)

        # Actions
        self.CancelButton.clicked.connect(self.onCancel)
        self.OKButton.clicked.connect(self.onOK)




"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_addVariable', addVariable() )
