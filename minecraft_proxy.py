from quarry.net.proxy import DownstreamFactory, Bridge
from twisted.internet import reactor


class PacketBridge(Bridge):
    verbose = False

    def packet_upstream_chat_command(self, buff):
        buff.save()
        message = buff.unpack_string()

        if message == "verbose":
            self.verbose = not self.verbose
            buff.discard()
        else:
            buff.restore()
            self.upstream.send_packet("chat_command", buff.read())

    def packet_unhandled(self, buff, direction, name):
        if self.verbose:
            print(f"[*][{direction}] {name}")

        if direction == "downstream":
            self.downstream.send_packet(name, buff.read())
        elif direction == "upstream":
            self.upstream.send_packet(name, buff.read())

    # def packet_upstream_player_position(self, buff):



class QuietDownStreamFactory(DownstreamFactory):
    bridge_class = PacketBridge
    motd = "Roeliefantje Proxy"
    online_mode=False

def main(argv):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--listen-host", default="127.0.0.1", help="address to listen on")
    parser.add_argument("-p", "--listen-port", default=12345, type=int, help="port to listen on")
    parser.add_argument("-b", "--connect-host", default="192.168.2.10", help="address to connect to")
    parser.add_argument("-q", "--connect-port", default=25565, type=int, help="port to connect to")
    args = parser.parse_args(argv)

    factory = QuietDownStreamFactory()
    factory.connect_host = args.connect_host
    factory.connect_port = args.connect_port

    factory.listen(args.listen_host, args.listen_port)
    reactor.run()

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
