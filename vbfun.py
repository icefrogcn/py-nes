# -*- coding: UTF-8 -*-
import time
from numba import jit

#自定义类
from deco import *

#@jit
def MemCopy(dest, dest_p, src, src_p , size):
    #if type(dest) == list and type(src)== list:
        dest[dest_p:dest_p + size] = src[src_p : src_p + size]
        '''for i in range(size):
            if src_p + i <= len(src) - 1:
                dest[dest_p + i] = src[src_p + i]'''


def mcopy(dest, dest_p, src, src_p , size):
    for i in range(10000):
        if type(dest) == list and type(src)== list:
            dest[dest_p:dest_p + size] = src[src_p : src_p + size]

#@jit
def mcopy1(dest, dest_p, src, src_p , size):
    for i in range(10000):
        dest[dest_p:dest_p + size] = src[src_p : src_p + size]

if __name__ == '__main__':
    pass
    print range(10)
    test1 = [255] * 200000
    test2 = range(300000)
    #print range(100)
    start = time.clock()
    mcopy1(test1, 0, test2, 11 , 10000)
    print time.clock() - start
    #print test1
    start = time.clock()
    mcopy(test1, 0, test2, 11 , 10000)
    print time.clock() - start
    #print test1

