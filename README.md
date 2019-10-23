# FreeCAD Assembly 4 / Assembly Without Solver
FreeCAD add-on for a bare-bone assembly structure, using App::Link  

An Assembly4 model is a standard FreeCAD `App::Part` object, and can be used with any FreeCAD tool handling `App::Part` objects. An Assembly4 Model can invariably be a stand-alone part, an assembly, a sub-assembly, and any combinations of these.

Any Assembly4 Model can contain (by `App::Link`) any other Assembly4 Model or any `App::Part`, but an `App::Part` cannot be used with Assembly4 to link by `App::Link` other `App::Part` objects. Parts and linked parts are placed to each-other by matching their Datum Coordinate Systems (`PartDesign::CoordinateSystem`, called here-after LCS for Local Coordinate System) using the built-in FreeCAD ExpressionEngine. No geometry is used to place and constrain parts relative to each other, thus avoiding a lot of the topological naming problems. 

![](Resources/media/Asm4_wb1.png)


## Prerequisites

**Important Note:** Assembly 4 is **not** compatible with FreeCAD v0.18, needs :

- [x] FreeCAD >= `v0.19.18353`

Pre-built binaries on the v0.19 development branch can be found [here](https://github.com/FreeCAD/FreeCAD/releases/tag/0.19_pre)


## Installation

### Automatic Installation (recommended)

Assembly 4 is available through the FreeCAD Addon Manager (menu Tools > Addon Manager). It is called _Assembly4_ in the Addon Repository.  

[![FreeCAD Addon manager status](https://img.shields.io/badge/FreeCAD%20addon%20manager-available-brightgreen)](https://github.com/FreeCAD/FreeCAD-addons)

**Note:** Restarting FreeCAD is required after installing this Addon.


## Getting Started

You can use the [example assemblies](https://github.com/Zolko-123/FreeCAD_Assembly4/tree/master/Examples) to experiment with this workbench's features. Open one _asm_something.fcstd_ file and try out the functions. There are `ReadMe.txt` files in each directory with some explanations. There are tutorials available to lear tu use Assembly4:

* [a quick assembly from scratch](TUTORIAL1.md)
* [a cinematic assembly reusing existing FreeCAD parts](TUTORIAL2.md)
* [a multy-layered assembly for advanced users](TUTORIAL3.md)
* [a Lego assembly](TUTORIAL4.md)
* [an architectural assembly](TUTORIAL5.md)



## Principle

Assembly4 uses a very powerful feature of FreeCAD, the **ExpressionEngine**. Some FreeCAD object's parameters can be entered through mathematical formulae, that are evaluated by this ExpressionEngine. For Assembly4, it's the parameter _`Placement`_ of the inserted _`App::Link`_ object that is calculated, such that 2 LCS - one in the linked part and the one in the assembly - are superimposed. 

You can find more informations in the detailed [instructions](INSTRUCTIONS.md).



## Constraints

To each part inserted into an assembly is associated constraint, which is an `App::FeaturePython` object in Assembly4, placed in the '_Constraints_' group at the root of the assembly. This constraint object contains information about the placement of the linked object in the assembly. 

At the time of this writing, there is only 1 type of constraint in Assembly4 : matching of LCS between 2 objects. It is foreseen in the future to extend the available types of constraints.

Each constraint contains an `App::Placement` property, called '`AttachmentOffset`', which introduces an offset between the attachment LCS in the part and the target LCS in the assembly. This allows 



## Free Placement

It is also possible to insert a part into an assembly without any constraint and without using the ExpressionEngine. In this case the inserted part (its `App::Link` really) can be moved manually by the built-in FreeCAD dragger. Right-click on the link in the Model tree, and in the contextual menu choose _Transform_ . It is also possible to manually edit the inserted link's _Placement_ property.

This is then a raw interface between FreeCAD `App::Part` objects through the `App::Link` functionality.



## Release notes

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
