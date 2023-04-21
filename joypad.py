# -*- coding: UTF-8 -*-

import time
import math

import keyboard
#JOYPAD
from nes import NES

BUTTON_PRESS = 0x41
BUTTON_RELEASE = 0x40
class JOYPAD(NES):
    
    def __init__(self,debug = False):
         self.Joypad = [0x40] * 0x8
         #self.Joypad = [0x00] * 0x8
         self.Joypad_Count = 0
         self.padkey ={
             'enter':3,         #St
             '0':self.turnoff,
             }

    def Read(self):
        #print self.Joypad_Count
        '''try:
            return self.padkey.get(addr)()
        except:
            print "Invalid PPU Read - %s" %hex(addr)
            print (traceback.print_exc())
            return 0'''
        if keyboard.is_pressed('b'):
            #print "START"
            self.Joypad[3] = BUTTON_PRESS
        else:
            pass
            self.Joypad[3] = BUTTON_RELEASE

        if keyboard.is_pressed('v'):
            #print "SELECT"
            self.Joypad[2] = BUTTON_PRESS
        else:
            pass
            self.Joypad[2] = BUTTON_RELEASE

        
        self.Joypad[1] = BUTTON_PRESS if keyboard.is_pressed('j') else BUTTON_RELEASE
        self.Joypad[0] = BUTTON_PRESS if keyboard.is_pressed('k') else BUTTON_RELEASE
        
        self.Joypad[4] = BUTTON_PRESS if keyboard.is_pressed('w') else BUTTON_RELEASE
        self.Joypad[5] = BUTTON_PRESS if keyboard.is_pressed('s') else BUTTON_RELEASE
        self.Joypad[6] = BUTTON_PRESS if keyboard.is_pressed('a') else BUTTON_RELEASE
        self.Joypad[7] = BUTTON_PRESS if keyboard.is_pressed('d') else BUTTON_RELEASE


        if keyboard.is_pressed('0'):
            print "turnoff"
            self.turnoff()


        joypad_info = self.Joypad[self.Joypad_Count]
        self.Joypad_Count = (self.Joypad_Count + 1) & 7
        return joypad_info

    def turnoff(self):
        NES.Running = 0
if __name__ == '__main__':
    JOYPAD = JOYPAD()











        
