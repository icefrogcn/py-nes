# -*- coding: UTF-8 -*-
import mido
from mido import Message, MidiTrack

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




if __name__ == '__main__':

    track1 = MidiTrack()
    track1.append(Message('program_change',channel = 0 , program = 70 ,time = 6.2))
    track1.append(Message('note_on', channel=0, note=100, velocity=3, time=6.2))
                #break
    msg = mido.Message('note_on', note=60)
    msg.bytes()
    port = mido.open_output('Port Name')
    port.send(msg)










        
