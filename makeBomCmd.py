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
#import infoPartCmd
import InfoKeys
#crea = infoPartCmd.infoPartUI.makePartInfo
#rempli = infoPartCmd.infoPartUI.infoDefault



"""
    +-----------------------------------------------+
    |               Helper functions                |
    +-----------------------------------------------+
"""



"""
    +-----------------------------------------------+
    |               prints a parts list             |
    +-----------------------------------------------+
"""

class makeBOM:
    def __init__(self):
        super(makeBOM,self).__init__()

    def GetResources(self):
        tooltip  = "EXPERIMENTAL !!! "
        tooltip += "Create the Bill of Materials of an Assembly"
        iconFile = os.path.join( Asm4.iconPath, 'Asm4_PartsList.svg' )
        return {"MenuText": "Create Part List", "ToolTip": tooltip, "Pixmap": iconFile }


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
        # for the compatibility with the old Model
        try :
            self.model = self.modelDoc.Assembly
        except:
            try:
                self.model = self.modelDoc.Model
                print("legacy Assembly4 Model")
            except:
                print("Hum, this might not work")
        self.drawUI()
        self.UI.show()
        self.BOM.clear()
        self.PartsList = {}
        self.listParts(self.model)
        self.BOM.setPlainText(str(self.PartsList))

### def listParts use of Part info Edit

    def listParts(self,object,level=0):
        if object == None:
            return
        if self.PartsList == None:
            self.PartsList = {}
        # research App::Part because the partInfo attribute is on
        if object.TypeId=='App::Link':
            self.listParts(object.LinkedObject,level+1)
        else:
            if object.TypeId=='App::Part':
                if level > 0:
                    # write PartsList
                    # test if the part already exist on PartsList
                    if object.Label in self.PartsList:
                        # if already exist =+ 1 in qty of this part count
                        self.PartsList[object.Label]['Qty.'] = self.PartsList[object.Label]['Qty.'] + 1
                    else:
                        # if not exist , create a dict() for this part
                        self.PartsList[object.Label] = dict()
                        self.PartsList[object.Label]['Qty.'] = 1
                        for prop in InfoKeys.partInfo:
                            try:
                                # try to get partInfo in part
                                getattr(object,prop)
                                self.PartsList[object.Label][prop] = getattr(object,prop)
                            except AttributeError:
                                print ('you don\'t have fill the info of this Part :',object.Label,prop)
                                # create an entry for that part under its name
                                # usually the first entered is the name or id
                                self.PartsList[object.Label][prop] = object.Label
                                return
                                # crea(object)
                                # rempli(object)
                # look for sub-objects
                for objname in object.getSubObjects():
                    subobj = object.Document.getObject( objname[0:-1] )
                    self.listParts(subobj,level+1)
        return

 
    """def onSave(self):
        #pass
        ###Saves ASCII tree to user system file
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
        #self.UI.close()"""


### def onCopy - Copy on Spreadsheet

    def onCopy(self):
        """Copies Parts List to Spreadsheet"""
        document = App.ActiveDocument
        # init plist whit dict() PartsList
        plist = self.PartsList
        if len(plist) == 0:
            return
        # BOM on Spreadsheet
        if not hasattr(document, 'BOM'):
            spreadsheet = document.addObject('Spreadsheet::Sheet','BOM')
        else:
            spreadsheet = document.BOM

        spreadsheet.Label = "BOM"
        # clean the BOM
        spreadsheet.clearAll()
        # to write line in spreadsheet
        def wrow(drow: [str], row: int):
            for i, d in enumerate(drow):
                spreadsheet.set(str(chr(ord('a') + i)).upper()+str(row+1), str(d))
        # to make list of values of dict() plist
        data = list(plist.values())
        # to write first line with keys
        wrow(data[0].keys(),0)
        # to write line by line BoM in Spreadsheet
        for i,_ in enumerate(data):
            wrow(data[i].values(),i+1)
        
        document.recompute()



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
        self.CopyButton = QtGui.QPushButton('In Spreadsheet')
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
