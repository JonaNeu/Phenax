def writeText(device,text):
    for c in text:
        writeChar(device,c)

def writeChar(device,c):
    if c >= "0" and c <= "9":
        device.press( 0x07 + (ord(c)-ord('0')) )
        return
    if c >= "a" and c <= "z":
        device.press( 0x1d + (ord(c)-ord('a')) )
        return
    if c >= "A" and c <= "Z":
        device.press( 0x1d + (ord(c)-ord('A')), 0x01 )
        return
    if c == '\\':
        device.press( 0x49 )
        return
    if c == '\'':
        device.press( 0x4b )
        return
    if c == '@':
        device.press( 0x4d )
        return
    if c == '_':
        device.press( 0x5f )
        return
#TODO To complete...
