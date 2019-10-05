Assembly of a V4 engine in Assembly-4:

* open the top-level assembly asm_V4.fcstd

* to animate the rotation of the crankshaft, activate document asm_V4.fcstd, 
  and copy-and-paste the following lines into the python console:

import time
step = 10
for angle in range( 30, 750+step, step ):
	App.getDocument("asm_V4").LCS_crankshaft.AttachmentOffset = App.Placement( App.Vector(0,0,0), App.Rotation( App.Vector(0,1,0), angle ) )
	App.ActiveDocument.recompute()
	Gui.updateGui()
	time.sleep(0.025)
	
	
