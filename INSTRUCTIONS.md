# FreeCAD Assembly 4 workbench user instructions

These instructions present the intended usage and workflow to assembly design using FreeCAD's Assembly4 workbench. It is intended for all users.



## Installation


### Addon Manager (recommended)

Assembly 4 is available through the FreeCAD Addon Manager (menu **Tools > Addon Manager**). It is called _Assembly4_ in the Addon Repository.  

[![FreeCAD Addon manager status](https://img.shields.io/badge/FreeCAD%20addon%20manager-available-brightgreen)](https://github.com/FreeCAD/FreeCAD-addons)

**Important Note:** Assembly 4 needs FreeCAD v0.19 or above. Assembly4 is **not** compatible with FreeCAD v0.18 and before. 

**Important Note:** Assembly 4 is **not** compatible with Assembly2+ and Assembly3.


### Manual Installation

It is also possible to install this workbench manually into FreeCAD's local workbench directory. This can be useful for testing local modifications to the workbench, or to remove an old stale version of the workbench. 

In this case, download the Github [FreeCAD_Assembly4-master.zip](https://github.com/Zolko-123/FreeCAD_Assembly4/archive/master.zip) archive from [github.com/Zolko-123/FreeCAD_Assembly4](https://github.com/Zolko-123/FreeCAD_Assembly4) to a temporary directory, and extract the Zip archive. Then, remove any existing Assembly4 directory from FreeCAD's local workbench directory, and copy the folder *FreeCAD_Assembly4-master* into the directory containing all FreeCAD addon modules :

* for Windows: `C:\Users\******\AppData\Roaming\FreeCAD\Mod`
* for MacOS: `~/Library/Preferences/FreeCAD/Mod/`
* for Linux, _FreeCAD version v0.19_ : `~/.FreeCAD/Mod` 
* for Linux, _FreeCAD version v0.20_ : `~/.local/share/FreeCAD/Mod/` 






## Usage

Assembly4 commands are accessible from the Assembly menu or the Assembly4 toolbar. The **Assembly** menu contains tools to _build_ the assembly, and the **Constraints** menu contains tools to _place_ parts relative to each other.


### Toolbar

Commands are activated with relevant selection. If a command is inactive (grayed out) it's because something is selected to which that function doesn't apply.

![](Resources/media/Asm4_Toolbar.png)

### Menu

<details>
  <summary>These functions are also accessible from the Assembly menu:</summary> 

![](Resources/media/Asm4_Menu.png)

</details>

### Assembly4 commands

. Icon .|Tool|Description 
:---|:---|:---
![](Resources/icons/Asm4_Model.svg)|**New Assembly**|creates an assembly, which is a FreeCAD `App::Part` called *Assembly* and with some extra additions. This can be used to design a stand-alone part or be the container for an assembly. One document can only contain one assembly container.
![](Resources/icons/Asm4_Body.svg)|**New Body**|creates FreeCAD `PartDesign::Body` in the selected `App::Part`. This Body can then be used with FreeCAD's PartDesign workbench. If you create such a `PartDesign::Body` with the PartDesign workbench, it will be placed at the root of the document, outside any `App::Part`.
![](Resources/icons/Asm4_Part.svg)|**New Part**|creates FreeCAD `App::Part` in the current document and allows to give it a name. A document can contain many parts.
![](Resources/icons/Asm4_Group.svg)|**New Group**|creates FreeCAD `App::DocumentObjectGroup` in the current document and allows to give it a name. A group has no other function than as an organizer in the Tree view.
![](Resources/icons/Asm4_PartInfo.svg)|**Edit Part Information**|Add information to selected Part to be used in for example BOM.
![](Resources/icons/Link_Part.svg)|**Insert Part**|creates a FreeCAD `App::Link` to an `App::Part`. Only parts from documents already open in the session and saved to disk can be used. If there are multiple parts in a document, they can be selected individually. A part can be inserted (linked) many times, but each instance must have a unique name in the assembly tree. If a name already attributed is given again, FreeCAD will automatically give it a unique (and probably un-user-friendly) name.
![](Resources/icons/Asm4_Screw.svg)|**Fasteners dropdown**|Allows to insert industry standard screws, nuts and washers from the **Fasteners Workbench** library, and allows to attach them to Assembly4 datum objects, primarily coordinate systems (LCS). These features are only available if the Fasteners Workbench is installed. The Fasteners Workbench can be installed like Assembly4 through FreeCAD's addon manager: menu **Tools > Addon Manager > fasteners**
![](Resources/icons/Asm4_Screw.svg)|*Insert Screw*|creates a normed screw from the Fasteners Workbench. The type of screw, diameter and length can be changed in the properties window of the screw after creation.
![](Resources/icons/Asm4_Nut.svg)|*Insert Nut*|creates a normed nut from the Fasteners Workbench. The type of nut, diameter and length can be changed in the properties window of the nut after creation.
![](Resources/icons/Asm4_Washer.svg)|*Insert Washer*|creates a normed washer from the Fasteners Workbench. The type of washer and its diameter can be changed in the properties window of the washer after creation.
![](Resources/icons/Asm4_mvFastener.svg)|*Edit attachment of Fastener*|allows to attach an object from the Fasteners Workbench — screw, nut or washer — to a datum object in the assembly or a sister part, in the regular Assembly4 manner.
![](Resources/icons/Asm4_Sketch.svg)|**New Sketch**|creates FreeCAD Sketch in an `App::Part` (and thus also in Assembly4 Models). After creation the attachment dialog opens and allows to attach this Sketch.
![](Resources/icons/Asm4_AxisCross.svg)|**New Datum**|this is a drop-down combined menu grouping the creation of all Datum objects:
![](Resources/icons/Asm4_AxisCross.svg)|*New LCS*|creates `PartDesign::CoordinateSystem` in an `App::Part` (and thus also in Assembly4 Models). This LCS is unattached, to attach it to an object edit its MapMode in its Placement Property
![](Resources/icons/Asm4_Plane.svg)|*New Datum Plane*|creates a datum `PartDesign::Plane`
![](Resources/icons/Asm4_Axis.svg)|*New Datum Axis*|creates a datum `PartDesign::Line`
![](Resources/icons/Asm4_Point.svg)|*New Datum Point*|creates a datum `PartDesign::Point`
![](Resources/icons/Asm4_Hole.svg)|*New Hole LCS*|creates datum `PartDesign::CoordinateSystem` in an `App::Part` (and thus also in Assembly4 Models) at the center of the selected circular edge. This is therefore only active when a (single) circular edge is selected. This `PartDesign::CoordinateSystem` is attached to the center of the circle, and is intended to serve as attachment LCS for fasteners.  This is the combined function of creating an LCS and attaching it (via MapMode) to a circular edge, and is provided to streamline the workflow.
![](Resources/icons/Import_Datum.svg)|**Import Datum**|this imports an existing Datum object from a linked part into the assembly. Precisely, it creates a Datum in the assembly and attaches it to a datum in a sister part of the same type. By default, the same name is given to the imported Datum object. 
![](Resources/icons/Asm4_shapeBinder.svg)|**Create a shape binder**|Create a reference to an external shape. This creates a SubShapeBinder of the selected shapes (face, edge, point) in the root assembly. Only shapes belonging to the same part can be imported in a single step 
![](Resources/icons/Place_Link.svg)|**Place Link**|this positions the child instance of a linked part in the current host assembly. This attaches an LCS in the linked part to a target LCS in the assembly. This target LCS can be either in the assembly itself (in the *Model*) or in a sister part already linked. In this case, it is important to note that only LCS at the root of the linked part can be used.
![](Resources/icons/Asm4_releaseAttachment.svg)|**Release from Attachment**|Release an object from all attachments to any geometry.
![](Resources/icons/Asm4_Solver.svg)|**Solve constraints and update assembly**|this recomputes all the links and all the placements in the assembly
![](Resources/icons/Asm4_Mirror.svg)|**Mirror**|Create a mirror of selected object. Select a source object and then a mirror plane or a normal to a plane before activating the tool. 
![](Resources/icons/Asm4_LinearArray.svg)|**Linear Array**|Create a linear array. Select first an object and then a direction object. The property Linear Step is the distance between elements. Example expression on Linear Step property to place the last element 100 mm from start position `100mm*Index/(Count + 1)`
![](Resources/icons/Asm4_PolarArray.svg)|**Circular Array**|Create a circular (polar) array of the selected object and axis. Default expression for Angle Step property is `360/Count` to distribute the elements around a full circle. 
![](Resources/icons/Asm4_ExpressionArray.svg)|**Expression Array**|A base for arrays and mirror. Creates an array of the selected object where the placement of each element is calculated using expressions and an Index property. Select a source object to array and optionally an Axis that transformation will be related to. Without axis the transformations relates to the source object internal Z axis. Supported axis objects are axis or plane from an origin, datum line, LCS axes, straight line segments, arcs and circles. The Count property is the amount of elements in the array. The Placer property is recomputed and copied to each of the arrayed link while the Index property is incremented. Use Index in expressions on the entire Placer or its sub-properties. By opening Placer property in Tasks panel it is possible to set expressions for euler angles too. The Scaler propertie works in a similar way and sets the scale of the links.
![](Resources/icons/Variant_Link.svg)|**Variant Link**|This is a link to a part but with varying parameters, meaning that you can isert the same part several times, but adjusting the parameters of each instance of the part. Objects that can be used as source for a variant link are standard App::Part (Std_Part) that contain a PropertyContainer called "Variables". All variables of the source object can be set individually for each variant. Such variant links and their individual variables are persistent, meaning that they will be restored when the document is restored.
![](Resources/icons/Asm4_showLCS.svg)<br/>![](Resources/icons/Asm4_hideLCS.svg)|**Show/Hide LCS**|Shows or hides LCSs of selected part and its children. 
![](Resources/icons/Asm4_PartsList_Subassemblies.svg)<br/>![](Resources/icons/Asm4_PartsList.svg)|**Bill of Materials**|[BOM Example](https://github.com/Zolko-123/FreeCAD_Assembly4/blob/master/Examples/ConfigBOM/README.md)
![](Resources/icons/Part_Measure.svg)|**Measure**|Measure tool.
![](Resources/icons/Asm4_addVariable.svg)<br/>![](Resources/icons/Asm4_delVariable.svg)|**Add/Delete Variable**|this adds a variable to the `Variables` object in the Model. These variables can be used in any parameter of the document by entering `Variables.Height` or `Variables.Length` (for example). This is especially useful for assemblies built in a single file, where several parts can be built using the same dimensions. Modifying a variable is done in the `Properties` window of the `Variables` object.
![](Resources/icons/Asm4_Configurations.svg)|**Configurations**|Exploded assemblies can be done with configurations: first, make a default configuration with all parts in their correct location. Then, move and/or hide parts as wished by adjusting the AttachmentOffset property of each part. You can then create a new configuration based on this state. As opposed to an exploded assembly, you can create as many states as you wish, showing/hiding parts, and/or offsetting parts from their assembled position.
![](Resources/icons/Asm4_GearsAnimate.svg)|**Animate Assembly**|allows to select one of the variables from the `Variables` object and sweep it between two values. All parameters of the assembly that are set by this variable will be updated.

There is also a toolbar for selection filters

. Icon .|Tool|Description 
:---|:---|:---
![](Resources/icons/Snap_Vertex.svg)<br/>![](Resources/icons/Snap_Edge.svg)<br/>![](Resources/icons/Snap_Face.svg)|**Selection filters**|filter selections so that only vertices, edges or faces can be selected.
![](Resources/icons/Asm4_enableLinkSelection.svg)|**3D View selection mode**|Toggle 3D View selection mode which allows to select a Link object in the 3D view window instead of the Model tree.
![](Resources/icons/Asm4_SelectionAll.svg)|**Clear selection filters**|removes all filters and get back to normal selection



## Workflow

Some general purpose 3D CAD systems propose a workflow based on finished parts that are assembled into an assembly, and their position in that assembly is determined by constraints imposed on geometrical features present in the parts: holes, edges, faces... While this is quite easy to understand for beginners, it poses some limits on advanced users who need to modify the parts that are already inserted into an assembly. For example, if a part is placed using some geometrical feature, and that feature is later modified during the design process, the assembly solver might not be able to find the original constraint because the geometrical feature on which it was based has disappeared, and will throw an error. This can be a very difficult problem to solve, and is due to the dreaded *topological naming* issue. 

Therefore, this is not the workflow used in Assembly 4, and instead Assembly 4 uses the principle of a **master sketch**|at the root of the assembly, *i.e.* in the Assembly 4 *Model*, one — or more — sketches are drawn that represent the "skeleton" of the assembly. This skeleton matches the functionalities of the assembly, and holds elements such as points and lines at characteristical positions of the assembly: rotational axes, fixation points, translation axes, beam directions... Furthermore, local coordinate systems — technically these are `PartDesign::CoordinateSystem` type objects and are called **LCS** in Assembly 4 — are placed on these characteristical points. The same principle — local coordinate systems at characteristical locations — is also applied in the design process of parts. Thus, the local coordinate systems in the parts can be matched to local coordinate systems in the assembly, guaranteeing that the part is positioned in the assembly at its intended position.



### Part

The basic workflow for creating a part is the following:

* Create a new document, create a new 'Part' with the 'New Part' tool. This will create a new App::Part called with a LCS at the origin.
* Create or import geometries in bodies (`PartDesign::Body`)
* Create LCS with the 'New Coordinate System', and place them wherever you feel they're useful. Use the MapMode to attach the LCS
* Save part (only saved parts can be used currently). If necessary, close and re-open the file
* Repeat

### Assembly

The basic workflow for creating a part is the following:

* Create a new document, create a new 'Assembly'
* Create a new sketch with the 'New Sketch' tool. Attach it to whatever is useful, and draw the skeleton of the assembly, placing vertices and lines where useful
* Create new LCS (with the 'New Coordinate System' tool) and place them on the correct vertices of the sketch (using MapMode)
* Save document
* Import a part using the 'Insert Part' tool. In the Task panel, choose coordinate system from Part respective Model that shall be coincident.
* If the placement corresponds to your needs, click 'Ok', else select other LCS / Part until satisfied
* If the part is correctly placed but badly oriented, use the rotate buttons on the bottom of the Task panel.

### Nested Assemblies

The previous method allows to assemble parts within a single level.  
But this workbench also allows the assembly of assemblies: since there is no difference between 
parts and assemblies, the 'Insert External Part' allows to chose a part that has other parts linked to it. 
The only difference will be for the coordinate systems in the inserted assemblies: in order to be used 
with Assembly 4, a coordinate system must be directly in the root 'Model' container, meaning that a 
coordinate system inside a linked part cannot be used to attach the assembly to a higher-level assembly.

Therefore, in order to re-use a coordinate system of a part in an assembly, a coordinate system must be created at the root of the 'Model', and the placement of this coordinate system must be 'copied' over from the coordinate system that the user wants to use. This is done by inserting a coordinate system and using the 'Place LCS' command, which allows to select a linked part in the assembly and one of it's coordinate systems: the 2 coordinate systems — the one at the root of 'Model' and the one in the linked part — will always be superimposed, even if the linked part is modified, allowing the placement of the assembly in a higher level assembly using a linked part as reference. It sounds more complicated than it actually is.

![](Resources/media/Asm4_V4.png)

![](Resources/media/Lego_House+Garden.png)



## Principle

We present here a short summary of the inner workings of FreeCAD's Assembly4 workbench.

### Data structure

The very principle of Assembly4 is that `App::Part` objects are linked together using the `App::Link` interface introduced in FreeCAD v0.19. The host parent assembly **and** the included child parts are all `App::Part` type objects. The parts that are linked can be in the same document as the assembly or an external document, invariably.

Since a FreeCAD `App::Part` is a container, all objects included in the child part will be included in the parent assembly. To actually insert some geometry, solids or bodies need to be created inside the `App::Part` container and designed using other FreeCAD workbenches.

**Please Note:** objects in the same document as the linked part but outside the `App::Part` container will not be inserted. The *PartDesign* workbench doesn't produce **Parts**, it produces **Bodies**. It is entirely possible to use Parts made with the *Part* workbench with Assembly4, but if you want to use Bodies made with the PartDesign WB you need first to create a Part and move the Body into that Part.

### Part placements

Instances of linked parts are placed in the assembly using their *Placement* property, visible and accessible in their *Property* window. This *Placement* property can be calculated in various ways:

* manually, by setting the parameters in the *Placement* property fields or by using the **Transform** tool (right-click > Transform)
* by using Assembly4's **Place linked part** tool, which sets an *ExpressionEngine* into the *Placement* property.

When using Assembly4's tool, a local coordinate system in the child part and one in the host parent assembly are matched (superimposed). This is somewhat different from constraints that some other CAD systems use, but once used to it this approach is very powerful.

The result is the following:  

![](Resources/media/Asm4_Bielle_Bague.png)

In this example, the instance *Bague* is highlighted:

* the blue circle shows the *Placement* property 
  * the blue text in the *Value* field indicates that the *Placement* is calculated by the *ExpressionEngine*
* the red circle shows the properties of this instance:
  * *Assembly Type* `Asm4EE` indicates that it's an Assembly4 object
  * *Attached By* `#LCS_O` indicates that the child part's *LCS_0* is the reference to insert the part into the assembly
  * *Attached To* `Bielle#LCS_O` indicates that this instance is attached to the child instance *Bielle* (this is the name of the child instance in this assembly and not that of the original part !) and in that child it is targeted at _LCS_0_
  * the *Attachment Offset* property allows to offset the child's attachment LCS w.r.t. the target LCS. In this example, the child instance *Bague* is offset in the Z-direction by -15mm

All Assembly4 children have these 4 properties; these are the first places to check if something in your assembly doesn't behave as expected.




## Tutorials and Examples

You can use the [example assemblies](https://github.com/Zolko-123/FreeCAD_Examples) to experiment with this workbench's features. Open one _asm_something.fcstd_ file and try out the functions. There are `ReadMe.txt` files in each directory with some explanations. There are tutorials available to learn to use Assembly4:

* [a quick assembly from scratch](https://github.com/Zolko-123/FreeCAD_Examples/blob/master/Asm4_Tutorial1/README.md)
* [a cinematic assembly in one file, using a master sketch](https://github.com/Zolko-123/FreeCAD_Examples/blob/master/Asm4_Tutorial2/README.md)
* [a Lego assembly](https://github.com/Zolko-123/FreeCAD_Examples/tree/master/Asm4_Tutorial3)



## License

LGPLv2.1 (see [LICENSE](LICENSE))
