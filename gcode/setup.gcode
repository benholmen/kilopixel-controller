(MACHINE SETUP)
(https://github.com/gnea/grbl/wiki/Grbl-v1.1-Configuration)
(https://wiki.shapeoko.com/index.php/G-Code#G-code_supported_by_Grbl)

$100=26.67 (X steps/mm. Calculate at 200 steps/rev * 16 microsteps / 60 mm per rev)
$101=26.67 (Y steps/mm. Calculate at 200 steps/rev * 16 microsteps / 60 mm per rev)

$110=8000	(X max speed mm/min)
$111=6000	(Y max speed mm/min)

$120=1200    (X max accel mm^2/min)
$121=600	(Y max accel mm^2/min)

$130=1800	(X max travel)
$131=1125	(Y max travel)
$132=0		(Z max travel)

$130=780    (PROTOTYPE: X max travel)
$131=320    (PROTOTYPE: Y max travel)

(HOMING REFERENCE: https://github.com/gnea/grbl/wiki/Set-up-the-Homing-Cycle)
$5=0        (limit switch type: 1 = NC)
$22=1		(homing: 1 = enable, 0 = disable)
$23=3		(homing direction)
$25=6000    (homing speed: initial seek speed)

$1=255	    (step idle delay: keep the steppers powered and locked all the time. Could also turn them off by setting to 0 to save power/heat but might lose steps)

$10=3       (Status Report: Machine Position and Work Position)
