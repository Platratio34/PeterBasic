LOAD 0 01
LOAD 1 FF
LOAD 2 01
LOAD 3 02
LOAD 4 02
LOAD 5 30
:loop
ADD_S 0 0 2
JUMP 1 end
JUMP 3 store
JUMP 0 loop
:store
MOVE 0 7
MOVE 0 6
LOAD 0 0A 
:storeLoop
JUMP_L 6 storeLoopEnd
LOAD 6
:storeLoopEnd
MOVE 7 0
ADD_S 6 0 5
STORE_P 6 00
ADD_S 3 3 4
JUMP 0 loop
:end
HALT