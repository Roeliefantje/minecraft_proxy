import json
from xmlrpc.client import ProtocolError
import requests
from twisted.python import failure

from twisted.internet import reactor
from quarry.types.uuid import UUID
from quarry.net.proxy import UpstreamFactory, Upstream, DownstreamFactory, Downstream, Bridge
from quarry.net import auth, crypto
from twisted.internet import reactor


class MyUpstream(Upstream):
    def packet_login_encryption_request(self, buff):
        p_server_id = buff.unpack_string()

        # 1.7.x
        if self.protocol_version <= 5:
            def unpack_array(b): return b.read(b.unpack('h'))
        # 1.8.x
        else:
            def unpack_array(b): return b.read(b.unpack_varint(max_bits=16))

        p_public_key = unpack_array(buff)
        p_verify_token = unpack_array(buff)

        if not self.factory.profile.online:
            raise ProtocolError("Can't log into online-mode server while using"
                                " offline profile")

        self.shared_secret = crypto.make_shared_secret()
        self.public_key = crypto.import_public_key(p_public_key)
        self.verify_token = p_verify_token

        # make digest
        digest = crypto.make_digest(
            p_server_id.encode('ascii'),
            self.shared_secret,
            p_public_key)

        # do auth
        # deferred = self.factory.profile.join(digest)
        # deferred.addCallbacks(self.auth_ok, self.auth_failed)

        url = "https://sessionserver.mojang.com/session/minecraft/join"

        payload = json.dumps({
            "accessToken": self.factory.profile.access_token,
            "selectedProfile": self.factory.profile.uuid.to_hex(False),
            "serverId": digest
        })
        headers = {
            'Content-Type': 'application/json'
        }

        r = requests.request(
            "POST", "https://sessionserver.mojang.com/session/minecraft/join", headers=headers, data=payload)

        if r.status_code == 204:
            self.auth_ok(r.text)
        else:
            self.auth_failed(failure.Failure(
                auth.AuthException('unverified', 'unverified username')))


class MyDownstream(Downstream):
    def packet_login_encryption_response(self, buff):
        if self.login_expecting != 1:
            raise ProtocolError("Out-of-order login")

        # 1.7.x
        if self.protocol_version <= 5:
            def unpack_array(b): return b.read(b.unpack('h'))
        # 1.8.x
        else:
            def unpack_array(b): return b.read(b.unpack_varint(max_bits=16))

        p_shared_secret = unpack_array(buff)
        p_verify_token = unpack_array(buff)

        shared_secret = crypto.decrypt_secret(
            self.factory.keypair,
            p_shared_secret)

        verify_token = crypto.decrypt_secret(
            self.factory.keypair,
            p_verify_token)

        self.login_expecting = None

        if verify_token != self.verify_token:
            raise ProtocolError("Verify token incorrect")

        # enable encryption
        self.cipher.enable(shared_secret)
        self.logger.debug("Encryption enabled")

        # make digest
        digest = crypto.make_digest(
            self.server_id.encode('ascii'),
            shared_secret,
            self.factory.public_key)

        # do auth
        remote_host = None
        if self.factory.prevent_proxy_connections:
            remote_host = self.remote_addr.host

        # deferred = auth.has_joined(
        #     self.factory.auth_timeout,
        #     digest,
        #     self.display_name,
        #     remote_host)
        # deferred.addCallbacks(self.auth_ok, self.auth_failed)

        r = requests.get('https://sessionserver.mojang.com/session/minecraft/hasJoined',
                         params={'username': self.display_name, 'serverId': digest, 'ip': remote_host})

        if r.status_code == 200:
            self.auth_ok(r.json())
        else:
            self.auth_failed(failure.Failure(
                auth.AuthException('invalid', 'invalid session')))


class MyUpstreamFactory(UpstreamFactory):
    protocol = MyUpstream

    connection_timeout = 10


class MyBridge(Bridge):
    upstream_factory_class = MyUpstreamFactory

    def make_profile(self):
        """
        Support online mode
        """

        # follow: https://kqzz.github.io/mc-bearer-token/

        accessToken = 'eyJhbGciOiJIUzI1NiJ9.eyJ4dWlkIjoiMjUzNTQwNTYyNTM4NzUxNiIsImFnZyI6IkFkdWx0Iiwic3ViIjoiOTEzYTY3MWUtYjk2NC00YzRkLTk5MmUtYmRjYTk2MjE1MGZmIiwibmJmIjoxNjcwNDQ1MjEzLCJhdXRoIjoiWEJPWCIsInJvbGVzIjpbXSwiaXNzIjoiYXV0aGVudGljYXRpb24iLCJleHAiOjE2NzA1MzE2MTMsImlhdCI6MTY3MDQ0NTIxMywicGxhdGZvcm0iOiJVTktOT1dOIiwieXVpZCI6IjRhOGM4N2EyODM5NzkyYTllZDBiNGRiMmZmYTViODI2In0.tS-7ZsGzB5qIju5wRdWHQkZ51gJreB84TyWqts8HotE'

        url = "https://api.minecraftservices.com/minecraft/profile"
        headers = {'Authorization': 'Bearer ' + accessToken}
        response = requests.request("GET", url, headers=headers)
        result = response.json()
        myUuid = UUID.from_hex(result['id'])
        myUsername = result['name']
        return auth.Profile('(skip)', accessToken, myUsername, myUuid)


class MyDownstreamFactory(DownstreamFactory):
    protocol = MyDownstream
    bridge_class = MyBridge
    motd = "Proxy Server"


def main(argv):
    # Parse options
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a1", "--listen-host1", default="127.0.0.1", help="address to listen on")
    parser.add_argument("-p1", "--listen-port1", default=12345, type=int, help="port to listen on")
    parser.add_argument("-b", "--connect-host", default="hypixel.net", help="address to connect to")
    parser.add_argument("-q", "--connect-port", default=25565, type=int, help="port to connect to")
    args = parser.parse_args(argv)

    # Create factory
    factory = MyDownstreamFactory()
    factory.connect_host = args.connect_host
    factory.connect_port = args.connect_port

    # Listen
    factory.listen(args.listen_host1, args.listen_port1)
    reactor.run()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])