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
import Part
import Sketcher
import PartDesign

import Asm4_libs as Asm4



"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class test():
    def __init__(self):
        self.menutext    = "testmenutext"
        self.tooltip     = "testtooltip"
        self.icon        = os.path.join( Asm4.iconPath , 'Asm4_test.svg')

    def GetResources(self):
        return {"MenuText"   : self.menutext,
                "ToolTip"    : self.tooltip,
                "Pixmap"     : self.icon 
                }

    def IsActive(self):
        return(True)
        

    def Activated(self):
        Gui.Control.showDialog( profileUI() )
    
    """def makeProfile(self):
        # init doc
        doc = App.ActiveDocument
        #init name of part
        partName = 'test'
        partNamet=''
        i=1
        if doc.getObject(partName):
            while partName != partNamet :
                n=str(i)		
                partNamet = partName  + n
                print(partNamet)
                if not doc.getObject(partNamet) :
                    partName = partNamet
                i=i+1
        #make part
        newPart =doc.addObject('App::Part',partName)
        # add LCS if appropriate
        # add an LCS at the root of the Part, and attach it to the 'Origin'
        lcs0 = newPart.newObject('PartDesign::CoordinateSystem','LCS_0')
        lcs0.Support = [(newPart.Origin.OriginFeatures[0],'')]
        lcs0.MapMode = 'ObjectXY'
        lcs0.MapReversed = False
        # If the 'Part' group exists, move it there:
        #init partsGroup
        partsGroup = doc.getObject('Parts')
        if partsGroup.TypeId == 'App::DocumentObjectGroup':
            if newPart.Name != 'Assembly':
                partsGroup.addObject(newPart)
                    # recompute
        newPart.recompute()
        App.ActiveDocument.recompute()
        #init part
        part = doc.getObject(partName)

        #init name of body
        bodyName = 'bodytest'
        bodyNamet=''
        i=1
        if doc.getObject(bodyName):
            while bodyName != bodyNamet :
                n=str(i)		
                bodyNamet = bodyName  + n
                print(bodyNamet)
                if not doc.getObject(bodyNamet) :
                    bodyName = bodyNamet
                i=i+1

        #make body
        newBody =doc.addObject('PartDesign::Body',bodyName)
        # add LCS if appropriate
        # add an LCS at the root of the Part, and attach it to the 'Origin'
        lcs0 = newBody.newObject('PartDesign::CoordinateSystem','LCS_0')
        lcs0.Support = [(newBody.Origin.OriginFeatures[0],'')]
        lcs0.MapMode = 'ObjectXY'
        lcs0.MapReversed = False
        # move the body in the part:
        part.addObject(newBody)
        # recompute
        newPart.recompute()
        App.ActiveDocument.recompute()
        #init body
        body = doc.getObject(bodyName)
        #init sketch
        sketchName = 'sketchtest'
        sketchNamet=''
        i=1
        n=1
        if doc.getObject(sketchName):
            while sketchName != sketchNamet :
                n=str(i)		
                sketchNamet = sketchName  + n
                print(sketchNamet)
                if not doc.getObject(sketchNamet) :
                    sketchName = sketchNamet
                i=i+1
        #init support
        support = body.Origin.OriginFeatures[5].Name
        print (support)
        #make sketch
        body.newObject('Sketcher::SketchObject',sketchName)
        #init sketch
        sketch = doc.getObject(sketchName)
        sketch.Support = (doc.getObject(support),[''])
        sketch.MapMode = 'FlatFace'
        #make ext circle
        sketch.addGeometry(Part.Circle(App.Vector(0.000000,-0.000000,0),App.Vector(0,0,1),30.000000),False)
        sketch.addConstraint(Sketcher.Constraint('Coincident',0,3,-1,1)) 
        sketch.addConstraint(Sketcher.Constraint('Diameter',0,60.000000)) 
        sketch.renameConstraint(1, u'diaext')
        #make int circle
        sketch.addGeometry(Part.Circle(App.Vector(0.000000,-0.000000,0),App.Vector(0,0,1),29.000000),False)
        sketch.addConstraint(Sketcher.Constraint('Coincident',1,3,0,3)) 
        sketch.addConstraint(Sketcher.Constraint('Diameter',1,58.000000)) 
        sketch.renameConstraint(3, u'diaint')
        #recompute
        App.ActiveDocument.recompute()
        #init sketch
        padName = 'padtest'
        padNamet=''
        i=1
        if doc.getObject(padName):
            while padName != padNamet :
                n=str(i)		
                padNamet = padName  + n
                print(padNamet)
                if not doc.getObject(padNamet) :
                    padName = padNamet
                i=i+1

        #make pad
        body.newObject('PartDesign::Pad',padName)
        #init pad
        pad = doc.getObject(padName)
        #use sketck for pad
        pad.Profile = sketch
        #length of pad
        pad.Length = 10.0
        #recompute
        App.ActiveDocument.recompute()"""




"""
    +-----------------------------------------------+
    |    The UI and functions in the Task panel     |
    +-----------------------------------------------+
"""
class profileUI():

    def __init__(self):
        #init of widget
        self.base = QtGui.QWidget()
        self.form = self.base        
        iconFile = os.path.join( Asm4.iconPath , 'Asm4_test.svg')
        self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle("Profile Creator")
        
        # the GUI objects are defined later down
        self.drawUI()
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
        self.finish()
        
    def proreset(self):
        self.qledit[0].setEnabled(1)
        self.qledit[1].setEnabled(0)
        self.qledit[2].setEnabled(0)
        self.qledit[3].setEnabled(0)
        self.qledit[4].setEnabled(0)
        self.qledit[5].setEnabled(1)
        
    def on_currentIndexChanged(self):
        print(self.profileType.currentText(), self.profileForm.currentText() )
        self.proreset()
        if self.profileType.currentText()!= 'choisir' and self.profileForm.currentText() != 'choisir':
            if self.profileType.currentText() == 'Tube':
                self.qledit[4].setEnabled(1)
            if self.profileType.currentText() == 'Fer':
                self.qledit[4].clear()
            if self.profileForm.currentText() == 'Rond':
                self.qledit[1].clear()
                self.qledit[2].clear()
                self.qledit[3].setEnabled(1)
            if self.profileForm.currentText() == 'Carré':
                self.qledit[2].clear()
                self.qledit[3].clear()
                self.qledit[1].setEnabled(1)
            if self.profileForm.currentText() == 'Rectangulaire/Plat':
                self.qledit[3].clear()
                self.qledit[1].setEnabled(1)
                self.qledit[2].setEnabled(1)
                

    # Define the iUI, only static elements
    def drawUI(self):
        #init Profile
        self.Profile=[]
        # Place the widgets with layouts
        self.mainLayout = QtGui.QVBoxLayout(self.form)
        self.formLayout = QtGui.QFormLayout()
        
        #profile type data
        checkLayout = QtGui.QHBoxLayout()
        self.profileType = QtGui.QComboBox()
        self.profileType.addItem("choisir")
        self.profileType.addItem("Tube")
        self.profileType.addItem("Fer")
        self.profileType.addItem("Etire")
        checkLayout.addWidget(self.profileType)
        self.formLayout.addRow(QtGui.QLabel('Type'),checkLayout)
        self.profileType.currentIndexChanged.connect(self.on_currentIndexChanged)
        
        #profile form data
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.profileForm = QtGui.QComboBox()
        self.profileForm.addItem("choisir")
        self.profileForm.addItem("Rond")
        self.profileForm.addItem("Carré")
        self.profileForm.addItem("Rectangulaire/Plat")
        checkLayout.addWidget(self.profileForm)
        self.formLayout.addRow(None,checkLayout)
        self.tree = QtGui.QPushButton('tree')
        self.buttonsLayout.addWidget(self.tree)
        self.profileForm.currentIndexChanged.connect(self.on_currentIndexChanged)
        
        self.proconst=[('hauteur',''),('largeur',''),('diametre',''),('epaisseur',''),('longueur','')]
        self.qledit=[]
        checkLayout = QtGui.QHBoxLayout()
        propValue = QtGui.QLineEdit()
        checkLayout.addWidget(propValue)
        self.formLayout.addRow(QtGui.QLabel('nom de la piece'),checkLayout)
        propValue.setEnabled(1)
        self.qledit.append(propValue)
        for i,prop in enumerate(self.proconst):
            checkLayout = QtGui.QHBoxLayout()
            propValue = QtGui.QLineEdit()
            lala = QtGui.QIntValidator ()
            propValue.setValidator(lala)
            checkLayout.addWidget(propValue)
            self.formLayout.addRow(QtGui.QLabel(prop[0]),checkLayout)
            propValue.setEnabled(0)
            self.qledit.append(propValue)

        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(QtGui.QLabel())
        
        # Buttons
        #self.buttonsLayout = QtGui.QHBoxLayout()
        self.One = QtGui.QPushButton('One')
        self.Two = QtGui.QPushButton('Two')
        self.buttonsLayout.addWidget(self.One)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.Two)

        self.mainLayout.addLayout(self.buttonsLayout)
        self.form.setLayout(self.mainLayout)

        # Actions
        self.One.clicked.connect(self.makeProfile)
        self.Two.clicked.connect(self.finish)
        
    def makeProfile(self):
        # init doc
        doc = App.ActiveDocument
        #init name of part
        #partName = 'gt'
        partName = self.qledit[0].text()
        print(partName)
        partNamet=''
        i=1
        if doc.getObject(partName):
            print(partName)
            while partName != partNamet :
                n=str(i)		
                partNamet = partName  + n
                print(partNamet)
                if not doc.getObject(partNamet) :
                    partName = partNamet
                i=i+1
                print(partName)
        #make part
        print(partName)
        newPart = doc.addObject('App::Part',partName)
        # add LCS if appropriate
        # add an LCS at the root of the Part, and attach it to the 'Origin'
        lcs0 = newPart.newObject('PartDesign::CoordinateSystem','LCS_0')
        lcs0.Support = [(newPart.Origin.OriginFeatures[0],'')]
        lcs0.MapMode = 'ObjectXY'
        lcs0.MapReversed = False
        # If the 'Part' group exists, move it there:
        #init partsGroup
        partsGroup = doc.getObject('Parts')
        if partsGroup.TypeId == 'App::DocumentObjectGroup':
            if newPart.Name != 'Assembly':
                partsGroup.addObject(newPart)
                    # recompute
        newPart.recompute()
        App.ActiveDocument.recompute()
        #init part
        part = doc.getObject(partName)

        #init name of body
        bodyName = 'bodytest'
        bodyNamet=''
        i=1
        if doc.getObject(bodyName):
            while bodyName != bodyNamet :
                n=str(i)		
                bodyNamet = bodyName  + n
                print(bodyNamet)
                if not doc.getObject(bodyNamet) :
                    bodyName = bodyNamet
                i=i+1

        #make body
        newBody =doc.addObject('PartDesign::Body',bodyName)
        # add LCS if appropriate
        # add an LCS at the root of the Part, and attach it to the 'Origin'
        lcs0 = newBody.newObject('PartDesign::CoordinateSystem','LCS_0')
        lcs0.Support = [(newBody.Origin.OriginFeatures[0],'')]
        lcs0.MapMode = 'ObjectXY'
        lcs0.MapReversed = False
        # move the body in the part:
        part.addObject(newBody)
        # recompute
        newPart.recompute()
        App.ActiveDocument.recompute()
        #init body
        body = doc.getObject(bodyName)
        #init sketch
        sketchName = 'sketchtest'
        sketchNamet=''
        i=1
        n=1
        if doc.getObject(sketchName):
            while sketchName != sketchNamet :
                n=str(i)		
                sketchNamet = sketchName  + n
                print(sketchNamet)
                if not doc.getObject(sketchNamet) :
                    sketchName = sketchNamet
                i=i+1
        #init support
        support = body.Origin.OriginFeatures[5].Name
        print (support)
        #make sketch
        body.newObject('Sketcher::SketchObject',sketchName)
        #init sketch
        sketch = doc.getObject(sketchName)
        sketch.Support = (doc.getObject(support),[''])
        sketch.MapMode = 'FlatFace'
        #make ext circle
        sketch.addGeometry(Part.Circle(App.Vector(0.000000,-0.000000,0),App.Vector(0,0,1),30.000000),False)
        sketch.addConstraint(Sketcher.Constraint('Coincident',0,3,-1,1)) 
        sketch.addConstraint(Sketcher.Constraint('Diameter',0,int(self.qledit[3].text())) )
        sketch.renameConstraint(1, u'diaext')
        #make int circle
        sketch.addGeometry(Part.Circle(App.Vector(0.000000,-0.000000,0),App.Vector(0,0,1),29.000000),False)
        sketch.addConstraint(Sketcher.Constraint('Coincident',1,3,0,3)) 
        sketch.addConstraint(Sketcher.Constraint('Diameter',1,58.000000)) 
        sketch.renameConstraint(3, u'diaint')
        #recompute
        App.ActiveDocument.recompute()
        #init sketch
        padName = 'padtest'
        padNamet=''
        i=1
        if doc.getObject(padName):
            while padName != padNamet :
                n=str(i)		
                padNamet = padName  + n
                print(padNamet)
                if not doc.getObject(padNamet) :
                    padName = padNamet
                i=i+1

        #make pad
        body.newObject('PartDesign::Pad',padName)
        #init pad
        pad = doc.getObject(padName)
        #use sketck for pad
        pad.Profile = sketch
        #length of pad
        pad.Length = int (self.qledit[5].text())
        #recompute
        App.ActiveDocument.recompute()

# add the command to the workbench
Gui.addCommand( 'Asm4_test',  test() )
