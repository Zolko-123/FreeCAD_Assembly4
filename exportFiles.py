#!/usr/bin/env python3
# coding: utf-8
#
# exportFiles.py
#

import os, json, re, zipfile


from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
from FreeCAD import Console as FCC

import Asm4_libs as Asm4


has_anytree = False
try:
    from anytree import Node, RenderTree
    has_anytree = True
except ImportError:
    FCC.PrintWarning("\nASM4 WARNING: Pylib anytree is missing, exportFiles is not available\n")


class listLinkedFiles:

    def __init__(self, show_tree=False, relative_path=True):
        super(listLinkedFiles, self).__init__()
        self.show_tree = show_tree
        self.relative_path = relative_path
        # self.relative_path = True
        # if show_tree:
            # self.relative_path = True

    def GetResources(self):
        if self.show_tree:
            menutext = "Tree of Linked Files"
            tooltip = """
                Show the tree of linked files.
                Currently is displyed in the Report View.
            """
            iconFile = os.path.join(Asm4.iconPath, 'Asm4_List_Liked_Files_Tree.svg')
        else:
            menutext = "List of Linked Files"
            tooltip = """
                List unique linked files.
                Currently it displyed in the Report View.
            """
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

        if not has_anytree:
            FCC.PrintWarning("To use {} you must install pylib \"anytree\"\n".format(self.__class__.__name__))
            return

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

                if obj.TypeId == "App::Link":

                    filepath = obj.LinkedObject.Document.FileName #obj.getLinkedObject().Document.FileName
                    if relative_path:
                        filepath = os.path.relpath(filepath, root_dirpath)

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
                        find_files(subobj, root_dirpath, level, relative_path=relative_path, parent_node=parent_node, parent_filepath=parent_filepath)

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
            print("ASM4> Listing ended")

        return linked_files


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

# Add the command in the workbench
Gui.addCommand('Asm4_listLinkedFilesTree', listLinkedFiles(show_tree=True))
Gui.addCommand('Asm4_listLinkedFiles', listLinkedFiles(show_tree=False))
Gui.addCommand('Asm4_exportFiles', exportFiles())

# defines the drop-down button for Fasteners:
ExportCmdList = ['Asm4_listLinkedFilesTree',
                 'Asm4_listLinkedFiles',
                 'Asm4_exportFiles']
Gui.addCommand('Asm4_ExportList', Asm4.dropDownCmd(ExportCmdList, 'Export Files'))
