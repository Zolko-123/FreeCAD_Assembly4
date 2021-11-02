#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# libAsm4.py
# has been replaced by Asm4_libs, kept here for compatibility

import os

class setCustomIcon():
    def __init__( self, obj, iconFile):
        self.customIcon = os.path.join( iconPath, iconFile )
        
    def getIcon(self):
        return self.customIcon






