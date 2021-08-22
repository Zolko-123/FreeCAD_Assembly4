#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# libAsm4.py
# has been replaced by Asm4_libs, kept here for compatibility



"""
    +-----------------------------------------------+
    |                  Custom icon                  |
    |      Here only for compatibility reasons      |
    +-----------------------------------------------+
"""

# https://wiki.freecadweb.org/Viewprovider
# https://wiki.freecadweb.org/Custom_icon_in_tree_view
# 
# usage:
# object = App.ActiveDocument.addObject('App::FeaturePython','objName')
# object = model.newObject('App::FeaturePython','objName')
# object.ViewObject.Proxy = Asm4.setCustomIcon(object,'Asm4_Variables.svg')
class setCustomIcon():
    def __init__( self, obj, iconFile):
        #obj.Proxy = self
        self.customIcon = os.path.join( iconPath, iconFile )
        
    def getIcon(self):                                              # GetIcon
        return self.customIcon






