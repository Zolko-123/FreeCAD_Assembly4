#!/usr/bin/env python3
# coding: utf-8
# 
# makeBomCmd.py 
#
# parses the Asm4 Model tree and creates a list of parts



import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4




"""
    +-----------------------------------------------+
    |               Helper functions                |
    +-----------------------------------------------+
"""



"""
    +-----------------------------------------------+
    |               prints a parts list             |
    +-----------------------------------------------+
def Partlist(object,level=0):
    indent = '  '*level
    # list the Variables
    if object.Name=='Variables':
        print(indent+'Variables:')
        vars = object
        for prop in vars.PropertiesList:
            if vars.getGroupOfProperty(prop)=='Variables' :
                propValue = vars.getPropertyByName(prop)
                print(indent+'  '+prop+' = '+str(propValue))
    # if its a link, look for the linked object
    elif object.TypeId=='App::Link':
        print(indent+object.Label+' -> '+object.LinkedObject.Document.Name+'#'+object.LinkedObject.Label)
        Partlist(object.LinkedObject,level+1)
    # everything else
    else:
        print(indent+object.Label+' ('+object.TypeId+')')
        # if it's a part, look for sub-objects
        if object.TypeId=='App::Part':
            for objname in object.getSubObjects():
                subobj = object.Document.getObject( objname[0:-1] )
                Partlist(subobj,level+1)
    return
    
    
    
    
import FreeCAD,Draft
import csv

forbbox = ('PartDesign::Body', 'Part::Feature', 'Part::FeaturePython')

def Partlist(object,level=0,tab=None):
    indent = '  '*level
    if tab is None:
        tab = {}
    if object.TypeId=='App::Link':
        print(indent+object.Label+' -> '+object.LinkedObject.Document.Name+'#'+object.LinkedObject.Label+' => '+object.LinkedObject.FullName)
        Partlist(object.LinkedObject,level+1,tab)
    else:
        print(indent+object.Label+' ('+object.TypeId+')')
        if hasattr(object, 'Shape') and object.TypeId in forbbox:
            if object.FullName in tab:
                tab[object.FullName]["count"] = tab[object.FullName]["count"] + 1
            else:
                tab[object.FullName] = {}
                tab[object.FullName]["var"] = {} 
                tab[object.FullName]["count"] = 1

            tab[object.FullName]['label'] = object.Label
            tab[object.FullName]['fullname'] = object.FullName
            tab[object.FullName]['Id'] = object.Label
            bb=object.Shape.BoundBox
            tab[object.FullName]['xlen'] = bb.XLength
            tab[object.FullName]['ylen'] = bb.YLength
            tab[object.FullName]['zlen'] = bb.ZLength
            tab[object.FullName]['volume'] = str(object.Shape.Volume)

            if hasattr(object, 'AttachedTo'):
                tab[object.FullName]['attachedto'] = object.AttachedTo

            print (indent+" => BBox: "+str(object.Shape.BoundBox))		
            print (indent+" => Volume: "+str(object.Shape.Volume))		
        if object.TypeId=='App::Part':
            # look for Variables
            if object.Document.getObject( 'Variables' ):
                print(indent+'  Variables:')
                vars = object.Document.getObject( 'Variables' )
                for prop in vars.PropertiesList:
                    if vars.getGroupOfProperty(prop)=='Variables' :
                        propValue = vars.getPropertyByName(prop)
                        print(indent+'    '+prop+' = '+str(propValue))
                        if not object.FullName in tab:
                            tab[object.FullName] = {}
                            tab[object.FullName]['fullname'] = object.FullName
                            tab[object.FullName]["var"] = {}
                        tab[object.FullName]["var"][prop] = str(propValue) 
            # look for sub-objects
            for objname in object.getSubObjects():
                subobj = object.Document.getObject( objname[0:-1] )
                Partlist(subobj,level+1, tab)
    return tab


def dictoarr(tab): 
    keys = {}
    for obj in tab.keys():
        if isinstance(tab[obj], dict):
            for key in tab[obj].keys():
                if isinstance(tab[obj][key], dict):
                    for inner_key in tab[obj][key].keys():
                        keys[key+"."+inner_key] = {};
                        keys[key+"."+inner_key][0] = key;
                        keys[key+"."+inner_key][1] = inner_key;
                else:
                        keys[key] = 1;
    headings = sorted(keys.keys())

    arr = [ headings ]
    for obj in sorted(tab.keys()):
        line = []
        for head in headings:
            value = ''
            lookup = keys[head]
            if isinstance(lookup, dict):
                if lookup[0] in tab[obj] and lookup[1] in tab[obj][lookup[0]]: 	
                    value = tab[obj][lookup[0]][lookup[1]]
            else:
                if head in tab[obj]:
                    value = tab[obj][head]
            line.append(value)
        arr.append(line)	
    return arr


a = Partlist(FreeCAD.ActiveDocument.getObject("Model"), 0)
print("\n\n")
print(a)
t = dictoarr(a)
print("\n\n")
print(t)

with open('/tmp/table.csv', 'w') as csvfile:
    writer = csv.writer(csvfile, delimiter="\t")
    writer.writerows(t)
    
"""
class makeBOM:
    def __init__(self):
        super(makeBOM,self).__init__()

    def GetResources(self):
        return {"MenuText": "Create Part List",
                "ToolTip": "Create the Bom (Bill of Materials) of an Assembly4 Model",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_PartsList.svg')
                }


    def IsActive(self):
        # return self.checkModel()
        if Asm4.getAssembly() is None:
            return False
        else: 
            return True
        

    def Activated(self):
        self.UI = QtGui.QDialog()
        # get the current active document to avoid errors if user changes tab
        self.modelDoc = App.ActiveDocument
        # self.model = self.modelDoc.Model
        self.model = Asm4.getAssembly()
        self.drawUI()
        self.UI.show()
        self.BOM.clear()
        self.PartsList = ''
        self.listParts(self.model)
        self.BOM.setPlainText(self.PartsList)


    def listParts( self, obj, level=0 ):
        indent = '\n'+'\t'*level
        if obj.Document == self.modelDoc:
            docName = ''
        else:
            docName = obj.Document.Name+'#'
        #partBB = App.BoundBox()
        # list the Variables
        if obj.Name=='Variables':
            #print(indent+'Variables:')
            self.PartsList += indent+'Variables:'
            for prop in obj.PropertiesList:
                if obj.getGroupOfProperty(prop)=='Variables' :
                    propValue = obj.getPropertyByName(prop)
                    self.PartsList += indent+'\t'+prop+' = '+str(propValue)
        # if it's part we look for sub-objects
        elif obj.TypeId=='App::Part':
            self.PartsList += indent +docName +obj.Label
            for objname in obj.getSubObjects():
                subobj = obj.Document.getObject( objname[0:-1] )
                self.listParts( subobj, level+1 )
        # if its a link, look for the linked object
        elif obj.TypeId=='App::Link':
            self.PartsList += indent+obj.Label+' -> '
            self.listParts( obj.LinkedObject, level )
        # if its a Body container we also add the document name and the size
        elif obj.TypeId=='PartDesign::Body':
            self.PartsList += indent +docName +obj.Label
            if obj.Label2:
                self.PartsList += ' ('+obj.Label2+')'
            bb = obj.Shape.BoundBox
            if abs(max(bb.XLength,bb.YLength,bb.ZLength)) < 1e+10:
                Xsize = str(int((bb.XLength * 10)+0.099)/10)
                Ysize = str(int((bb.YLength * 10)+0.099)/10)
                Zsize = str(int((bb.ZLength * 10)+0.099)/10)
                self.PartsList += ', Size: '+Xsize+' x '+Ysize+' x '+Zsize
        # everything else except datum objects
        elif obj.TypeId not in Asm4.datumTypes:
            self.PartsList += indent+obj.Label
            if obj.Label2:
                self.PartsList += ' ('+obj.Label2+')'
            else:
                self.PartsList += ' ('+obj.TypeId+')'
            # if the object has a shape, add it at the end of the line
            if hasattr(obj,'Shape') and obj.Shape.BoundBox.isValid():
                bb = obj.Shape.BoundBox
                if max(bb.XLength,bb.YLength,bb.ZLength) < 1e+10:
                    Xsize = str(int((bb.XLength * 10)+0.099)/10)
                    Ysize = str(int((bb.YLength * 10)+0.099)/10)
                    Zsize = str(int((bb.ZLength * 10)+0.099)/10)
                    self.PartsList += ', Size: '+Xsize+' x '+Ysize+' x '+Zsize
        return


    def onSave(self):
        #pass
        """Saves ASCII tree to user system file"""
        _path = QtGui.QFileDialog.getSaveFileName()
        if _path[0]:
            save_file = QtCore.QFile(_path[0])
            if save_file.open(QtCore.QFile.ReadWrite):
                save_fileContent = QtCore.QTextStream(save_file)
                save_fileContent << self.BOM
                save_file.flush()
                save_file.close()
                self.BOM.setPlainText("Saved to file : " + _path[0])
            else:
                #FCC.PrintError("ERROR : Can't open file : "+ _path[0]+'\n')
                self.BOM.setPlainText("ERROR : Can't open file : " + _path[0])
        else:
            self.BOM.setPlainText("ERROR : Can't open file : " + _path[0])
        QtCore.QTimer.singleShot(3000, lambda:self.BOM.setPlainText(self.PartsList))
        #self.UI.close()


    def isReal( bb ):
        # check if the BoundingBox is a real one
        if bb.isValid() and abs(max(bb.XLength,bb.YLength,bb.ZLength)) < 1e+10:
            return True
        else:
            return False

    '''
    def checkModel(self):
        # check whether there is already a Model in the document
        # Returns True if there is an object called 'Model'
        if App.ActiveDocument and App.ActiveDocument.getObject('Model') and App.ActiveDocument.Model.TypeId=='App::Part':
            return(True)
        else:
            return(False)
    '''


    def onCopy(self):
        """Copies Parts List to clipboard"""
        self.BOM.selectAll()
        self.BOM.copy()
        self.BOM.setPlainText("Copied BoM to clipboard")
        QtCore.QTimer.singleShot(3000, lambda:self.BOM.setPlainText(self.PartsList))


    def onOK(self):
        self.UI.close()


    """
    +-----------------------------------------------+
    |     defines the UI, only static elements      |
    +-----------------------------------------------+
    """
    def drawUI(self):
        # Our main window will be a QDialog
        self.UI.setWindowTitle('Parts List / BOM')
        self.UI.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.UI.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.UI.setModal(False)
        # set main window widgets layout
        self.mainLayout = QtGui.QVBoxLayout(self.UI)

        # The list, is a plain text field
        self.BOM = QtGui.QPlainTextEdit()
        self.BOM.setMinimumSize(600,500)
        self.BOM.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        self.mainLayout.addWidget(self.BOM)

        # the button row definition
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.addStretch()
        # Save button
        self.CopyButton = QtGui.QPushButton('Copy')
        self.buttonLayout.addWidget(self.CopyButton)
        # Save button
        #self.SaveButton = QtGui.QPushButton('Save')
        #self.buttonLayout.addWidget(self.SaveButton)
        # OK button
        self.OkButton = QtGui.QPushButton('Close')
        self.OkButton.setDefault(True)
        self.buttonLayout.addWidget(self.OkButton)
        self.mainLayout.addLayout(self.buttonLayout)

        # finally, apply the layout to the main window
        self.UI.setLayout(self.mainLayout)

        # Actions
        self.CopyButton.clicked.connect(self.onCopy)
        #self.SaveButton.clicked.connect(self.onSave)
        self.OkButton.clicked.connect(self.onOK)

# add the command to the workbench
Gui.addCommand( 'Asm4_makeBOM', makeBOM() )
