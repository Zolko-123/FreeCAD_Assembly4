#!/usr/bin/env python3
# coding: utf-8
# 
# updateAssembly.py 


import math, re, os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import libAsm4 as Asm4



class updateAssembly:

    def GetResources(self):
        return {"MenuText": "Solve and Update Assembly",
                "ToolTip": "Update Assembly",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_Solver.svg')
                }


    def IsActive(self):
        if App.ActiveDocument:
            return(True)
        return(False)


    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # find every Part in the document ...
        for obj in App.ActiveDocument.Objects:
            # ... and update it
            if obj.TypeId == 'App::Part':
                obj.recompute('True')
        #App.ActiveDocument.recompute()
        import time
        import numpy as np
        from solver.Solver import Solver
        from solver.Solver import get_lists
        t = time.time()
        f, x, x_names = get_lists()
        x_i = np.zeros_like(x)
        for i in range(len(x)):
            x_i[i] = x[i].real
        sol = Solver(x,f)
        solved = sol.solve(x_i)
        for i in range(len(x)):
            obj = x_names[i]
            if "Rotation" in obj:
                angles = App.ActiveDocument.getObject(obj.split(".")[0]).Placement.Rotation.toEuler()
                if "x" in obj.split(".")[3]:
                    App.ActiveDocument.getObject(obj.split(".")[0]).Placement.Rotation = App.Rotation(angles[0], angles[1], solved.x[i])
                elif "y" in obj.split(".")[3]:
                    App.ActiveDocument.getObject(obj.split(".")[0]).Placement.Rotation = App.Rotation(angles[0], solved.x[i], angles[2])
                elif "z" in obj.split(".")[3]:
                    App.ActiveDocument.getObject(obj.split(".")[0]).Placement.Rotation = App.Rotation(solved.x[i], angles[1], angles[2])
            else:
                rsetattr(App.ActiveDocument, obj, solved.x[i])
        print(solved)
        App.ActiveDocument.recompute()
        time_used = time.time() - t
        print(f"solver took {time_used}")


from solver.Solver import rgetattr
def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition(".")
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


# add the command to the workbench
Gui.addCommand( 'Asm4_updateAssembly', updateAssembly() )
