# FreeCAD Assembly Without Solver / Assembly 4

FreeCAD add-on for a bare-bone assembly structure, using App::Link

Welcome to the FreeCAD_aws wiki! This page tries to explain how to make assemblies using these tools. This is the result from [discussions on the FreeCAD forum](https://forum.freecadweb.org/viewtopic.php?f=20&t=32843).


## Installation

Place and extract the downloaded archive _Assembly4.zip_ in the `~/.FreeCDA/Mod folder`, containing all extra modules.


## Principle

The point is that each part is a mostly standard FreeCAD `App::Part` object, and these are assembled using the `App::Link` framework found in the fork of FreeCAD ( https://github.com/realthunder/FreeCAD/tree/LinkStage3, pre-built binaries here: https://github.com/realthunder/FreeCAD_assembly3/releases)

The particularities of the `App::Part` used here are the following:

* they are called 'Model' at creation time 
* they contain a group called 'Constraints' at the root 
* they contain a Datum Coordinate System called LCS_0 at the root

The purpose of this is to avoid burdensome error checking: it is supposed that no other usecase would create an `App::Part` called 'Model', _i.e._ that if an `App::Part` is called 'Model' it will conform to these characteristics.

Any Model can contain (by `App::Link`) any other Model, and they are placed to each-other by matchings their Datum Coordinate Systems (`PartDesign::CoordinateSystem`, called here-after LCS : Local Coordinate System). There is no need for any geometry to be present to place and constrain parts relative to each other. LCS are used because they are both mechanical objects, since they fix all 6 degrees of freedom in an isostatic way, and mathematical objects that can be easily manipulated by rigorous methods (mainly combination and inversion).

To actually include some geometry, a body needs to be created, and designed using the PartDesign workbench. To be linked with the previously created model, this body needs to be inside the `App::Part container` called 'Model'.  

The result is the following:

![](Resources/media/asm_Bielle_tree_arrows.png)

* the part _Bielle_ is placed in the assembly by attaching it's _LCS_0_ to the _LCS_0_ of the parent assembly. 
* the part _Cuve_ is placed in the assembly by placing its _LCS_0_ on the _LCS_1_ of the part _Bielle_
* the part _Bague_ is placed in the assembly by placing its _LCS_0_ on the _LCS_0_ of the part _Bielle_
* the parts _Screw_CHC_1_ and _Screw_CHC_2_ are placed in the assembly by placing their _LCS_0_ on the _LCS_1_ and _LCS_2_ of the part _Cuve_

The 2 LCS - the one in the linked part and the one in the assembly, be it from the parent assembly or a sister part - are superimposed using an ExpressionEngine, with the following syntax:

* **If the LCS belongs to the parent assembly:**

`<<attLCS>>.Placement.multiply(<<constr_Link>>.Offset).multiply(.<<partLCS.>>.Placement.inverse())`

* **If the LCS belongs to a sister part:**

`<<attPart>>.Placement.multiply(<<attPart>>.<<attLCS.>>.Placement).multiply(<<constr_Link>>.Offset).multiply(.<<partLCS.>>.Placement.inverse())`

* **Constraints**:

To each part inserted into an assembly is associated an `App::FeaturePython` object, placed in the 'Constraints' group. This object contains information about the placement of the linked object in the assembly. It also contains an `App::Placement`, called 'Offset', which introduces an offset between the LCS in the part and the LCS in the assembly. The main purpose of this offset is to correct bad orientations between the 2 matching LCS. 

These constraints are not really constraints in the traditional CAD sense, but since `App::FeaturePython` objects are very versatile, they could be expanded to contain real constraints in some (distant) future.

![](Resources/media/asm_Bielle_constr_Offset.png)

_Close look at the fields contained in an _`App::FeaturePython`_ object associated with the part 'Cuve'_

![](Resources/media/asm_Bielle_demo.png)

_Parameters of the_ `App::Placement` _called 'Offset' allowing relative placement of the link -vs- the attachment LCS_

## Workflow

### Part

The basic workflow for creating a part is the following:

* create a new document, create a new 'Model' with the macro 'new_Model'. This will create a new App::Part called 'Model' with the default structure
* create or import geometries in bodies (`PartDesign::Body`)
* create LCS with the macro 'new_ModelLCS', and place them wherever you feel they're useful. Use the MapMode to attach the LCS
* save part (only saved parts can be used currently). If necessary, close and re-open the file
* repeat

### Assembly

The basic workflow for creating a part is the following:

* create a new document, create a new 'Model'
* create a new sketch with the 'new_ModelSketch' macro. Attach it to whatever is useful, and draw the skeleton of the assembly, placing vertices and lines where useful
* crate new LCS (with the new_ModelLCS macro) and place them on the correct vertices of the sketch (using MapMode)
* save document
* import a part using the 'link_Model' macro. It will place your part with its LCS_0 to the LCS_0 of the assembly. You should give it a recognisable name. 
* select the link in the tree, and execute the macro 'place_Link'. Select the LCS of the part that you want to use as attachment point, select the part that you want it to be attached, and select the LCS in that part where you want the part to be attached. Click 'Apply'. 
* if the placement corresponds to your needs, click 'Ok', else select other LCS / Part until satisfied
* if the part is correctly paced but badly oriented, select the corresponding constraint in the 'Constraints' folder, select the property 'Offset', and modify its parameters. Click 'Apply'. Repeat until satisfied

### Nested assemblies

The previous method allows to assemble parts within a single level. If you want to assemble an assembly into another assembly... **TBW**

![](Resources/media/asm_V4_2pistons.gif)

![](Resources/media/Lego_House+Garden.png)







<br/>
#### Release notes:<br/>

* 2019.03.09 (version 0.4) : <br/>
FreeCAD now imports as App <br/>
insert_Link launches place_Link

* 2019.03.05 (version 0.3.1) : <br/>
added the RotX-Y-Z buttons

* 2019.02.20 (version 0.3) : <br/>
mostly working version

* 2019.02.18 (version 0.1) : <br/>
initial release of Assembly 4 WB.




