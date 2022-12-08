import struct

class ByteProcessor:
    SEGMENT_BITS = 0x7F
    CONTINUE_BIT = 0x80

    def __init__(self):
        self.queue = []
        self.state = "handshake"

    def read_VarInt(self):
        value = 0
        position = 0

        while True:
            # [0] to convert it to integer which is needed for python for some reason.
            byte = self.queue.pop(0)[0]
            # ior current value with new value in case of more than 1 byte.
            value |= (byte & self.SEGMENT_BITS) << position

            # Check if the 8th byte is not on, thus reaching the end of the VarInt.
            if((byte & self.CONTINUE_BIT) == 0): break

            position += 7

            if (position >= 32): print("VarInt too long.")

        return value

    def read_String(self):
        string = ""

        # Get size of the styring
        string_size = self.read_VarInt()
        for i in range(string_size):
            byte = self.queue.pop(0)
            string += byte.decode("utf-8")
            # string += struct.unpack('>c', byte)[0]

        return string

    def read_uShort(self):
        byte = self.queue.pop(0) + self.queue.pop(0)
        return struct.unpack('>H', byte)[0]



    def readPacketC2S(self, data):
        # Add the bytes to the queue
        for byte in data:
            # For some reason looping over bytes gives you ints, so we convert
            # them back to bytes.
            self.queue.append(struct.pack('>B',byte))

        # Always read varint to get size of the packet
        packet_size = self.read_VarInt()
        packet_id = self.read_VarInt()
        print(f"Packet size: {packet_size}, Packet id: {packet_id}")
        print(self.state)

        if self.state == "handshake":
            if packet_id == 0:
                self.state = "login"
                return dict([("packet_id", packet_id),
                             ("protocol", self.read_VarInt()),
                             ("server_addr", self.read_String()),
                             ("serverPort", self.read_uShort()),
                             ("NextState", self.read_VarInt())])
        # state login, login start.

    def readPacketS2C(self, data):
        pass

        return dict([])







