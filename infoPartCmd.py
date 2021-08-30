#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# infoPartCmd.py



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

# allowed types to edit info
partTypes = [ 'App::Part', 'PartDesign::Body']

def checkPart():
    selectedPart = None
    # if an App::Part is selected
    if len(Gui.Selection.getSelection())==1:
        selectedObj = Gui.Selection.getSelection()[0]
        if selectedObj.TypeId in partTypes:
            selectedPart = selectedObj
    return selectedPart



"""
    +-----------------------------------------------+
    |                  The command                  |
    +-----------------------------------------------+
"""
class infoPartCmd():
    def __init__(self):
        super(infoPartCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": "Edit Part Information",
                "ToolTip": "Edit Part Information",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_PartInfo.svg')
                }

    def IsActive(self):
        # We only insert a link into an Asm4  Model
        if App.ActiveDocument and checkPart():
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
        self.form.setWindowTitle("Edit Part Information (FS Mod)")
       
        # hey-ho, let's go
        self.part = checkPart()
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

    def makePartInfo( self, reset=False ):
        # add the default part information
        for info in Asm4.partInfo:
            try :
                self.part
                if not hasattr(self.part,info):
                    print('object avec option part')
                    self.part.addProperty( 'App::PropertyString', info, 'PartInfo' )
            except AttributeError :
                if self.TypeId == 'App::Part' :
                    print ('object part')
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
        ###Macro pour automatisation des Informations liées à la pièce
        ###et la compatibilité labête de l'atelier paysan [greg]
        ###Nom de la pièce
        ###Désignation
        ###Longueur
        ###Angle 1
        ###Angle 2
        ###Diamètre des troues

        ###Création de la variable de la pièce
        try :
            self.TypeId
            piece=self
        except AttributeError:
            piece=self.part
        
        print (piece.FullName)
        for i in range(len(piece.Group)):
            if piece.Group[i].TypeId == 'PartDesign::Pad' :
                corp=piece.Group[i]
                print (i, 'trouvé')
            else :
                print (i ,'cest pas' ,str(piece.Group[i].FullName))
        try :
            corp
        except NameError :
            print('recherche profonde')
            for i in range(len(piece.Group)):
                if piece.Group[i].TypeId == 'PartDesign::Body' :
                    body=piece.Group[i]
                    print (i, 'trouvé Body')
                    for i in range(len(body.Group)):
                        print(body.FullName)
                        if body.Group[i].TypeId == 'PartDesign::Pad' :
                            corp=body.Group[i]
                            print (i, 'trouvé pad profond')
                else :
                    print ('la pièce : ' ,str(piece.Group[i].FullName), "n'est pas un profile standard")
        try :
            corp
        except NameError :
            print('y a pas moyen pour : ',piece.FullName ) 
            setattr(piece,'Nom_de_la_piece',"'"+piece.Label)
            return
        print(corp.FullName)
        barre=corp
        profile=barre.Profile[0]
        ###Recuperation des variables de la pièce
        test=0
        try :
            ep=float(profile.getDatum('epaisseur'))
            test+=1
            temp=int(ep)
            if ep==temp:
                ep=int(ep)
            ep=str(ep)
        except NameError:
            test=test
        try :
            lar= float(profile.getDatum('largeur'))
            test+=1
            temp=int(lar)
            if lar==temp:
                lar=int(lar)
            lar=str(lar)
        except NameError:
            test=test
        try :
            hau= float(profile.getDatum('hauteur'))
            test+=1
            temp=int(hau)
            if hau==temp:
                hau=int(hau)
            hau=str(hau)
        except NameError:
            test=test
        try :
            conge= float(profile.getDatum('conge'))
            test+=1
        except NameError:
            test=test
        try :
            dia= float(profile.getDatum('diametre'))
            test+=1
            temp=int(dia)
            if dia==temp:
                dia=int(dia)
            dia=str(dia)
        except NameError:
            test=test
        
        ### Déduction du profile

        if test==1:
            descri="fer rond Ø"+dia
        if test==2:
            try :
                descri="Tube rond "+dia+" x "+ep
            except NameError:
                descri="étiré plat "+lar+" x "+ep
        if test==3:
            try:
                if hau==lar:
                    descri="Tube carré "+hau+" x "+ep
                else:
                    descri="Tube rectangulaire "+hau+" x "+lar+" x "+ep
            except NameError:
                descri="fer plat "+lar+" x "+ep
        if test==0:
            print("le profile n'a pas était déterminé : contrainte non nomées")
            descri = "profile non déterminé"

        ###Création de la variable de percage si elle existe
        try:
            troue=App.ActiveDocument.getObject('Hole')
            sktroue=troue.OutList[0]
            troue1= str(len(App.ActiveDocument.getObject(sktroue.Name).Geometry))+" x D : "+str(troue.Diameter)
        except AttributeError:
            troue1=""
        try:
            angle1=str(App.ActiveDocument.getObject('Groove').Angle.Value)
        except AttributeError:
            angle1=""
        try:
            angle2=str(App.ActiveDocument.getObject('Groove001').Angle.Value)
        except AttributeError:
            angle2=""

        ###Recuperation des variables
        nom="'"+piece.Label
        longueur=float(barre.Length)
        temp=int(longueur)
        if longueur==temp:
            longueur=int(longueur)
        longueur=str(longueur)


        ###Ecriture des parametre dans le fichier #PARTINFO# existant
        setattr(piece,'Nom_de_la_piece',nom)
        setattr(piece,'Reference_AP',descri)
        setattr(piece,'Angle1',angle1)
        setattr(piece,'Angle2',angle2)
        setattr(piece,'percage',troue1)
        setattr(piece,'longueur',longueur)


        ###Affichage du résultat
        check=nom+" - "+descri+" - "+longueur+" mm"
        print (check)
        
        ###Actualisation
        try :
            self.getPartInfo()
            print('actualisation')
            for i,prop in enumerate(self.infoTable):
                if self.part.getGroupOfProperty(prop[0])=='PartInfo' :
                    if self.part.getTypeIdOfProperty(prop[0])=='App::PropertyString' :
                        self.infos[i].setText(prop[1])
        except AttributeError:
            pass
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
        self.AddNew = QtGui.QPushButton('Ajouter une nouvelle info')
        self.InfoDefault = QtGui.QPushButton('Info par default')
        self.buttonsLayout.addWidget(self.AddNew)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.InfoDefault)

        self.mainLayout.addLayout(self.buttonsLayout)
        self.form.setLayout(self.mainLayout)

        # Actions
        self.AddNew.clicked.connect(self.addNew)
        self.InfoDefault.clicked.connect(self.infoDefault)





"""
    +-----------------------------------------------+
    |       add the command to the workbench        |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_infoPart', infoPartCmd() )

