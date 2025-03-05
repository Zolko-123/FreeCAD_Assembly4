#!/usr/bin/env python3
# coding: utf-8
#
# FastenersLib.py




import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC
from FastenerBase import FSBaseObject
from ScrewMaker import screwTables
import FastenersCmd as FS

from . import Asm4_libs as Asm4
from .Asm4_Translate import translate



# icon to show in the Menu, toolbar and widget window
iconFile = os.path.join( Asm4.iconPath , 'Asm4_mvFastener.svg')




"""
    +-----------------------------------------------+
    |        a class to create all fasteners        |
    |       from the Fasteners WB (ScrewMaker)      |
    +-----------------------------------------------+

Gui.activateWorkbench('FastenersWorkbench')
Gui.activateWorkbench('Assembly4Workbench')
import FastenersCmd as FS
fs = App.ActiveDocument.addObject("Part::FeaturePython",'Screw')
FS.FSScrewObject( fs, 'ISO4762', None )
fs.Label = fs.Proxy.itemText
FS.FSViewProviderTree(fs.ViewObject)
fs.ViewObject.ShapeColor = (0.3, 0.6, 0.7)
# (0.85, 0.3, 0.5)
# (1.0, 0.75, 0)
fs.recompute()
Gui.Selection.addSelection(fs)
Gui.runCommand('FSChangeParams')
    
"""

class insertFastener:
    "My tool object"
    def __init__(self, fastenerType):
        self.FSclass = fastenerType
        self.FScolor = {'Screw' : (0.3, 0.6, 0.7),
                        'Nut'   : (0.85, 0.3, 0.5),
                        'Washer': (1.0, 0.75, 0.0),
                        'ThreadedRod':(0.3, 0.5, 0.75)
                        }
        # Screw
        if  self.FSclass      == 'Screw':
            self.menutext     = translate("Fasteners", "Insert Screw")
            self.tooltip      = translate("Fasteners", "<p>Insert a Screw into the Assembly</p>"
            + "<p>If another fastener is selected, a new fastener of the same type is created in the same assembly."
            + "If an axis or LCS is selected, the new fastener will be attached to it."
            + "If an assembly is selected, the new fastener will be inside that assembly.</p>")
            self.icon         = os.path.join( Asm4.iconPath , 'Asm4_Screw.svg')
        # Nut
        elif self.FSclass     == 'Nut':
            self.menutext     = translate("Fasteners", "Insert Nut")
            self.tooltip      = translate("Fasteners", "<p>Insert a Nut into the Assembly</p>"
            + "<p>If another fastener is selected, a new fastener of the same type is created in the same assembly."
            + "If an axis or LCS is selected, the new fastener will be attached to it."
            + "If an assembly is selected, the new fastener will be inside that assembly.</p>")
            self.icon         = os.path.join( Asm4.iconPath , 'Asm4_Nut.svg')
        # Washer
        elif self.FSclass     == 'Washer':
            self.menutext     = translate("Fasteners", "Insert Washer")
            self.tooltip      = translate("Fasteners", "<p>Insert a Washer into the Assembly</p>"
            + "<p>If another fastener is selected, a new fastener of the same type is created in the same assembly."
            + "If an axis or LCS is selected, the new fastener will be attached to it."
            + "If an assembly is selected, the new fastener will be inside that assembly.</p>")
            self.icon         = os.path.join( Asm4.iconPath , 'Asm4_Washer.svg')
        # Threaded Rod (makes errors)
        elif self.FSclass     == 'ThreadedRod':
            self.menutext     = translate("Fasteners", "Insert threaded rod")
            self.tooltip      = translate("Fasteners", "Insert threaded rod")
            self.icon         = os.path.join( Asm4.iconPath , 'Asm4_Rod.svg')


    def GetResources(self):
        return {"MenuText": self.menutext,
                "ToolTip" : self.tooltip,
                "Pixmap"  : self.icon }

    def IsActive(self):
        # if Asm4.getAssembly():
        if App.ActiveDocument:
            return True
        return None

    def Activated(self):
        # check that the Fasteners WB has been loaded before:
        if not 'Fasteners_ChangeParameters' in Gui.listCommands():
            Gui.activateWorkbench('FastenersWorkbench')
            Gui.activateWorkbench('Assembly4Workbench')
        # if something is selected
        container = None
        attLink   = ''
        attDoc    = ''
        attLcs    = ''
        lcsAxis   = ''
        fsClass   = self.FSclass
        fsType    = None
        selObj    = None

        if len(Gui.Selection.getSelection())==1:
            selObj = Gui.Selection.getSelection()[0]
            selEx  = Gui.Selection.getSelectionEx('', 0)[0]
            # if it's a container, we'll put it there
            if selObj.TypeId == 'App::Part':
                container = selObj
            # if a fastener is selected, we duplicate it
            elif isFastener(selObj):
                try:
                    fs = screwTables[selObj.type][0]
                    if fs in ['Screw','Nut','Washer']:
                        fsClass   = fs
                        fsType    = selObj.type
                        container = selObj.getParentGeoFeatureGroup()
                except:
                    FCC.PrintMessage(translate("Fasteners", "Selected object doesn't seem to be a valid fastener, ignoring\n"))
            # if it's a datum we place the fasteners on it
            elif selObj.TypeId in Asm4.datumTypes:
                # the datum is in the same document
                if len(selEx.SubElementNames[0].split('.'))==2:
                    # double check
                    if selEx.SubElementNames[0].split('.')[0]==selObj.Name:
                        attLcs  = selObj.Name
                        container = selObj.getParentGeoFeatureGroup()
                        lcsAxis = selEx.SubElementNames[0].split('.')[1]
                # the datum is in a linked child
                elif len(selEx.SubElementNames[0].split('.'))==3:
                    # double check
                    if selEx.SubElementNames[0].split('.')[1]==selObj.Name:
                        # we treat links only for assemblies
                        if Asm4.getAssembly():
                            attLink = selEx.SubElementNames[0].split('.')[0]
                            attDoc  = selObj.getParentGeoFeatureGroup().Document.Name
                            attLcs  = selObj.Name
                            container = Asm4.getAssembly()
                            lcsAxis = selEx.SubElementNames[0].split('.')[2]
                # placeObjectToLCS( fastener, attLink, attDoc, attLCS ):
        elif Asm4.getAssembly() and not Gui.Selection.hasSelection() :
            container = Asm4.getAssembly()
        # create the fastener
        newFastener = App.ActiveDocument.addObject("Part::FeaturePython",fsClass)
        # if a previous fastener was selected, we match its parameters
        if fsType:
            FS.FSScrewObject( newFastener, fsType, None )
            newFastener.recompute()
            newFastener.diameter = selObj.diameter
            newFastener.recompute()
            if hasattr(newFastener,'length'):
                try:
                    newFastener.length = selObj.length
                except:
                    FCC.PrintMessage("Length \""+selObj.length+"\" is not available, ignoring\n")
        # we create a new fastener as asked
        else:
            if fsClass == 'Screw':
                FS.FSScrewObject( newFastener, 'ISO7045', None )
            elif fsClass == 'Nut':
                FS.FSScrewObject( newFastener, 'ISO4032', None )
            elif fsClass == 'Washer':
                FS.FSScrewObject( newFastener, 'ISO7089', None )
            elif fsClass == 'ThreadedRod':
                FS.FSThreadedRodObject( newFastener, None )
        # make the Proxy and stuff
        # newFastener.Label = newFastener.Proxy.itemText
        FS.FSViewProviderTree(newFastener.ViewObject)
        # if a container was selected, put it there
        if container:
            container.addObject(newFastener)
        # apply custom Asm4 colours:
        try:
            newFastener.ViewObject.ShapeColor = self.FScolor[fsClass]
        except:
            FCC.PrintMessage("unknown fastener type \""+str(fsClass)+"\", ignoring\n")
        # add AttachmentEngine
        # oooops, no, creates problems because it creates an AttachmentOffset property that collides with Asm4
        # newFastener.addExtension("Part::AttachExtensionPython")
        # if a datum was selected, attach the fastener to it
        if attLcs:
            Asm4.placeObjectToLCS( newFastener, attLink, attDoc, attLcs )
            # rotate to X-Y-Z axis if appropriate
            if lcsAxis=='X':
                newFastener.AttachmentOffset = newFastener.AttachmentOffset * Asm4.rotY
            elif lcsAxis=='Y':
                newFastener.AttachmentOffset = newFastener.AttachmentOffset * Asm4.rotX.inverse()
            else:
                pass
        # ... and select it
        newFastener.recompute()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection( newFastener )
        # Gui.runCommand('FSChangeParams')
        # Gui.runCommand( 'Asm4_placeFastener' )




"""
    +-----------------------------------------------+
    |         wrapper for FSChangeParams            |
    +-----------------------------------------------+
"""
class changeFSparametersCmd():

    def __init__(self):
        super(changeFSparametersCmd,self).__init__()

    def GetResources(self):
        return {"MenuText": translate("Fasteners", "Change Fastener parameters"),
                "ToolTip": translate("Fasteners", "Change Fastener parameters"),
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_FSparams.svg')
                }

    def IsActive(self):
        if App.ActiveDocument and getSelectionFS():
            return True
        return False

    def Activated(self):
        # check that the Fasteners WB has been loaded before:
        if not 'Fasteners_ChangeParameters' in Gui.listCommands():
            Gui.activateWorkbench('FastenersWorkbench')
            Gui.activateWorkbench('Assembly4Workbench')
        # check that we have selected a Fastener from the Fastener WB
        selection = getSelectionFS()
        if selection:
            try:
                Gui.runCommand('Fasteners_ChangeParameters')
            except:
                Gui.runCommand('FSChangeParams')


"""
    +-----------------------------------------------+
    |               Helper functions                |
    +-----------------------------------------------+
"""
def getSelectionFS():    
    selectedObj = None
    # check that something is selected
    if len(Gui.Selection.getSelection())==1:
        obj = Gui.Selection.getSelection()[0]
        if isFastener(obj):
            selectedObj = obj
        else:
            for selObj in Gui.Selection.getSelectionEx():
                obj = selObj.Object
                if isFastener(obj):
                    selectedObj = obj
    # now we should be safe
    return selectedObj


def isFastener(obj):
    if not obj:
        return False
    if (hasattr(obj,'Proxy') and isinstance(obj.Proxy, FSBaseObject)):
        return True
    return False



"""
    +-----------------------------------------------+
    |         clone per App::Link fasteners         |
    +-----------------------------------------------+
    
    Select a fastener and several datum axes and the fastener will
    be cloned (as App::Link) and attached to those axes
"""
class cloneFastenersToAxesCmd():
    
    def __init__(self):
        super(cloneFastenersToAxesCmd,self).__init__()
    
    def GetResources(self):
        return {"MenuText": translate("Fasteners", "Clone Fastener to Axes"),
                "ToolTip": translate("Fasteners", "Clone Fastener to Axes"),
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_cloneFasteners.svg')
                }
    
    def IsActive(self):
        self.selection = self.getSelectedAxes()
        if Asm4.getAssembly() and self.selection:
            return True
        return False

    def Activated(self):
        (fstnr, axes) = self.selection
        if fstnr.Document:
            for axisData in axes:
                if len(axisData) > 3: # DocName/ModelName/AppLinkName/AxisName
                    docName = axisData[0]
                    doc = App.getDocument(docName)
                    if doc:
                        model = doc.getObject(axisData[1])
                        if model:
                            objLink = model.getObject(axisData[2])
                            if objLink:
                                obj = objLink.getLinkedObject()
                                axis = obj.getObject(axisData[3])
                                if axis and axis.Document:
                                    newFstnr = Asm4.cloneObject(fstnr)
                                    Asm4.placeObjectToLCS(newFstnr, axisData[2], axis.Document.Name, axisData[3])
                                    
            Gui.Selection.clearSelection()
            self.rootAssembly = Asm4.getAssembly()
            if self.rootAssembly:
                Gui.Selection.addSelection( fstnr.Document.Name, self.rootAssembly.Name, fstnr.Name +'.')


    def getSelectedAxes(self):
        holeAxes = []
        fstnr = None
        selection = Gui.Selection.getSelectionEx('', 0)
        
        if selection:
            for s in selection:
                for seNames in s.SubElementNames:
                    seObj = s.Object
                    for se in seNames.split('.'):
                        if se and (len(se) > 0):
                            seObj = seObj.getObject(se)
                            if Asm4.isAppLink(seObj):
                                seObj = seObj.getLinkedObject()
                            if Asm4.isHoleAxis(seObj):
                                holeAxes.append(Asm4.getSelectionPath(s.Document.Name, s.ObjectName, seNames))
                                break
                            elif isFastener(seObj):
                                if fstnr is None:
                                    fstnr = seObj
                                    break
                                else:
                                    # only 1 fastener can be selected
                                    return(None)
                        else:
                            break
        # if a fastener and at least 1 HoleAxis have been selected
        if fstnr and (len(holeAxes) > 0):
            return (fstnr, holeAxes)
        else:
            return(None)




"""
    +-----------------------------------------------+
    |       add the commands to the workbench       |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_insertScrew',    insertFastener('Screw')  )
Gui.addCommand( 'Asm4_insertNut',      insertFastener('Nut')    )
Gui.addCommand( 'Asm4_insertWasher',   insertFastener('Washer') )
#Gui.addCommand( 'Asm4_insertRod',      insertFastener('ThreadedRod') )
#Gui.addCommand( 'Asm4_placeFastener',  placeFastenerCmd()       )
Gui.addCommand( 'Asm4_cloneFastenersToAxes',  cloneFastenersToAxesCmd() )
Gui.addCommand( 'Asm4_FSparameters',   changeFSparametersCmd()  )

# defines the drop-down button for Fasteners:
FastenersCmdList = [    'Asm4_insertScrew', 
                        'Asm4_insertNut', 
                        'Asm4_insertWasher', 
                        'Asm4_cloneFastenersToAxes',
                        'Asm4_FSparameters'] 
Gui.addCommand( 'Asm4_Fasteners', Asm4.dropDownCmd( FastenersCmdList, 'Fasteners'))
