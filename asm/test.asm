LOAD r0 0xFF
LOAD r1 0x01
LOAD r2 0x01
:add
ADD_S r1 r1 r2
JUMP r1 end
JUMP r0 add
:end
HALT