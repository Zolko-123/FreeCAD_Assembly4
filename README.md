# FreeCAD Assembly 4 workbench

Current version 0.11.5



## Overview

This assembly workbench allows to assemble into a single Part container under a single coordinate system other FreeCAD objects using Links, and place them relative to the assembly and to each-other. The parts in the assembly can invariably be in the same document as the assembly or in an external document. When parts are modified in their original document, they are instantly updated in the assembly.

As an Assembly4 _Assembly_ is a standard FreeCAD `App::Part` container, it can be used and manipulated with any FreeCAD tool handling `App::Part` objects. In particular, it can be inserted into another _Assembly_ to create nested assemblies. It can also contain solids and datum objects. An _Assembly_ can be an assembly, a sub-assembly or a stand-alone part, and any combinations of these; a document can contain only 1 _Assembly_.

Parts and linked parts are placed to each-other in the host parent assembly by matching their Datum Coordinate Systems (called LCS for Local Coordinate System) using the built-in FreeCAD *ExpressionEngine.* No geometry is used to place and constrain parts relative to each other, thus avoiding a lot of the topological naming problems. 


![](Resources/media/Asm4_wb1.png)

**Please Note:** only _Part_ and _Body_ containers at the root of a document can be inserted. Objects nested inside containers cannot be used directly by Assembly4. 

**Please Note:** objects in the same document as the linked part but outside the `App::Part` container will **not** be inserted.

**Please Note:** objects need to be opened in the current session in order to be inserted into an assembly.



## Installation

[![FreeCAD Addon manager status](https://img.shields.io/badge/FreeCAD%20addon%20manager-available-brightgreen)](https://github.com/FreeCAD/FreeCAD-addons)

### Addon Manager (recommended)

Assembly 4 is available through the FreeCAD Addon Manager (menu **Tools > Addon Manager**). It is called _Assembly4_ in the Addon Repository.  

**Important Note:** Assembly 4 needs FreeCAD v0.19 or above. Assembly4 is **not** compatible with FreeCAD v0.18 and before. 

### Manual Installation

It is possible to install this workbench manually into FreeCAD's local workbench directory. This can be useful for testing local modifications to the workbench, or to remove an old stale version of the workbench. 

In this case, download the Github [FreeCAD_Assembly4-master.zip](https://github.com/Zolko-123/FreeCAD_Assembly4/archive/master.zip) archive from [github.com/Zolko-123/FreeCAD_Assembly4](https://github.com/Zolko-123/FreeCAD_Assembly4) to a temporary directory, and extract the Zip archive. Then, remove any existing Assembly4 directory from FreeCAD's local workbench directory, and copy the folder *FreeCAD_Assembly4-master* into the directory containing all FreeCAD addon modules :

* for Windows: `C:\Users\******\AppData\Roaming\FreeCAD\Mod`
* for Linux: `~/.FreeCAD/Mod` 
* for MacOS: `~/Library/Preferences/FreeCAD/Mod/`



## Getting Started

You can get more information in the [user instructions](INSTRUCTIONS.md), the [technical manual](TECHMANUAL.md), and you can use the provided [example assemblies](https://github.com/Zolko-123/FreeCAD_Examples) to experiment with this workbench's features. There are also online tutorials :

* [a quick assembly from scratch](https://github.com/Zolko-123/FreeCAD_Examples/blob/master/Asm4_Tutorial1/README.md)
* [a cinematic assembly in one file, using a master sketch](https://github.com/Zolko-123/FreeCAD_Examples/blob/master/Asm4_Tutorial2/README.md)
* [a Lego assembly](https://github.com/Zolko-123/FreeCAD_Examples/blob/master/Asm4_Tutorial3/README.md)
* [Some examples to play with](https://github.com/Zolko-123/FreeCAD_Examples)







## Release notes

* 2021.11.3 (**0.11.5**) :  
added AttachmentEngine (MapMode) to all created Parts, Bodies and Fasteners  
Small fixes  

* 2021.10.18 (**0.11.4**) :  
translations in placements of parts respect user preferences units  
small tweaks  

* 2021.10.09 (**0.11.3**) :  
Merged all placement of parts (links, fasteners, anything with a "Placement" into a single command, which launches the corresponding task UI  
Created the "Constraints" menu and moved the placement command there (in preparation of the merge of the A2+ solver)  

* 2021.10.08 (**0.11.2**) :  
added "Open File" to insertLink  
BOM and infoPart improvements  

* 2021.10.01 (**0.11.1**) :  
reverted Asm4.QUnitSpinBox() to QtGui.QDoubleSpinBox() because of incompatibilites with some locale (',' comma decimal separators)  

* 2021.10.01 (**0.11.0**) :  
first version of variantLink: EXPERIMENTAL, use with caution  
multiple datum imports (thanx abetis)  
improved BoM and PartInfo (thax FarmingSoul)  
added supprot for user preferences in distance units (thanx xoviat)  

* 2021.09.19 (**0.10.7**) :  
fixed some minor bugs  
improved BOM and PartInfo  
new version string (removed date)  
initial variantLink object  

* 2021.09.07 (**0.10.6**) :  
corrected placeLink selection mechanism: now, the user can select LCS in either the model tree, the 3D window or the task panel lists  

* 2021.09.05 (**0.10.5**) :  
reverted placeLink to 0.10.3 version (bug in the selections)  

* 2021.09.01 (**0.10.4**) :  
added wrapper for SubShapeBinder  

* 2021.08.30 (**0.10.3**) :  
Returned to the part placement preview in *placeLink*  
Some small fixes  

* 2021.08.29 (**0.10.2**) :  
Fix placeFasteners  

* 2021.08.26 (**0.10.1**) :  
Fix in selection in placeLink: this fixes a freeze in the UI, but direct selection in the tree is not possible anymore  
Added spiral offset for circular array  

* 2021.08.23 (**0.10.00**) :  
Translation i18  
Circular array  
Changed libAsm4 as to Asm4_libs (the Variables objects will lose their tree-view icon)  
Added Asm4_objects  

* 2021.06.24 (**0.9.17**) :  
Minor bugfixes in _AnimationLib_ and _placeLink_  
Introduced the next assembly property _SolverId_ (which will replace _AssemblyType_) with value _Asm4::ExpressionEngine_. _placeLink_ checks the new and old properties for forward compatibility  
__This should be the final version of the 0.9 series__

* 2021.05.03 (**0.9.16**) :  
Various fixes  
Animation Export  

* 2021.03.10 (**0.9.15**) :  
added mirroring of a part  

* 2021.03.07 (**0.9.14**) :  
HoleAxis can now create datums on all selected circles from 1 single part in 1 step   
Added a selection filter in the main Assembly4 toolbar  
Made the measurement tool compatible with the selection filter  
Changed insertLink and placeLink such that any App::Part can serve as parent assembly but it is inaccessible from the UI for now (might bring more trouble than benefit)  

* 2020.12.01 (**0.9.13**) :  
improved LCS selection  
placeFasteners update  

* 2020.11.20 (**0.9.12**) :  
placeFasteners update  
parent combo-box width corrected  

* 2020.11.14 (**0.9.11**) :  
Added Offset translation adjustment in the placeLink dialog  
Added Configuration Engine  
Measurements obey the preferences settings  
Some code clean-up (hopefully won't break anything, if it does please report)  
**Big thanx for the help, this is really appreciated**  

* 2020.11.01 (**0.9.10**) :  
Bugfixe in placement of Fastener on "Hole Axis"  
small usability improvements  

* 2020.09.24 (**0.9.9**) :  
Small bugfixes and usability improvements  

* 2020.09.02 (**0.9.8**) :  
Small usability improvements  

* 2020.06.29 (**0.9.7**) :  
Native Fasteners, included Task to change parameters  

* 2020.06.23 (**0.9.6**) :  
Improved Measure tool  

* 2020.06.19 (**0.9.5**) :  
Added new Measure tool  
Added preliminary BoM, PartList and PartInfo functions  
Minor bugfixes and improvements  

* 2020.05.25 (**0.9.4**) :  
Minor update for Fasteners (simplified format, should be backwards compatible)  

* 2020.05.18 (**0.9.3**) :  
Bugfixe: create Body/Part didn't place them in the selected App::Part container  

* 2020.05.08 (**0.9.2**) :  
The UI windows are now in the Task Panel.  

* 2020.05.03 (**0.9.1**) :  
Bugfixes  

* 2020.04.15 (**0.9.0**) :  
PartDesign::Body can be directly imported (linked), no need to wrap them in App::Part container  

* 2020.03.15 (**version 0.8.1**) :  
Added slider for animation  
Reversed Document#Label (Name) to Document#Name (Label)  

* 2020.02.13 (**version 0.8.0**) :  
All dialogs are now resizable  
Various bugfixes  
Made the Asm4 properties of all objects homogeneous  
Moved examples and tutorials to dedicated repository (some users ran into trouble for updating the WB because they had modified the local files)  

* 2020.01.25 (**version 0.7.12**) :  
Refined datum and variables creation  

* 2020.01.22 (**version 0.7.11**) :  
Added version info to the Help dialog  

* 2020.01.21 (**version 0.7.10**) :  
bug-fix to not fall for random criss-cross linking of objects  

* 2020.01.20 (**version 0.7.9**) :  
(silly) bug-fix  

* 2020.01.18 (**version 0.7.8**) :  
added "release attachments" button  
various small fixes

* 2020.01.06 (**version 0.7.7**) :  
Moved the tutorials to the Resources directory  
import libAsm4 as Asm4  
Added a Help command (dummy placeholder)  
Ported example2 to the latest Asm4 format

* 2019.12.12 (**version 0.7.6**) :  
Improved animation and datum import.

* 2019.12.02 (**version 0.7.5**) :  
Minor (but useful !) refinements for variables and animation.

* 2019.11.24 (**version 0.7.4**) :  
Added Animation command

* 2019.11.19 (**version 0.7.3**) :  
Added linkArray, a wrapper for Draft::LinkArray  
Fixes for the Fasteners command

* 2019.11.14 (**version 0.7.2**) :  
Bug-fix for importDatum  

* 2019.11.11 (**version 0.7.1**) :  
Bug-fix  

* 2019.11.05 (**version 0.7.0**) :  
Support for screws & nuts from the Fasteners workbench  
Added Variables to the Model  
The model file format has changed, former assembly models can be opened but must be re-assembled.

* 2019.10.11 (**version 0.6.4**) :  
Improved assembly in single file  
Various small fixes

* 2019.10.11 (**version 0.6.3**) :  
It is now possible to link parts from the same document as the assembly itself, allowing to make 1-file assemblies and still use all the other tools.

* 2019.10.11 (**version 0.6.2**) :  
Added page for Tutorial 1.  
Fine-tuned some functions  
Renamed icons in a consistent way  

* 2019.10.07 (**version 0.6.1**) :  
Moved the code that was in Mod_Asm4 to the root, to be compatible with the FreeCAD AddonManager

* 2019.10.05 (**version 0.6**) :  
Ported to FreeCAD-v0.19-pre, with new syntax for the ExpressionEngine

* 2019.07.23 (**version 0.5.5**) :  
Fixed a bug in partLCSlist.findItems  
New Datum Point in the Model

* 2019.07.18 (**version 0.5.4**) :  
A cosmetic update to fix a 25 year old Windows bug:  
some UTF-8 characters in the comments were not accepted on some Windows 10 machines

* 2019.06.15 (**version 0.5.3**) :  
Now the LCS can be renamed, and they show up in the LCS list in the command placeLink as such.  
It's only visual, the ExpressionEngine still uses the LCS.Name though

* 2019.05.07 (**version 0.5.2**) :  
added insertDatumCmd

* 2019.03.18 (**version 0.5.1**) :  
Part can now be linked without being placed: this is then a raw interface with App::Link  
The instance can be moved manually with the 'Transform' dragger

* 2019.03.12 (**version 0.5**) :  
moved the actual code to Mod_Asm4

* 2019.03.11 (**version 0.4.1**) :  
Added placement of Datum Point

* 2019.03.09 (**version 0.4**) :  
FreeCAD now imports as App  
insert_Link launches place_Link

* 2019.03.05 (**version 0.3.1**) :  
added the RotX-Y-Z buttons

* 2019.02.20 (**version 0.3**)  
mostly working version

* 2019.02.18 (**version 0.1**) :  
initial release of Assembly 4 WB



## Discussion
Please offer feedback or connect with the developers in the [dedicated FreeCAD forum thread](https://forum.freecadweb.org/viewtopic.php?f=20&t=34806).



## Addon Repository
This addon is hosted on a [GitHub repository](https://github.com/Zolko-123/FreeCAD_Assembly4). 



## License

LGPLv2.1 (see [LICENSE](LICENSE))
