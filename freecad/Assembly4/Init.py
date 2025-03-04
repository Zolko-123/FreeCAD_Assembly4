# -*- coding: utf-8 -*-
###################################################################################
#
#  Init.py
#  
#  Copyright 2018 Mark Ganson <TheMarkster>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
###################################################################################

import FreeCAD

from . import Asm4_locator

Asm4_path = os.path.join(os.path.dirname(Asm4_locator.__file__))
# Assembly4 version info
# with file package.xml
packageFile  = os.path.join(Asm4_path, '..', '..', 'package.xml')
try:
    metadata     = FreeCAD.Metadata(packageFile)
    Asm4_date    = metadata.Date
    Asm4_version = metadata.Version
# with file VERSION
except:
    versionPath = os.path.join(Asm4_path, '..', '..', 'VERSION')
    versionFile = open(versionPath,"r")
    # read second line
    version = versionFile.readlines()[1]
    versionFile.close()
    # remove trailing newline
    Asm4_version = version[:-1]

# check for FreeCAD version
FCver = FreeCAD.Version()
if FCver[0]=='0' and FCver[1]=='22':
    git = int(FCver[3][0:5])
    if isinstance(git, int) and git>35594 :
        pass
        # print("This version of FreeCAD ("+FCver[0]+"."+FCver[1]+"-"+str(git)+") is not compatible with Assembly4, you may encounter erors")


# print("Assembly4 workbench ("+Asm4_version+") loaded")
