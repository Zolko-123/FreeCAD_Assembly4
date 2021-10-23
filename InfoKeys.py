#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
#
# libraries for FreeCAD's Assembly 4 workbench

import os, json

import FreeCAD as App
import infoPartCmd


# Autofilling info ref
partInfo =[     'LabelDoc',                 \
                'LabelPart',                \
                'PadLength',                \
                'ShapeLength']

infoToolTip = {'LabelDoc':'Return the Label of Document','LabelPart':'Return the Label of Part','PadLength':'Return the Length of Pad','ShapeLength':'Return the Length of Shape'}

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
    for prop in partInfo:
        partInfoDef.setdefault(prop,{'userData':prop + 'User','active':True})
    try:
        os.mkdir(ConfUserDir)
    except:
        pass
    file = open(ConfUserFilejson, 'x')
    json.dump(partInfoDef,file)
    file.close()
    

### now user configuration is :
file = open(ConfUserFilejson, 'r')
infoKeysUser = json.load(file).copy()
file.close()

def infoDefault(self):
    ### auto filling module
    ### load infoKeysUser    
    file = open(ConfUserFilejson, 'r')
    infoKeysUser = json.load(file).copy()
    file.close()
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
    try :
        LabelDoc(self,PART,DOC)
    except NameError :
        print('there is no DOC for this part : ',PART.FullName )
    try :
        LabelPart(self,PART)
    except NameError :
        print('there is no Part' )
    try :    
        PadLength(self,PART,PAD)
    except NameError :
        print('there is no PAD for this Part : ',PART.FullName )
    try :
        ShapeLength(self,PART,SKETCH)
    except NameError :
        print('there is no Sketch for this Part : ',PART.FullName )
"""
how make a new autoinfofield :

ref newautoinfofield name in partInfo[]

make a description in infoToolTip = {}

put newautoinfofield name in infoDefault() at the end with the right arg (PAD,SKETCH...)

write new def like that :

def newautoinfofieldname(self,PART(option : DOC , BODY , PAD , SKETCH):
###you can use DOC - PART - BODY - PAD - SKETCH
    auto_info_field = infoKeysUser.get('newautoinfofieldname').get('userData')
    auto_info_fill = newautoinfofield information
    try:
        ### if the command comes from makeBom write autoinfo directly on Part
        self.TypeId
        setattr(PART,auto_info_field,str(auto_info_fill))
    except AttributeError:
        ### if the command comes from infoPartUI write autoinfo on autofilling field on UI
        try :
        ### if field is actived
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0]== auto_info_field :
                    self.infos[i].setText(str(auto_info_fill))
        except AttributeError:
        ### if field is not actived
            pass

"""

def ShapeLength(self,PART,SKETCH):
###you can use DOC - PART - BODY - PAD - SKETCH
    auto_info_field = infoKeysUser.get('ShapeLength').get('userData')
    try :
        auto_info_fill = SKETCH.Shape.Length
    except AttributeError:
        return
    try:
        ### if the command comes from makeBom write autoinfo directly on Part
        self.TypeId
        setattr(PART,auto_info_field,str(auto_info_fill))
    except AttributeError:
        ### if the command comes from infoPartUI write autoinfo on autofilling field on UI
        try :
        ### if field is actived
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0]== auto_info_field :
                    self.infos[i].setText(str(auto_info_fill))
        except AttributeError:
        ### if field is not actived
            pass
            

def PadLength(self,PART,PAD):
###you can use DOC - PART - BODY - PAD - SKETCH
    auto_info_field = infoKeysUser.get('PadLength').get('userData')
    try :
        auto_info_fill = PAD.Length
    except AttributeError:
        return
    try:
        ### if the command comes from makeBom write autoinfo directly on Part
        self.TypeId
        setattr(PART,auto_info_field,str(auto_info_fill))
    except AttributeError:
        ### if the command comes from infoPartUI write autoinfo on autofilling field on UI
        try :
        ### if field is actived
            for i in range(len(self.infoTable)):
                if self.infoTable[i][0]== auto_info_field :
                    self.infos[i].setText(str(auto_info_fill))
        except AttributeError:
        ### if field is not actived
            pass


        
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