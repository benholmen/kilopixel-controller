(MACHINE SETUP)
(https://github.com/gnea/grbl/wiki/Grbl-v1.1-Configuration)
(https://wiki.shapeoko.com/index.php/G-Code#G-code_supported_by_Grbl)

$100=26.667	(X steps/mm. Calculate at 200 steps/rev * 4 microsteps / 60 mm per rev)
$101=26.667	(Y steps/mm. Calculate at 200 steps/rev * 4 microsteps / 60 mm per rev)
$102=200	(Z steps/mm. Calculate at 200 steps/rev * 1 microsteps / 16 mm per rev)

$110=6000	(X max speed mm/min: top tested speed 8000)
$111=6000	(Y max speed mm/min: top tested speed 6000)
$112=300	(Z max speed mm/min: top tested speed 800+; 400 is good)

$120=400	(X max accel mm^2/min)
$121=400	(Y max accel mm^2/min)
$122=300	(Z max accel mm^2/min)

$130=1170	(X max travel)
$131=710	(Y max travel)
$132=2000	(Z max travel)

(HOMING REFERENCE: https://github.com/gnea/grbl/wiki/Set-up-the-Homing-Cycle)
$5=0		(limit switch type: 1 = NC)
$3=5		(stepper motor direction: X and Z inverted)
$21=0		(enable soft limits to avoid crashing)
$22=1		(homing: 1 = enable, 0 = disable)
$23=7		(homing direction)
$25=8000	(homing speed: initial seek speed)
$27=1.00	(homing pull-off, in mm: I want this to be enough to clear the limit switch, but < 1/4 turn of the Z-axis)

$1=255		(step idle delay: keep the steppers powered and locked all the time. Could also turn them off by setting to 0 to save power/heat but might lose steps)

$H

