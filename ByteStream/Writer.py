from Utils.Helpers import Helpers

class Writer:
    def __init__(self, client, endian='big'):
        self.client=client; self.endian=endian; self.buffer=b''
    def writeInt(self,data,length=4): self.buffer += data.to_bytes(length,self.endian,signed=True)
    def writeUInteger(self,integer,length=1): self.buffer += integer.to_bytes(length,self.endian,signed=False)
    def writeLong(self,data): self.writeInt(data,8)
    def writeLogicLong(self,data): self.writeVInt(0); self.writeVInt(data)
    def writeArrayVint(self,data): self.writeVInt(len(data)); [self.writeVInt(x) for x in data]
    def writeUInt8(self,integer): self.writeUInteger(integer)
    def writeInt8(self,integer): self.writeInt(integer,1)
    def writeInt16(self,data): self.writeInt(data,2)
    def writeBool(self,boolean): self.writeUInt8(1 if boolean else 0)
    def writeByte(self,data): self.writeInt(data,1)
    def writeBytes(self,data): self.buffer += data
    def writeVInt(self,data,rotate=True):
        if data==0: self.writeByte(0); return
        if data<0: data=(2147483648*2)+data
        else: data=(data<<1)^(data>>31)
        final=b''
        while data:
            b=data&0x7f
            if data>=0x80: b|=0x80
            if rotate:
                rotate=False; lsb=b&1; msb=(b&0x80)>>7; b>>=1; b=b&~0xC0; b|=(msb<<7)|(lsb<<6)
            final += b.to_bytes(1,'big'); data >>= 7
        self.buffer += final
    def writeString(self,string=None):
        if string is None: self.writeInt(-1)
        else:
            encoded=string.encode(); self.writeInt(len(encoded)); self.buffer += encoded
    def writeDataReference(self,x,y=0):
        if x!=0: self.writeVInt(x); self.writeVInt(y)
        else: self.writeVInt(0)
    def writeNullVInt(self): self.writeVInt(-1)
    def size(self): return len(self.buffer)
    def getRaw(self): return self.buffer
    writeBoolean=writeBool
    writeInt32=writeInt
    writeVint=writeVInt
    writeScId=writeDataReference
