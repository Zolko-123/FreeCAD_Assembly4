# FreeCAD Assembly4 Workbench

## Release notes

* 2024.06.07 (**0.50.14**) :  
Adapted to work with FreeCAD development version v0.22 … hopefully  
Introduced a nice new FreeCAD logo  

* 2024.06.07 (**0.50.13**) :  
Corrected command name for Fasteners change parameters  
Updated version check  

* 2024.03.19 (**0.50.12**) :  
Re-added warning for incompatible FreeCAD version  
Updated ReadMe  

* 2024.03.19 (**0.50.11**) :  
Fixed a silly ? left over  
Removed version check (needs more testing)  

* 2024.03.19 (**0.50.10**) :  
Added warning for incompatible FreeCAD development version  

* 2024.03.08 (**0.50.9**) :  
fixed some translation code errors  

* 2024.03.06 (**0.50.8**) :  
Improved error handling for OpenCV library in animations  
Translations  
Minor fixes  

* 2024.01.31 (**0.50.7**) :  
Merged BoM and PartInfo code from JonasThomas (still doesn't seem to work !)  
Simplyfied globalPlacement for LCS in Asm4_Measure  
Removed "Donate" button (recieved 55€ altogether, a BIG thank-you to all the donors, but it's not worth the trouble)  
Show Origin planes for PartDesign Bodies, with colors  

* 2023.12.05 (**0.50.6**) :  
Fixed measurements with LCS  

* 2023.12.05 (**0.50.5**) :  
Removed annoying warning in checkInterference  
Cleanup in Asm4_libs  

* 2023.10.02 (**0.50.4**) :  
Inversed variable name check for units  

* 2023.10.01 (**0.50.3**) :  
Initial interference check (thanx to leoheck)  
Put show/hide LCS back in the toolbar  
Various small fixes  

* 2023.05.07 (**0.50.2**) :  
Finally managed to read version info from package.xml  
Fixed deleteVariable greyed-out  
Custon ViewProvider for variantLink  

* 2023.04.16 (**0.50.1**) :  
Fixed some QLayout warnings with latest FreeCAD builds  

* 2023.04.15 (**0.50.0**) :  
Jumped version to 0.50 meaning we're half-way there  
Switched back to the assembly being called "Assembly"  
Removed dependency in exportFiles  
Creating fasteners when a datum object is selected places the fastener onto that datum  
Mirror part improvement  
Clean-up of Assembly and Variables creation  

* 2023.04.03 (**0.12.7**) :  
Added PayPal Donate button  
Added copyright notice  
Changed exportFiles warning to plain message  

* 2023.02.26 (**0.12.6**) :  
Small fixes here and there  
BOM and PartInfo are now partially working again  

* 2022.12.15 (**0.12.5**) :  
Added ExpressionArray, and circular and linear-arrays based on it (thanx Jolbas)  
BOM and PartInfo are (still) broken  
Fixed Issue #382 (number of decimals in variables)  

* 2022.09.08 (**0.12.4**) :  
Moved the Changelog into a separate file  
Fixed an error with new version of fasteners WB  

* 2022.07.19 (**0.12.3**) :  
Changed the menu entry for insertLink to Import Part  
Small fixes  

* 2022.07.04 (**0.12.2**) :  
Fixed a bug in Asm4.checkModel() for retro-compatibility  

* 2022.06.29 (**0.12.1**) :  
Fixed a bug in AnimationLib  

* 2022.06.11 (**0.12.0**) :  
Reverted to name "Model"  

* 2022.04.25 (**0.11.12**) :  
Removed Groups from containerTypes in Asm4_libs  

* 2022.04.20 (**0.11.11**) :  
Small fixes and improvements  

* 2022.02.20 (**0.11.10**) :  
Improved configurationEngine for compatibility  
Preselect the sole LCS if there is only 1  

* 2022.02.15 (**0.11.9**) :  
Bugfix of the configurationEngine  
Bugfix for parts corrupted by v0.11.5 : print a warning, part cannot be fixed automatically  

* 2022.02.03 (**0.11.8**) :  
added possibility to use parts (links) in groups inside the assembly. Works also for fasteners  

* 2022.01.27 (**0.11.7**) :  
bugfix: corrected default name when duplicating an existing link  
introduced package.xml  

* 2022.01.10 (**0.11.6**) :  
bugfix: removed AttachmentEngine (MapMode) to all created Parts, Bodies and Fasteners, because that creates an AttachmentOffset that conflicts with the placement by Asm4  

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
added support for user preferences in distance units (thanx xoviat)  

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
