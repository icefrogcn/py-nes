# -*- coding: UTF-8 -*-
import threading
import time
from numba import jit,jitclass,objmode

#自定义类
from deco import *

#@deco
def read_file_to_array(fp):  
    return [ord(i) for i in open(fp, "rb").read()]

class mm():
    def __init__(self):
        self.acc = 0
    def t_1(self):
        while 1:
            if self.acc % 1000 == 0:
                continue
            self.acc += 1

    def t_2(self):
        while 1:
            if self.acc % 1000 == 0:
                self.acc += 1
            else:
                pass
            #print self.acc

@jit
def t():
    with objmode(time1='f8'):
        time1 = time
    return time1

if __name__ == '__main__':
    pass
    mm = mm()
    t1 = threading.Thread(target = mm.t_1)
    t2 = threading.Thread(target = mm.t_2)

    print t()

