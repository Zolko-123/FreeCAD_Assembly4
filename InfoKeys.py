#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
#
# libraries for FreeCAD's Assembly 4 workbench

import os, shutil
import Asm4_libs as Asm4

# protection against update of userconf

### to have the dir of external configuration file
wbPath = Asm4.wbPath
ConfUserFile       = os.path.join( wbPath, 'infoConfUser.py' )
ConfUserFileInit   = os.path.join( wbPath, 'infoConfUserInit.py' )
### try to open existing external configuration file of user
try :
    fichier = open(ConfUserFile, 'r')
    fichier.close()
    fichier.close()
### else make the default external configuration file
except :
    shutil.copyfile( ConfUserFileInit , ConfUserFile )
    
import infoConfUser

import infoPartCmd

# Autofilling info ref

partInfo =[     'LabelDoc',                 \
                'LabelPart' ,               \
                'newUpdateofAsm4' ]

def infoDefault(self):
    ### auto filling module
    
    ### part variable creation
    try :
        self.TypeId
        PART=self
    except AttributeError:
        PART=self.part
    ### you have PART    
    DOC=PART.Document
    ### you have DOC
    ### research
    for i in range(len(PART.Group)):
        if PART.Group[i].TypeId == 'PartDesign::Body' :
            BODY=PART.Group[i]
            ### you have BODY
            for i in range(len(BODY.Group)):
                if BODY.Group[i].TypeId == 'PartDesign::Pad' :
                    PAD=BODY.Group[i]
                    ### you have PAD
                    try :
                        SKETCH=PAD.Profile[0]
                        ### you have SKETCH
                    except NameError :
                        print('there is no Sketch on a Pad of : ',PART.FullName )


    ### start all autoinfofield
    LabelDoc(self,PART,DOC)
    LabelPart(self,PART)
    
"""
how make a new autoinfofield :

ref newautoinfofield name in partInfo[]

ref newautoinfofield name in infoDefault() at the end

write new def like that :

def newautoinfofield(self,PART (opt : DOC , BODY , PAD , SKETCH):
###you can use DOC - PART - BODY - PAD - SKETCH
    auto_info = string you want to write in field
    try:
        ### if the command comes from makeBom write autoinfo directly on Part
        self.TypeId
        auto_info = string 
        setattr(PART,'newautoinfofield name',auto_info)
    except AttributeError:
        ### if the command comes from infoPartUI write autoinfo on autofilling field on UI
        try :
        ### if field is actived
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0]=='newautoinfofield name':
                    self.infos[i].setText(auto_info)
        except AttributeError:
        ### if field is not actived
            pass

"""
        
def LabelDoc(self,PART,DOC):
    docLabel = infoConfUser.partInfo.get('LabelDoc').get('userData')
    try:
        ### if the command comes from makeBom write autoinfo directly on Part
        self.TypeId
        setattr(PART,docLabel,DOC.Label)
    except AttributeError:
        ### if the command comes from infoPartUI write autoinfo on autofilling field on UI
        try :
        ### if field is actived
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0]==docLabel:
                    self.infos[i].setText(DOC.Label)
        except AttributeError:
        ### if field is not actived
            pass
        
def LabelPart(self,PART):
    partLabel = infoConfUser.partInfo.get('LabelPart').get('userData')
    try:
        ### if the command comes from makeBom write autoinfo directly on Part
        self.TypeId
        setattr(PART,partLabel,PART.Label)
    except AttributeError:
        ### if the command comes from infoPartUI write autoinfo on autofilling field on UI
        try :
        ### if field is actived
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0]== partLabel:
                    self.infos[i].setText(PART.Label)
        except AttributeError:
        ### if field is not actived
            pass


    
    pass