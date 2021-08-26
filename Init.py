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

import Asm4_locator
Asm4_path = os.path.dirname( Asm4_locator.__file__ )
# Assembly4 version info
versionPath = os.path.join( Asm4_path, 'VERSION' )
versionFile = open(versionPath,"r")
# read second line
version = versionFile.readlines()[1]
versionFile.close()
# remove trailing newline
Asm4_version = version[:-1]

print("Assembly4 workbench ("+Asm4_version+") loaded")
