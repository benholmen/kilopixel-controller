(MACHINE SETUP)
(https://github.com/gnea/grbl/wiki/Grbl-v1.1-Configuration)
$100=100	(X steps/mm. Calculate at 16 teeth/rev * 2mm/tooth * 200 steps/rev * 1/16 steps)
$101=100	(Y steps/mm. Calculate at 16 teeth/rev * 2mm/tooth * 200 steps/rev * 1/16 steps)

$110=8000	(X max speed mm/min)
$111=8000	(Y max speed mm/min)

$120=200	(X max accel mm^2/min)
$121=200	(Y max accel mm^2/min)

$130=1800	(X max travel)
$131=1125	(Y max travel)
$132=0		(Z max travel)

$22=0		(homing: 1 = enable, 0 = disable)
$23=1		(homing direction: top left home location)

($1=255)		(step idle delay: keep the steppers powered and locked all the time. Could also turn them off to save power/heat but might lose steps)
$1=0		(step idle delay: unpower the steppers during testing. they get HOT)
