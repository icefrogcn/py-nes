# -*- coding: UTF-8 -*-
import re



import time
import datetime
import threading

ttt = 0
bbb = ttt
bbb=bbb+1
print ttt,bbb


#自定义类
from deco import *
from wrfilemod import *

import cpu6502commands
from cpu6502commands import *

#import cpu6502
#from cpu6502 import *

import neshardware
from neshardware import neshardware

NESLoop = 0
CPURunning = True
FirstRead = True










    
if __name__ == '__main__':
    pass
    
    #fc = neshardware()
    #fc.ROM.LoadNES('1942.nes')
    #fc.StartingUp()

    var = 513
    print bin(var)
    print var // 128
    
    start = time.clock()
    print bin(var>>7 & 0x1)
    print time.clock() - start

    
    start = time.clock()
    print bin(var // 128 & 0x1)
    print time.clock() - start
    #cpu6502.exec6502()
        










        
