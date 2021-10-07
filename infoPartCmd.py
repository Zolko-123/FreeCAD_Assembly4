#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# infoPartCmd.py



import os, json

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4
import InfoKeys

# protection against update of user configuration

### to have the dir of external configuration file
ConfUserDir = os.path.join(App.getUserAppDataDir(),'Templates')
ConfUserFilename = "Asm4_infoPartConf.json"
ConfUserFilejson = os.path.join(ConfUserDir, ConfUserFilename)


### try to open existing external configuration file of user
try :
    file = open(ConfUserFilejson, 'r')
    file.close()
### else make the default external configuration file
except :
    partInfoDef = dict()
    for prop in InfoKeys.partInfo:
        partInfoDef.setdefault(prop,{'userData':prop + 'User','active':True})
    os.mkdir(ConfUserDir)
    file = open(ConfUserFilejson, 'x')
    json.dump(partInfoDef,file)
    file.close()
    
"""
now user configuration is :
file = open(ConfUserFilejson, 'r')
user configuration = json.load(file).copy()
file.close()
"""

"""
    +-----------------------------------------------+
    |                  The Help Tools               |
    +-----------------------------------------------+
"""
def writeXml(text):
    text=text.encode('unicode_escape').decode().replace('\\','_x_m_l_')
    return text

def decodeXml(text):
    text=text.replace('_x_m_l_','\\').encode().decode('unicode_escape')
    return text

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
        tooltip += "The default part information can be configured"
        tooltip += "use the Config button"
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
        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()
        self.makePartInfo(self,self.part)
        self.infoTable = []
        self.getPartInfo()

        # the GUI objects are defined later down
        self.drawUI()


    def getPartInfo(self):
        self.infoTable.clear()
        for prop in self.part.PropertiesList:
            if self.part.getGroupOfProperty(prop)=='PartInfo' :
                if self.part.getTypeIdOfProperty(prop)=='App::PropertyString' :
                    for propuser in self.infoKeysUser :
                        if self.infoKeysUser.get(propuser).get('userData') == prop :
                            if self.infoKeysUser.get(propuser).get('active'):
                                value = self.part.getPropertyByName(prop)
                                self.infoTable.append([prop,value])

    # add the default part information
    def makePartInfo( self, object , reset=False ):
        for info in self.infoKeysUser:
            if self.infoKeysUser.get(info).get('active'):
                try :
                    object.part
                    if not hasattr(object.part,self.infoKeysUser.get(info).get('userData')):
                        #object with part
                        object.part.addProperty( 'App::PropertyString', self.infoKeysUser.get(info).get('userData'), 'PartInfo' )
                except AttributeError :
                    if object.TypeId == 'App::Part' :
                        #object part
                        if not hasattr(object,self.infoKeysUser.get(info).get('userData')):
                            object.addProperty( 'App::PropertyString', self.infoKeysUser.get(info).get('userData'), 'PartInfo' )    
        return
    
    # AddNew
    def addNew(self):
        for i,prop in enumerate(self.infoTable):
            if self.part.getGroupOfProperty(prop[0])=='PartInfo' :
                if self.part.getTypeIdOfProperty(prop[0])=='App::PropertyString' :
                    for propuser in self.infoKeysUser :
                        if self.infoKeysUser.get(propuser).get('userData') == prop[0] :
                            if self.infoKeysUser.get(propuser).get('active'):
                                text=self.infos[i].text()
                                setattr(self.part,prop[0],str(text))

    # edit info keys
    def editKeys(self):
        Gui.Control.closeDialog()
        Gui.Control.showDialog( infoPartConfUI() )
        #pass
        
    def reInit(self):
        #init of list of all Properties
        List = self.part.PropertiesList
        listpi=[]
        #make list of PartInfo Properties
        for prop in List :
            if self.part.getGroupOfProperty(prop) == 'PartInfo' :
                listpi.append(prop)
        # delete all PartInfo Properties
        for suppr in listpi :
            self.part.removeProperty(suppr)
        # message for user
        mb = QtGui.QMessageBox()
        mb.setText("Your fields \n has been re-initilize")
        mb.setWindowTitle("RE-INITIALISATION")
        mb.exec_() 
        # close
        self.finish()
        

    # InfoDefault
    def infoDefault(self):
        InfoKeys.infoDefault(self)
        #pass

    # close
    def finish(self):
        Gui.Control.closeDialog()

    # standard panel UI buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)

    # Cancel
    def reject(self):
        print("info cancel")
        self.finish()

    # OK: we insert the selected part
    def accept(self):
        self.addNew()
        print("info save")
        self.finish()


    # Define the iUI, only static elements
    def drawUI(self):
        # Place the widgets with layouts
        self.mainLayout = QtGui.QVBoxLayout(self.form)
        self.formLayout = QtGui.QFormLayout()
        self.infos=[]
        for i,prop in enumerate(self.infoTable):
            for propuser in self.infoKeysUser :
                if self.infoKeysUser.get(propuser).get('userData') == prop[0] :
                    if self.infoKeysUser.get(propuser).get('active'):
                        checkLayout = QtGui.QHBoxLayout()
                        propValue = QtGui.QLineEdit()
                        propValue.setText( prop[1] )
                        checkLayout.addWidget(propValue)
                        self.formLayout.addRow(QtGui.QLabel(decodeXml(prop[0])),checkLayout)
                        self.infos.append(propValue)

        self.mainLayout.addLayout(self.formLayout)
        self.mainLayout.addWidget(QtGui.QLabel())
        
        # Buttons
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.confFields = QtGui.QPushButton('Config')
        self.reinit = QtGui.QPushButton('re-init')
        self.reinit.setToolTip('To re-initialize your PartInfo Field of your part')
        self.autoFill = QtGui.QPushButton('auto-filling')
        self.buttonsLayout.addWidget(self.confFields)
        self.buttonsLayout.addWidget(self.reinit)
        self.buttonsLayout.addWidget(self.autoFill)

        self.mainLayout.addLayout(self.buttonsLayout)
        #self.form.setLayout(self.mainLayout)

        # Actions
        self.confFields.clicked.connect(self.editKeys)
        self.reinit.clicked.connect(self.reInit)
        self.autoFill.clicked.connect(self.infoDefault)
        test=False
        try:
            if self.infoTable[0][1]=='':
                test=True
        except IndexError:
            test=True
        if test :
            self.infoDefault()
            self.addNew()

class infoPartConfUI():

    def __init__(self):
        self.base = QtGui.QWidget()
        self.form = self.base
        iconFile = os.path.join( Asm4.iconPath , 'Asm4_PartInfo.svg')
        self.form.setWindowIcon(QtGui.QIcon( iconFile ))
        self.form.setWindowTitle("Edit Part Info Configuration")
       
        # hey-ho, let's go
        self.infoKeysDefault = InfoKeys.partInfo.copy()
        self.infoToolTip = InfoKeys.infoToolTip.copy()
        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()
        # create a dict() of defaultinfokeys and userinfokeys
        self.confTemplate = dict()
        self.confTemplate = self.infoKeysUser.copy()
                
        # the GUI objects are defined later down
        self.drawConfUI()
  
    
    # close
    def finish(self):
        Gui.Control.closeDialog()
        print('exit config')

    # standard panel UI buttons
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)

    # Cancel
    def reject(self):
        print("Cancel")
        self.finish()

    # OK: we write a new config
    def accept(self):
        # init i
        i=0
        # verification of field
        for prop in self.confTemplate:
            if self.infos[i].text() == '':
                mb = QtGui.QMessageBox()
                mb.setText("YOU CAN NOT LEAVE A FIELD BLANK \n DISABLE IT OR DELETE IT")
                mb.setWindowTitle("WRITTING OF NEW CONFIG")
                mb.exec_() 
                return
            i+=1
        # init i
        i=0
        # creation of dict() for user config file
        config=dict()
        for prop in self.confTemplate:
            uData=writeXml(self.infos[i].text())
            config.setdefault(prop,{'userData':uData.replace(" ", "_"),'active':self.checker[i].isChecked()})
            i+=1
        # write user config file
        file = open(ConfUserFilejson, 'w')
        json.dump(config,file)
        file.close()
        # write in infoKeysUser
        file = open(ConfUserFilejson, 'r')
        self.infoKeysUser = json.load(file).copy()
        file.close()
        # message for user
        mb = QtGui.QMessageBox()
        mb.setText("Your configuration \n has been saved")
        mb.setWindowTitle("WRITTING OF NEW CONFIG")
        mb.exec_() 
        # close
        self.finish()
    
    def addNewManField(self):
        # init new default name
        nameref='man'
        indexref=1
        newref = nameref + str(indexref)
        while newref in self.confTemplate :
            indexref+=1
            newref = nameref + str(indexref)
        # init new user name
        newField=self.newOne.text()
        self.newOne.setText('')
        self.addNewField(newref,newField)
    
    def addNewField(self,newref,newField):
        # write new field on confTemplate
        self.confTemplate.setdefault(newref,{'userData': newField,'active': True })
        # write new field on line
        # Label
        newLab = QtGui.QLabel(newref)
        self.gridLayout.addWidget(newLab,self.i,0)
        self.label.append(newLab)
        # Qline
        newOne = QtGui.QLineEdit()
        newOne.setText(newField)
        self.gridLayout.addWidget(newOne,self.i,1)
        self.infos.append(newOne)
        # checkbox
        checkLayout = QtGui.QVBoxLayout()
        checked     = QtGui.QCheckBox()
        checked.setChecked(self.confTemplate.get(newref).get('active') )
        self.gridLayout.addWidget(checked,self.i,2)
        self.checker.append(checked)
        # suppcombo
        self.suppCombo.addItem(newField)
        self.i+=1
    
    # Define the deleteField action   
    def deleteField(self):
        # delete all ref line and infos.text()
        delField = writeXml(self.suppCombo.currentText())
        i=0
        for prop in self.confTemplate:
            if self.confTemplate.get(prop).get('userData') == delField:
                self.label[i].deleteLater()
                self.label.remove( self.label[i])
                self.infos[i].deleteLater()
                self.infos.remove(self.infos[i])
                self.checker[i].deleteLater()
                self.checker.remove(self.checker[i])
                self.suppCombo.removeItem(i-len(self.infoKeysDefault))
                self.refField = str(prop)
            i+=1
        # delete it on confTemplate
        self.confTemplate.pop(self.refField)
        return
    
    # fonction of return if autofield list is update or no and what is new
    def updateAutoFieldlist(self):
        # init list
        listUser=[]
        for li in self.infoKeysUser :
            listUser.append(li)
        listDefault=self.infoKeysDefault.copy()
        for li in listUser:
            try :
                listDefault.remove(li)
            except:
                pass
        if listDefault == [] :
            return None
        else :
            return listDefault
    
    # Define the update autoField module
    # if infoKeys.py Update have new-autoField
    # the user must be able to install them
    def updateAutoField(self):
        upField = self.upCombo.currentText()
        self.upCombo.removeItem(self.upCombo.currentIndex())
        self.addNewField(upField,upField)
        

    # Define the iUI
    def drawConfUI(self):
        # init container
        self.label=[]
        self.infos=[]
        self.checker=[]
        self.combo=[]
        self.upcombo=[]
        # Place the widgets with layouts
        # make multiple layout
        self.mainLayout = QtGui.QVBoxLayout(self.form)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayoutButtons = QtGui.QGridLayout()
        self.gridLayoutUpdate = QtGui.QGridLayout()
        
        # make a first column with default data
        default = QtGui.QLabel('default Data')
        self.gridLayout.addWidget(default,0,0)
        i=1
        for prop in self.confTemplate:
            default = QtGui.QLabel(prop)
            default.setToolTip(self.infoToolTip.get(prop))
            self.gridLayout.addWidget(default,i,0)
            self.label.append(default)
            i+=1
        # make add and delete label
        self.addnewLab = QtGui.QLabel('add New')
        self.gridLayoutButtons.addWidget(self.addnewLab,0,0)
        self.suppLab = QtGui.QLabel('Delete')
        self.gridLayoutButtons.addWidget(self.suppLab,1,0)
        
        # make a second column with user data in QLinEdit
        user = QtGui.QLabel('user Data')
        self.gridLayout.addWidget(user,0,1)
        i=1
        for prop in self.confTemplate:
            propValue = QtGui.QLineEdit()
            propValue.setText( decodeXml(self.confTemplate.get(prop).get('userData')) )
            self.gridLayout.addWidget(propValue,i,1)
            self.infos.append(propValue)
            i+=1
        # make add qline and delete combobox
        # add
        self.newOne = QtGui.QLineEdit()
        self.i=i
        self.gridLayoutButtons.addWidget(self.newOne,0,1)
        # delete
        self.suppCombo =  QtGui.QComboBox()
        for prop in self.confTemplate:
            if prop[0:3] == 'man' :
                self.suppCombo.addItem(decodeXml(self.confTemplate.get(prop).get('userData')))
        self.gridLayoutButtons.addWidget(self.suppCombo,1,1)
        
        # make a third column of QCheckBox for activate or not
        active = QtGui.QLabel('active')
        self.gridLayout.addWidget(active,0,2)
        i=1
        for prop in self.confTemplate:
            checkLayout = QtGui.QVBoxLayout()
            checked     = QtGui.QCheckBox()
            checked.setChecked(self.confTemplate.get(prop).get('active') )
            self.gridLayout.addWidget(checked,i,2)
            self.checker.append(checked)
            i+=1
        self.addnew = QtGui.QPushButton('add New')
        self.gridLayoutButtons.addWidget(self.addnew,0,2)
        self.suppBut = QtGui.QPushButton('Delete')
        self.gridLayoutButtons.addWidget(self.suppBut,1,2)
        # Actions
        self.addnew.clicked.connect(self.addNewManField)
        self.suppBut.clicked.connect(self.deleteField)
            
        # insert layout in mainlayout
        self.mainLayout.addLayout(self.gridLayout)
        self.mainLayout.addLayout(self.gridLayoutButtons)
        
        # If are there update show there
        if self.updateAutoFieldlist() != None :
            updateLab = QtGui.QLabel('Update New Auto-infoField')
            self.gridLayoutUpdate.addWidget(updateLab,0,0)
            self.upCombo =  QtGui.QComboBox()
            self.gridLayoutUpdate.addWidget(self.upCombo,1,0)
            for prop in self.updateAutoFieldlist() :
                self.upCombo.addItem(prop)
            self.upBut = QtGui.QPushButton('Update')
            self.gridLayoutUpdate.addWidget(self.upBut,1,1)
            # Actions
            self.upBut.clicked.connect(self.updateAutoField)
            
            # insert layout in mainlayout
            self.mainLayout.addLayout(self.gridLayoutUpdate)
        
        
        

"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_infoPart', infoPartCmd() )

