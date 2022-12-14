from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives import ciphers, serialization

# Inspired by https://github.com/barneygale/quarry/blob/master/quarry/net/crypto.py

class rsa_encryption:
    server_pub_key = None
    client_pub_key = None
    shared_secret = None

    def __init__(self):
        self.key_pair = rsa.generate_private_key(
            public_exponent=65537,
            key_size=1024,
            backend=default_backend()
        )


    def export_public_key(self):
        # Export the public key so we can send it in a packet.
        return self.key_pair.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def import_public_key(self, key):
        # Import public key of server or client in usable state.
        return serialization.load_der_public_key(
            data=key,
            backend=default_backend()
        )

    def import_server_pub(self, key):
        self.server_pub_key = self.import_public_key(key)

    def import_client_pub(self, key):
        self.client_pub_key = self.import_public_key(key)

    def decrypt_secret(self, secret):
        return self.key_pair.decrypt(
            ciphertext=secret,
            padding=padding.PKCS1v15()
        )

    def encrypt_secret(self, secret):
        return self.server_pub_key.encrypt(
            plaintext=secret,
            padding=padding.PKCS1v15()
        )


class aes_encryption: