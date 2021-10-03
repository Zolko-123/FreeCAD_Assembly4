#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
#
# libraries for FreeCAD's Assembly 4 workbench

import os
import json

import FreeCAD as App

# protection against update of user configuration

### to have the dir of external configuration file
ConfUserDir = os.path.join(App.getUserAppDataDir(),'Asm4_UserConf')
ConfUserFilename = "infoConfUser.json"
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
    
### now user configuration is :
file = open(ConfUserFilejson, 'r')
infoKeysUser = json.load(file).copy()
file.close()


import infoPartCmd

# Autofilling info ref

partInfo =[     'LabelDoc',                 \
                'LabelPart'  ]

infoToolTip = {'LabelDoc':'Return the Label of Document','LabelPart':'Return the Label of Part'}

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

make a description in infoToolTip = {}

put newautoinfofield name in infoDefault() at the end

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
    docLabel = infoKeysUser.get('LabelDoc').get('userData')
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
    partLabel = infoKeysUser.get('LabelPart').get('userData')
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