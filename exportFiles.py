#!/usr/bin/env python3
# coding: utf-8
#
# exportFiles.py
#
#####################################
# Copyright (c) openBrain 2020
# Licensed under LGPL v2
#
# This FreeCAD macro prints the Tree of selected object(s) as ASCII art.
# Several styles are available. Tree branch pattern is customizable.
# It can export to clipboard, file or embedded text document.
# This mainly aims at documenting the model.
#
# Version history :
# **** : brought into exportFiles for Assembly4
# *0.6 : introduce last fork string definition, add new style
# *0.5 : beta release
#
#####################################


import os, json, re, zipfile


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4

'''
has_anytree = False
try:
    from anytree import Node, RenderTree
    has_anytree = True
except ImportError:
    FCC.PrintMessage("\nINFO : Pylib anytree is missing, exportFiles is not available\n")
'''

# lists the parts and linked parts of the selected container
class listLinkedFiles():

    def GetResources(self):
        menutext = "Structure tree of the assembly"
        tooltip  = "<p>Show the hierarchical tree structure of parts and sub-assemblies in the assembly. "
        tooltip += "The tree is displayed with ASCII art</p>"
        tooltip += "<p><b>Usage</b>: select an entity and click the command</p>"
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_List_Liked_Files_Tree.svg')
        return {
            "MenuText": menutext,
            "ToolTip" : tooltip,
            "Pixmap"  : iconFile
        }


    def IsActive(self):
        if App.ActiveDocument and len(Gui.Selection.getSelection())==1:
            return True
        elif App.ActiveDocument and Asm4.getAssembly():
            return True
        else:
            return False


    def __init__(self):
        super(listLinkedFiles, self).__init__()
        # types of objects to be included in the listing
        # links and derivatives are also included
        self.DEF_TYPES = ['App::Part', 'PartDesign::Body', 'Part::FeaturePython', 'App::DocumentObjectGroup']
        # visual ASCII art
        self.TAB    = '    '
        self.BRANCH = ' │  '
        self.FORK   = ' ├─ '
        self.LAST   = ' └─ '
        # where we write stuff
        self.ascii_tree = ""
        self.root_path  = ""
        # the UI
        self.UI = QtGui.QDialog()
        self.drawUI()


    def Activated(self):
        # clear stuff
        self.ascii_tree = ""
        self.root_path  = ""
        self.tree_view.clear()
        #
        if len(Gui.Selection.getSelection())==1:
            objects = Gui.Selection.getSelection()
        elif Asm4.getAssembly():
            objects = [ Asm4.getAssembly() ]
        else:
            FCC.PrintWarning("Oups, you shouldn't see this message, something went wrong")
        # get the directory path of the selected object
        filename = objects[0].Document.Name
        self.root_path = objects[0].Document.FileName.partition(filename)[0]
        # FCC.PrintMessage("rel_path = "+self.root_path+"\n")
        # now build the tree
        self.printChildren(objects)
        self.UI.show()
        self.tree_view.setPlainText(self.ascii_tree)


    # this is where the magic happens. Copied from TreeToAscii macro
    # Build ASCII tree by recursive call
    def printChildren(self, objs=None, level=0, baseline=''):
        for cnt, obj in enumerate(objs,1):
            # find the filepath
            filepath = ''
            if obj.isDerivedFrom('App::Link'):
                target = obj.LinkedObject
            else:
                target = obj
            # try relative filepath ...
            if self.root_path:
                filepath = target.Document.FileName.partition(self.root_path)[2]
            # ... else absolute
            if filepath =='':
                filepath = target.Document.FileName
            # make the data
            data = {
                "LBL"  : obj.Label,
                "NAME" : '('+obj.Name+')' if obj.Label!=obj.Name else '',
                "DOC"  : filepath,
                "TARG" : obj.LinkedObject.Name if obj.isDerivedFrom('App::Link') else ''
            }
            # print the line
            if cnt == len(objs):
                if level>0:
                    self.ascii_tree += baseline + self.LAST
            else:
                self.ascii_tree += baseline + self.FORK
            # new data print
            if obj.isDerivedFrom('App::Link'):
                pattern = '{LBL} => {TARG} @ {DOC}'
            else:
                pattern = '{LBL} {NAME}'
            self.ascii_tree += pattern.format(**data)
            # we add the filename for the first element
            if level==0 and target.Document.FileName != '' :
                self.ascii_tree += ' @ '+target.Document.FileName
            self.ascii_tree += '\n'
            # for the next line
            if cnt == len(objs):
                if level>0:
                    baselinenext = baseline + self.TAB
                else:
                    baselinenext = ''
            else:
                baselinenext = baseline + self.BRANCH
            # table of children to be listed next
            children = []
            for child in obj.ViewObject.claimChildren():
                if child.TypeId in self.DEF_TYPES or child.isDerivedFrom('App::Link'):
                    children.append(child)
            self.printChildren(children, level + 1, baselinenext)


    def copyToClip(self):
        """Copies ASCII tree to clipboard"""
        self.tree_view.selectAll()
        self.tree_view.copy()
        self.tree_view.setPlainText("Copied to clipboard")
        QtCore.QTimer.singleShot(3000, lambda:self.tree_view.setPlainText(self.ascii_tree))


    # defines the UI, only static elements
    def drawUI(self):
        # Our main window will be a QDialog
        # make this dialog stay above the others, always visible
        self.UI.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint )
        self.UI.setWindowTitle('Tree structure of the selected object')
        self.UI.setWindowIcon( QtGui.QIcon( os.path.join( Asm4.iconPath , 'FreeCad.svg' ) ) )
        self.UI.setMinimumWidth(470)
        self.UI.resize(470,300)
        self.UI.setModal(False)
        # the layout for the main window is vertical (top to down)
        mainLayout = QtGui.QVBoxLayout(self.UI)
        # from TreeToAscii macro
        self.tree_view = QtGui.QPlainTextEdit(self.ascii_tree)
        self.tree_view.setReadOnly(True)
        self.tree_view.setMinimumWidth(Gui.getMainWindow().width()/2)
        self.tree_view.setMinimumHeight(Gui.getMainWindow().height()/2)
        self.tree_view.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        f = QtGui.QFont("unexistent");
        f.setStyleHint(QtGui.QFont.Monospace);
        self.tree_view.setFont(f);
        button_box = QtGui.QDialogButtonBox()
        copy_clip_but = QtGui.QPushButton("Copy to clipboard", button_box)
        button_box.addButton(copy_clip_but, QtGui.QDialogButtonBox.ActionRole)
        #button_box.addStretch()
        close_dlg_but = QtGui.QPushButton("Close", button_box)
        button_box.addButton(close_dlg_but, QtGui.QDialogButtonBox.RejectRole)
        #button_box.addButton(QtGui.QDialogButtonBox.Close)
        #button_box.button(QtGui.QDialogButtonBox.Close).setDefault(True)
        mainLayout.addWidget(self.tree_view)
        mainLayout.addWidget(button_box)
        # actions
        copy_clip_but.clicked.connect(self.copyToClip)
        button_box.rejected.connect(self.UI.reject)


'''
class exportFiles:

    def __init__(self):
        super(exportFiles, self).__init__()

    def GetResources(self):

        menutext = "Export Linked Files"
        tooltip = """
            Creates a .zip file with linked files.
        """
        iconFile = os.path.join(Asm4.iconPath, 'Asm4_Export_PartsList.svg')

        return {
            "MenuText": menutext,
            "ToolTip": tooltip,
            "Pixmap": iconFile
        }

    def IsActive(self):
        if Asm4.getAssembly() is None:
            return False
        else:
            return True

    def Activated(self):

        if not has_anytree:
            FCC.PrintWarning("To use {} you must install pylib \"anytree\"\n".format(self.__class__.__name__))
            return

        self.UI = QtGui.QDialog()
        self.modelDoc = App.ActiveDocument
        print("ASM4> Exporting files to a .zip package")

        filename = App.ActiveDocument.Name
        relfilepath = App.ActiveDocument.FileName # GUI uses absolute path, CLI the path given byt the user
        doc_root_dirpath = os.path.dirname(relfilepath)
        suggested_zip_file = os.path.join(doc_root_dirpath, filename + "_asm4.zip")
        self.zip_filepath = QtGui.QFileDialog.getSaveFileName(None, "Export Linked Files (as .zip)", suggested_zip_file, "All files (*)", "")[0]
        if self.zip_filepath == "":
            return

        self.linked_files = listLinkedFiles(show_tree=False, relative_path=False).get_linked_files()
        self.export_zip_package()

    def export_zip_package(self):
        print("ASM4, Creating a zip package with linked files")

        current_path = os.getcwd()

        filename = App.ActiveDocument.Name
        relfilepath = App.ActiveDocument.FileName # GUI uses absolute path, CLI the path given byt the user
        doc_root_dirpath = os.path.dirname(relfilepath)

        common_path = os.path.commonpath(self.linked_files)
        print("ASM4> Common path: \"{}\"".format(common_path))
        root_dirpath = common_path

        # Chdir does not like empty path (when Freecad was opened in the same path of the FCStd file)
        if root_dirpath == "":
            root_dirpath = "./"

        os.chdir(root_dirpath)

        # Create the Zip file
        # TODO: Check if this doc_root_dirpath is always right
        zip_obj = zipfile.ZipFile(self.zip_filepath, 'w', zipfile.ZIP_DEFLATED)
        zip_obj.create_system = 3 # symlink support

        # Add files to the package
        remove_zip = False
        for i, filepath in enumerate(self.linked_files):
            relfilepath = os.path.relpath(filepath, root_dirpath)
            print("ASM4> [ZIP] {}, adding file {}".format(i+1, relfilepath))
            try:
                zip_obj.write(filepath, relfilepath)
            except:
                print("ASM4> Error: Cannot create the zip package")
                remove_zip = True
                break

            if os.path.splitext(os.path.basename(filepath))[0] == filename:
                assembly_symlink_path = filename + ".FCStd"
                if not os.path.isfile(assembly_symlink_path):
                    relfilepath = os.path.relpath(filepath, root_dirpath)
                    print("ASM4> [ZIP] {}, creating symlink {} to {}".format("_", assembly_symlink_path, relfilepath))
                    os.symlink(relfilepath, assembly_symlink_path)
                    print("ASM4> [ZIP] {}, adding symlink {}".format("_", assembly_symlink_path))
                    zip_info = zipfile.ZipInfo(assembly_symlink_path)
                    zip_info.external_attr |= 0xA0000000
                    zip_obj.writestr(zip_info, os.readlink(assembly_symlink_path))
                    os.remove(assembly_symlink_path) # remove symlink created

        zip_obj.close()

        if remove_zip:
            os.remove(self.zip_filepath)
            print("ASM4> Zip could not be created.")
        else:
            print("ASM4> Zip package {} was created.".format(self.zip_filepath))

        # Revert current path
        os.chdir(current_path)
'''

# Add the command in the workbench
Gui.addCommand('Asm4_listLinkedFiles', listLinkedFiles())

