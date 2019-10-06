# FreeCAD Assembly Without Solver / Assembly 4
FreeCAD add-on for a bare-bone assembly structure, using App::Link  

Welcome to the FreeCAD_aws wiki! This page tries to explain how to make assemblies using these tools. This project the result of [discussions on the FreeCAD forum](https://forum.freecadweb.org/viewtopic.php?f=20&t=32843).

## Prerequisites

**Important Note:** Assembly 4 is **not** compatible with FreeCAD v0.18
- [x] FreeCAD >= `v0.19.18353`

## Installation

### Automatic Installation (recommended)

Assembly 4 is available through the [FreeCAD Addon Manager](https://github.com/FreeCAD/FreeCAD-addons/#1-builtin-addon-manager).
It is called 'A4' in the Addon Repository.    

**Note:** Restarting FreeCAD is required after installing this Addon.

### Manual Installation

```bash
  cd ~/.FreeCAD/Mod  
  git clone https://github.com/Zolko-123/FreeCAD_Assembly4
```
To update the Addon:  

```bash
  cd ~/.FreeCAD/Mod/FreeCAD_Assembly4/
  git fetch
```

**Note:**
Another method is to download and extract the Github .zip archive. Then move (or link) the sub-directory `Mod_Asm4` (which contains all the actual code) into the `~/.FreeCDA/Mod` folder, containing all additional modules.

**Important Note:** Restarting FreeCAD is required after installing this Addon.

## Getting Started

You can use the [example assemblies](https://github.com/Zolko-123/FreeCAD_Assembly4/tree/master/Examples) to experiment with this workbench's features. Open one _asm_something.fcstd_ file and try out the functions. There are `ReadMe.txt` files in each directory with some explanations.


## Principle

The point is that each part is a mostly standard FreeCAD `App::Part` object, and these are assembled using the `App::Link` framework found in the fork of FreeCAD (https://github.com/realthunder/FreeCAD/tree/LinkStage3, pre-built binaries on the [realthunder's FreeCAD_assembly3 release page](https://github.com/realthunder/FreeCAD_assembly3/releases)

The particularities of the `App::Part` used here are the following:

* they are called 'Model' at creation time  
* they contain a group called 'Constraints' at the root  
* they contain a Datum Coordinate System called LCS_0 at the root  

The purpose of this is to avoid burdensome error checking: it is supposed that no other usecase would create an `App::Part` called 'Model', _i.e._ that if an `App::Part` is called 'Model' it will conform to these characteristics.  

Any Model can contain (by `App::Link`) any other Model, and they are placed to each-other by matching their Datum Coordinate Systems (`PartDesign::CoordinateSystem`, called here-after LCS (Local Coordinate System)). There is no need for any geometry to be present to place and constrain parts relative to each other. LCS are used because they are both mechanical objects, since they fix all 6 degrees of freedom in an isostatic way, and mathematical objects that can be easily manipulated by rigorous methods (mainly combination and inversion).

To actually include some geometry, a body needs to be created, and designed using the PartDesign workbench. To be linked with the previously created model, this body needs to be inside the `App::Part container` called 'Model'.  

The result is the following:  
![](Resources/media/Asm4_wb0.png)

* the part _Bielle_ is placed in the assembly by attaching it's _LCS_0_ to the _LCS_0_ of the parent assembly. 
* the part _Cuve_ is placed in the assembly by placing its _LCS_0_ on the _LCS_1_ of the part _Bielle_
* the part _Bague_ is placed in the assembly by placing its _LCS_0_ on the _LCS_0_ of the part _Bielle_
* the parts _Screw_CHC_1_ and _Screw_CHC_2_ are placed in the assembly by placing their _LCS_0_ on the _LCS_1_ and _LCS_2_ of the part _Cuve_


## ExpressionEngine

Assembly4 uses a special and very useful feature of FreeCAD, the **ExpressionEngine**. Some parameters can be entered through mathematical formulae, that are evaluated by this ExpressionEngine. For Assembly4, it's the parameter _`Placement`_ of the inserted _`App::Link`_ object that is calculated, such that 2 LCS - one in the linked part and the one in the assembly - are superimposed. 

In normal use, the ExpressionEngine of an _`App::Link`_ object is hidden, it must be shown as in the following screenshot:

![](Resources/media/asm_EE.png)

#### Syntax

The syntax of the ExpressionEngine is the following:

* **If the LCS belongs to the parent assembly:**

  `LCS_parent.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS_link.Placement ^ -1`

* **If the LCS belongs to a sister part:**

  `ParentLink.Placement * ParentPart#LCS_parent.Placement * constr_LinkName.AttachmentOffset * LinkedPart#LCS.Placement ^ -1`

* **_ParentLink_ is the name of the App::Link of the sister part in the assembly**
* **_ParentPart_ is the name of the App::Part that the previous ParentLink refers-to**
* **_LCS_parent_ is the LCS in the parent part (can be either the assembly itself or a sister part in the assembly)**
* **_constr_LinkName_ is a FeaturePython object with a conventional name**
* **_LinkedPart_ is the App::Part's name that the inserted App::Link refers-to**
* **_LCS_link_ is the LCS in the linked part**

#### Constraints

To each part inserted into an assembly is associated an `App::FeaturePython` object, placed in the 'Constraints' group. This object contains information about the placement of the linked object in the assembly. It also contains an `App::Placement`, called '`AttachmentOffset`', which introduces an offset between the LCS in the part and the LCS in the assembly. The main purpose of this offset is to correct bad orientations between the 2 matching LCS. 


**Note:** These constraints are not really constraints in the traditional CAD sense, but since `App::FeaturePython` objects are very versatile, they could be expanded to contain real constraints in some (distant) future.

![](Resources/media/Asm4_wb1.png)

_Taking a closer look at the fields contained in an `App::FeaturePython` object associated with the part 'Bague'. The small button under the cursor opens the dialog that allows to edit the parameters of the Attachment Offset_

![](Resources/media/Asm4_wb2.png)

_Dialog that opens when clicking the previous small button, and permitting to edit the parameters of the_ `App::Placement` _called_ 'AttachmentOffset' _in the constraint associated with a link, and allowing relative placement of the link -vs- the attachment LCS_

## Workflow

### Toolbar
The toolbar for the Assembly4 workbench holds the following buttons:

![](Resources/media/Toolbar.png)

![New Model Icon](./Mod_Asm4/icons/Model.svg) **New Model**  

![Insert Link Icon](./Mod_Asm4/icons/LinkModel.svg) **Insert link**  

![Place linked Part Logo](./Mod_Asm4/icons/PlaceLink.svg)  **Place linked Part**

![New LCS in the Model Logo](./Mod_Asm4/icons/AxisCross.svg) **New LCS in the Model**  

![Import Datum object Logo](./Mod_Asm4/icons/ImportDatum.svg) **Import Datum object**  

![Place Datum object Logo](./Mod_Asm4/icons/Place_AxisCross.svg) **Place Datum object**

![New Sketch in the Model Logo](./Mod_Asm4/icons/Model_NewSketch.svg) **New Sketch in the Model**

![New Datum Point in the Model Logo](./Mod_Asm4/icons/Point.svg) **New Datum Point in the Model**

![New Body in the Model Logo](./Mod_Asm4/icons/PartDesign_Body.svg) **New Body in the Model**

### Part

The basic workflow for creating a part is the following:

* Create a new document, create a new 'Model' with the macro 'new_Model'. This will create a new App::Part called 'Model' with the default structure
* Create or import geometries in bodies (`PartDesign::Body`)
* Create LCS with the macro 'new_ModelLCS', and place them wherever you feel they're useful. Use the MapMode to attach the LCS
* Save part (only saved parts can be used currently). If necessary, close and re-open the file
* Repeat

### Assembly

The basic workflow for creating a part is the following:

* Create a new document, create a new 'Model'
* Create a new sketch with the 'new_ModelSketch' macro. Attach it to whatever is useful, and draw the skeleton of the assembly, placing vertices and lines where useful
* Create new LCS (with the new_ModelLCS macro) and place them on the correct vertices of the sketch (using MapMode)
* Save document
* Import a part using the 'link_Model' macro. It will place your part with its LCS_0 to the LCS_0 of the assembly. You should give it a recognisable name. 
* Select the link in the tree, and execute the macro 'place_Link'. Select the LCS of the part that you want to use as attachment point, select the part that you want it to be attached, and select the LCS in that part where you want the part to be attached. Click 'Apply'. 
* If the placement corresponds to your needs, click 'Ok', else select other LCS / Part until satisfied
* If the part is correctly paced but badly oriented, select the corresponding constraint in the 'Constraints' folder, select the property 'Offset', and modify its parameters. Click 'Apply'. Repeat until satisfied

### Nested Assemblies

The previous method allows to assemble parts within a single level.  
But this workbench also allows the assembly of assemblies: since there is no difference between 
parts and assemblies, the 'Insert External Part' allows to chose a part that has other parts linked to it. 
The only difference will be for the coordinate systems in the inserted assemblies: in order to be used 
with Assembly 4, a coordinate system must be directly in the root 'Model' container, meaning that a 
coordinate system inside a linked part cannot be used to attach the assembly to a higher-level assembly.

Therefore, in order to re-use a coordinate system of a part in an assembly, a coordinate system must be created at the root of the 'Model', and the placement of this coordinate system must be 'copied' over from the coordinate system that the user wants to use. This is done by inserting a coordinate system and using the 'Place LCS' command, which allows to select a linked part in the assembly and one of it's coordinate systems: the 2 coordinate systems — the one at the root of 'Model' and the one in the linked part — will always be superimposed, even if the linked part is modified, allowing the placement of the assembly in a higher level assembly using a linked part as reference. It sounds more complicated than it actually is.

![](Resources/media/Asm4_V4.gif)

![](Resources/media/Lego_House+Garden.png)


#### Release notes

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

## License

LGPLv2.1 (see [LICENSE](LICENSE))
