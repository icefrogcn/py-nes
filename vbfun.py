# -*- coding: UTF-8 -*-

from numba import jit

#自定义类
from deco import *

#@jit
def MemCopy(dest, dest_p, src, src_p , size):
    if type(dest) == list and type(src)== list:
        dest[dest_p:dest_p + size] = src[src_p : src_p + size]
        '''for i in range(size):
            if src_p + i <= len(src) - 1:
                dest[dest_p + i] = src[src_p + i]'''



if __name__ == '__main__':
    pass
    test1 = [0] * 20
    test2 = range(30)
    print range(100)
    MemCopy(test1, 0, test2, 11 , 11)
    print test1

