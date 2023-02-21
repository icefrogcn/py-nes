# -*- coding: UTF-8 -*-
import mido
from mido import Message,MidiFile,MidiTrack

import random

#APU
''' Public Sub PlayRect(ch)
    Dim f, l, v
    If SoundCtrl And pow2(ch) Then
        v = (Sound(ch * 4 + 0) And 15) 'Get volume
        l = vlengths(Sound(ch * 4 + 3) \ 8) 'Get length
        If v > 0 Then
            f = Sound(ch * 4 + 2) + (Sound(ch * 4 + 3) And 7) * 256 'Get frequency
            If f > 1 Then
                If ChannelWrite(ch) Then 'Ensures that a note doesn't replay unless memory written
                    ChannelWrite(ch) = False
                    lastFrame(ch) = Frames + l
                    playTone ch, getTone(f), v
                End If
            Else
                stopTone ch
            End If
        Else
            stopTone ch
        End If
    Else
        ChannelWrite(ch) = True
        stopTone ch
    End If
    If Frames >= lastFrame(ch) Then
        stopTone ch
    End If
End Sub'''

def MidiOpen():
    if midiOutOpen(mdh, 0, 0, 0, 0) :
        print "Cannot open midi"
    else:
        #pass
        midiOpened = True

    
'''Public Sub MidiClose()
    If midiOpened Then
        midiOutClose mdh
        midiOpened = False
    End If
End Sub'''


class APU:
    tones = [0] * 4
    volume = [0] * 4
    lastFrame = [0] * 4

    doSound = True

    vlengths = [5, 127, 10, 1, 19, 2, 40, 3, 80, 4, 30, 5, 7, 6, 13, 7, 6, 8, 12, 9, 24, 10, 48, 11, 96, 12, 36, 13, 8, 14, 16, 15] # As Long
    
def pAPUinit():
    'Lookup table used by nester.'
    #fillArray vlengths, 
    
    #SelectInstrument 0, 80 'Square wave'
    #SelectInstrument 1, 80 'Square wave'
    #SelectInstrument 2, 74 'Triangle wave. Used recorder (like a flute'
    #SelectInstrument 3, 127 'Noise. Used gunshot. Poor but sometimes works.'


def play_note(note, length, track, base_num=0, delay=0, velocity=1.0, channel=0):

    bpm = 125

    meta_time = 60 / bpm * 1000 # 一拍多少毫秒，一拍等于一个四分音符

    major_notes = [0, 2, 2, 1, 2, 2, 2, 1]

    base_note = 60 # C4对应的数字

    track.append(Message('note_on', note=base_note + base_num*12 + sum(major_notes[0:note]), velocity=round(64*velocity), time=round(delay*meta_time), channel=channel))

    track.append(Message('note_off', note=base_note + base_num*12 + sum(major_notes[0:note]), velocity=round(64*velocity), time=round(meta_time*length), channel=channel))
    

if __name__ == '__main__':

    track1 = MidiTrack()
    track1.append(Message('program_change',channel = 0 , program = 70 ,time = 6.2))
    track1.append(Message('note_on', channel=0, note=100, velocity=3, time=6.2))
                #break
    msg = mido.Message('note_on', note=60)
    msg.bytes()
    port = mido.open_output('Port Name')
    port.send(msg)










        
