#!/usr/bin/env python3
# coding: utf-8
#
# exportFiles.py
#

import os
import json
import re

from anytree import Node, RenderTree
import zipfile

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App

import Asm4_libs as Asm4

class listLinkedFiles:

    def __init__(self, show_tree=False):
        super(listLinkedFiles, self).__init__()
        self.show_tree = show_tree
        self.relative_path = True
        # if show_tree:
            # self.relative_path = True

    def GetResources(self):
        if self.show_tree:
            menutext = "List Linked Files (Tree)"
            tooltip  = "List linked files in a tree, (currently in the console)"
            iconFile = os.path.join(Asm4.iconPath, 'Asm4_List_Liked_Files_Tree.svg')
        else:
            menutext = "List Linked Files"
            tooltip  = "List linked files, (currently in the console)"
            iconFile = os.path.join(Asm4.iconPath, 'Asm4_List_Liked_Files.svg')

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
        self.UI = QtGui.QDialog()
        self.modelDoc = App.ActiveDocument
        if self.show_tree:
            print("ASM4> Listing linked files in a tree")
        else:
            print("ASM4> Listing uniq linked files")
        self.linked_files = self.list_files(self.show_tree, self.relative_path, verbose=True)

    def get_linked_files(self):
        self.linked_files = self.list_files(self.show_tree, self.relative_path, verbose=False)
        return self.linked_files

    def list_files(self, show_tree=0, relative_path=True, verbose=True):

        def find_linked_files(relative_path=True):

            def find_files(obj, root_dirpath, level=0, relative_path=True, parent_node=None, parent_filepath=None):

                if obj == None:
                    return

                filepath = obj.getLinkedObject().Document.FileName
                if relative_path:
                    filepath = os.path.relpath(filepath, root_dirpath)

                if obj.TypeId == "App::Link":

                    indexes_of_current_level = [idx for idx, s in enumerate(linked_files_level) if str(level) in str(s)]
                    linked_files_at_current_level = [linked_files[idx] for idx in indexes_of_current_level]

                    if not any(filepath in s for s in linked_files_at_current_level):

                        if filepath != parent_filepath:
                            linked_files.append(filepath)
                            linked_files_level.append(level)
                            node = Node(filepath, parent=parent_node)
                            find_files(obj.LinkedObject, root_dirpath, level+1, relative_path=relative_path, parent_node=node, parent_filepath=filepath)

                # Navigate on objects inside a folders
                if obj.TypeId == 'App::DocumentObjectGroup' or obj.TypeId == 'App::Part':
                    for objname in obj.getSubObjects():
                        subobj = obj.Document.getObject(objname[0:-1])
                        find_files(subobj, root_dirpath, level, relative_path=relative_path, parent_node=parent_node, parent_filepath=filepath)

            linked_files = []
            linked_files_level = []
            level=0

            filepath = App.ActiveDocument.FileName
            root_dirpath = os.path.dirname(filepath)
            if relative_path:
                filepath = os.path.relpath(filepath, root_dirpath)

            linked_files.append(filepath)
            linked_files_level.append(level)
            file_tree = Node(filepath)

            for obj in (App.ActiveDocument.Objects):
                find_files(obj, root_dirpath, level=level, relative_path=relative_path, parent_node=file_tree, parent_filepath=filepath)

            return linked_files, file_tree

        linked_files, file_tree = find_linked_files(relative_path=relative_path)

        linked_files = set(linked_files) # uniq files

        if verbose:
            if show_tree:
                for pre, fill, node in RenderTree(file_tree):
                    print("%s%s" % (pre, node.name))
            else:
                for i, filepath in enumerate(sorted(linked_files)):
                    print("{:3d} - {}".format(i+1, filepath))

        return linked_files


class exportFiles:

    def __init__(self):
        super(exportFiles, self).__init__()

    def GetResources(self):

        menutext = "Export Files"
        tooltip  = "Create a .zip file with files following the while hierarchy"
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
        self.UI = QtGui.QDialog()
        self.modelDoc = App.ActiveDocument
        print("ASM4> Exporting files to a .zip package")


        # Ask for a place and file name to save the exported file...
        # Open the file browser in the curretn file path
        # self.zip_filepath =

        self.linked_files = listLinkedFiles(show_tree=False).get_linked_files()
        self.export_zip_package()

    def export_zip_package(self):
        print("ASM4, Creating a zip package with linked files")

        current_path = os.getcwd()

        filename = App.ActiveDocument.Name
        relfilepath = App.ActiveDocument.FileName # GUI uses absolute path, CLI the path given byt the user

        root_dirpath = os.path.dirname(relfilepath)

        # Chdir dor not like empty path (when Freecad was opened in the same path of the FCStd file)
        if root_dirpath == "":
            root_dirpath = "./"

        os.chdir(root_dirpath)

        # Create the Zip file
        zippath = os.path.join(root_dirpath, filename + "_asm4.zip")
        zip_obj = zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED)

        # Add files to the package
        remove_zip = False
        for i, filepath in enumerate(self.linked_files):
            # filepath = os.path.relpath(filepath, root_dirpath)
            print("ASM4> [ZIP] {}, adding file {}".format(i+1, filepath))
            absfilepath = os.path.join(root_dirpath, filepath)
            arcname = os.path.basename(filepath)
            try:
                zip_obj.write(filepath, filepath)
            except:
                print("ASM4> [ZIP] Error: Cannot create the zip package")
                remove_zip = True
                break

        zip_obj.close()

        if remove_zip:
            os.remove(zippath)
            print("ASM4> Zip could not be created.")
        else:
            print("ASM4> Zip package {} was created.".format(zippath))

        # Revert current path
        os.chdir(current_path)

# Add the command in the workbench
Gui.addCommand('Asm4_listLinkedFilesTree', listLinkedFiles(show_tree=True))
Gui.addCommand('Asm4_listLinkedFiles', listLinkedFiles(show_tree=False))
Gui.addCommand('Asm4_exportFiles', exportFiles())
