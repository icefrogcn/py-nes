# -*- coding: UTF-8 -*-


#自定义类
from deco import *

#@deco
def read_file_to_array(fp):  
    return [ord(i) for i in open(fp, "rb").read()]


if __name__ == '__main__':
    pass
    #read_file_to_array('mario.nes')

