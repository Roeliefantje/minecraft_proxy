import struct

class ByteProcessor:
    SEGMENT_BITS = 0x7F
    CONTINUE_BIT = 0x80
    client_public_key = None
    server_public_key = None

    # TODO
    # When encryption request is sent from the server, Client creates Encryption response packet
    # Client generates 16-byte shared secret and uses the server public key to encrypt it
    # So we need to send back our public key to the client when we intercept the encryption request from the server
    # This way we can know the shared secret which will be used for encryption.
    # We also need to decrypt the token and encrypt it using the server public key, as only then will the server
    # ack the handshake.


    # After this the server and client need to make a request to sessionserver.mojang.com
    # But the hashes will not match, as the client uses our public key instead of that of the server,
    # So we probably have to send a get request ourselves as well, this way the server will send a Login Success packet.

    # If we make the client send an invalid packet with our public key, I dont know what happens, but maybe it unvalidates the connection,
    # In this case, we could make the client ocnnect to us generating our own server id, and then connect to the server and send another request packet.
    # As far as I am aware, you can be online on two servers at once, so this shouldn't bring problems.

    # https://wiki.vg/Protocol_Encryption

    def __init__(self):
        self.queue = []
        self.state = "handshake"

    def read_VarInt(self):
        value = 0
        position = 0

        while True:
            # [0] to convert it to integer which is needed for python for some reason.
            byte = self.queue.pop(0)
            integer_value = struct.unpack('>b', byte)[0]
            # ior current value with new value in case of more than 1 byte.
            # But seeing how we handle them as integers += is the same.
            value |= (int) (integer_value & self.SEGMENT_BITS) << position

            # Check if the 8th byte is not on, thus reaching the end of the VarInt.
            if((integer_value & self.CONTINUE_BIT) == 0): break

            position += 7

            if (position >= 32): print("VarInt too long.")

        return value

    def write_VarInt(self, value):
        # while True:
        #     if ()
        pass

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
        return struct.unpack('>h', byte)[0]

    def read_bool(self):
        byte = self.queue.pop(0)[0]
        print(byte)
        if byte == 1:
            return True
        else:
            return False

    def read_long(self):
        byte = b''
        for _ in range(8):
            byte += self.queue.pop(0)

        return struct.unpack('>q', byte)[0]

    def read_byte_array(self, size):
        byte = b''
        for _ in range(size):
            byte += self.queue.pop(0)

        return byte

    def read_uuid(self):
        byte = b''
        for _ in range(16):
            byte += self.queue.pop(0)

        val = struct.unpack('>QQ', byte)
        int_val = (val[0] << 64) + val[1]

        string_uuid = f"{int_val:x}"
        return string_uuid




    def readPacketC2S(self, data):
        # Add the bytes to the queue
        self.queue = []
        for byte in data:
            # For some reason looping over bytes gives you ints, so we convert
            # them back to bytes.
            self.queue.append(struct.pack('>B',byte))

        # Always read varint to get size of the packet
        packet_size = self.read_VarInt()
        packet_id = self.read_VarInt()
        print(f"Packet size: {packet_size}, Packet id: {packet_id}, Length of queue:{len(self.queue)}")

        if self.state == "handshake":
            if packet_id == 0: # Handshake packet
                self.state = "login"
                return dict([("packet_id", packet_id),
                             ("protocol", self.read_VarInt()),
                             ("server_addr", self.read_String()),
                             ("serverPort", self.read_uShort()),
                             ("NextState", self.read_VarInt())])

        if self.state == "login":
            if packet_id == 0: # Login start packet
                print(data)
                username = self.read_String()
                has_sig_data = self.read_bool()
                timestamp = None
                pub_key_len = None
                pub_key = None
                sig_len = None
                sig = None

                if has_sig_data is True:
                    timestamp = self.read_long()
                    pub_key_len = self.read_VarInt()
                    pub_key = self.read_byte_array(pub_key_len)
                    self.client_public_key = pub_key
                    sig_len = self.read_VarInt()
                    sig = self.read_byte_array(sig_len)

                has_uuid = self.read_bool()
                uuid = None
                if has_uuid is True:
                    uuid = self.read_uuid()

                return dict([("username", username),
                             ("has_sig_data", has_sig_data),
                             ("timestamp", timestamp),
                             ("pub_key_len", pub_key_len),
                             ("pub_key", pub_key),
                             ("sig_len", sig_len),
                             ("signature", sig),
                             ("has_uuid", has_uuid),
                             ("uuid", uuid),
                             ])



        # state login, login start.

    def readPacketS2C(self, data):
        pass

        return dict([])







