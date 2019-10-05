Assembly of a hypnotic thingy: https://forum.freecadweb.org/viewtopic.php?f=20&t=34530


* open the top-level assembly asm_Hypnotic.fcstd

* to animate the rotation of the wheel, activate document asm_Hypnotic.fcstd, 
  and copy-and-paste the following lines into the python console:

step = 1
for angle in range( 15, 735+step, step ):
	App.getDocument("asm_Hypnotic").LCS_rot.AttachmentOffset = App.Placement( App.Vector(0,0,0), App.Rotation( App.Vector(0,0,1), angle ) )
	App.activeDocument().recompute()
	Gui.updateGui()
	
	
