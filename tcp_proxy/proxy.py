import sys
import socket
from multiprocessing import Process, Pipe
import struct
import math

from processByte import ByteProcessor

def downStreamReciever(connection, pipe, byteProcessor):
    while True:
        data = connection.recv(4096)
        if data:
            # print(f"Data recieved: {data}")
            print(byteProcessor.readPacketC2S(data))
            pipe.send(data)

def downStreamSender(connection, pipe):
    while True:
        data = pipe.recv()
        # print(f"Sending data to downstream: {data}")
        connection.sendall(data)


def downStream(addr, pipeUp, pipeDown, byteProcessor):
    # The connection to the client
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(addr)
    sock.listen()

    connection, client_adress = sock.accept()

    reciever = Process(target=downStreamReciever, args=(connection, pipeUp, byteProcessor))
    sender = Process(target=downStreamSender, args=(connection, pipeDown))
    reciever.start()
    sender.start()


def upStreamReciever(connection, pipe):
    while True:
        data = connection.recv(4096)
        if data:
            # print(f"Data recieved from upstream: {data}")
            pipe.send(data)

def upStreamSender(connection, pipe):
    while True:
        data = pipe.recv()
        # print(f"sending data to upstream: {data}")
        connection.sendall(data)

def upStream(addr, pipeUp, pipeDown):
    # The connection to the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)

    reciever = Process(target=upStreamReciever, args=(sock, pipeDown))
    sender = Process(target=upStreamSender, args=(sock, pipeUp))
    reciever.start()
    sender.start()

    reciever.join()


def main():
    # Create Pipes
    upPipeRecv, upPipeSend = Pipe()
    downPipeRecv, downPipeSend = Pipe()
    proxy_addr = ('127.0.0.1', 12345)
    mc_server_addr = ('127.0.0.1', 25565)

    byteProcessor = ByteProcessor()

    downStream(proxy_addr, upPipeSend, downPipeRecv, byteProcessor)
    upStream(mc_server_addr, upPipeRecv, downPipeSend)


if __name__ == "__main__":
    main()