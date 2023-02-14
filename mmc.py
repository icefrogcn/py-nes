# -*- coding: UTF-8 -*-
#CPU Memory Map
''' Functions for emulating MMCs. Select8KVROM and the
' like
' 16.07.00'''
CurrVr = 0 #As Byte
PrgSwitch1 = 0 #As Byte
PrgSwitch2 = 0 #As Byte
SpecialWrite6000 = False #As Boolean

bank0(2047) As Byte ' RAM            主工作内存
bank6(8191) As Byte ' SaveRAM        记忆内存
bank8(8191) As Byte '8-E are PRG-ROM.主程序
bankA(8191) As Byte
bankC(8191) As Byte
bankE(8191) As Byte
'''
'the mappers try to only switch banks when necessary.
'The following helps it to ignore most unnecessary bankswitches
'下面的是用来帮助忽略大多数不必要的程序快切换
'The following vars store addresses,so that if a game switches to a bank that's already loaded in that slot,
'所以如果一个游戏切换到已经被载入的程序块，下面的用来变量存贮地址将能够避免被相同的数据覆盖
'it will be able to avoid copying data over itself

'''
'''
Private pval8 As Long
Private pval4(1) As Long
Private pval2(3) As Long
Private pval1(7) As Long
Public pTablesWritten As Boolean

Public Sub MMC3_Sync()
If swap Then
    reg8 = &HFE
    regA = PrgSwitch2
    regC = PrgSwitch1
    regE = &HFF
Else
    reg8 = PrgSwitch1
    regA = PrgSwitch2
    regC = &HFE
    regE = &HFF
End If
SetupBanks
End Sub

Public Function MaskBankAddress(bank As Byte)
If bank >= PrgCount * 2 Then
Dim i As Byte: i = &HFF
Do While (bank And i) >= PrgCount * 2
    i = i \ 2
Loop
MaskBankAddress = (bank And i)
Else
MaskBankAddress = bank
End If
End Function
'''

def MaskVROM(page, mask):
    return page and (mask - 1)

'''
'only switches banks when needed
'******只有需要时才切换******
Public Sub SetupBanks()

    reg8 = MaskBankAddress(reg8)
    regA = MaskBankAddress(regA)
    regC = MaskBankAddress(regC)
    regE = MaskBankAddress(regE)
    
    MemCopy bank8(0), gameImage(reg8 * &H2000&), &H2000&
    MemCopy bankA(0), gameImage(regA * &H2000&), &H2000&
    MemCopy bankC(0), gameImage(regC * &H2000&), &H2000&
    MemCopy bankE(0), gameImage(regE * &H2000&), &H2000&
End Sub
'''
def Select8KVROM(val1):
    val1 = MaskVROM(val1, ChrCount)
    MemCopy VRAM(0), VROM(val1 * &H2000&), &H2000&

def Select4KVROM(val1 As Byte, bank As Byte)
    val1 = MaskVROM(val1, ChrCount * 2)
    MemCopy VRAM(bank * &H1000&), VROM(val1 * &H1000&), &H1000&

def Select2KVROM(val1 As Byte, bank As Byte)
    val1 = MaskVROM(val1, ChrCount * 4)
    If Mapper = 4 Then
        MemCopy VRAM(MMC3_ChrAddr Xor (bank * &H800&)), VROM(val1 * &H800&), &H800&
    Else
        MemCopy VRAM(bank * &H800&), VROM(val1 * &H800&), &H800&
    End If

def Select1KVROM(val1 As Byte, bank As Byte)
    val1 = MaskVROM(val1, ChrCount * 8)
    Select Case Mapper
    Case 4
        MemCopy VRAM(MMC3_ChrAddr Xor (bank * &H400&)), VROM(val1 * &H400&), &H400&
    Case 23
        MemCopy VRAM(bank * &H400&), VROM(val1 * &H400&), &H400&
    Case Else
        MemCopy VRAM(bank * &H400&), VROM(val1 * &H400&), &H400&
    End Select




if __name__ == '__main__':
    print TICKS, instruction, addrmode
    TICKS, instruction, addrmode = init6502()
    print TICKS, instruction, addrmode
                #break

        










        
