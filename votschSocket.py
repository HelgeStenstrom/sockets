#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Fungerar i python3.

# From https://docs.python.org/3/library/socket.html#example


# Echo server program
import socket

class vötschFake:
    def __init__(self):
        self.temp = 27.1

    def setTempActual(self, temp):
        self.temp = temp

    def format(self, x):
        return "%06.1f " % x

    def responseFunction(self, command):
        command = command.strip()
        if command.startswith("$01I"):
            response = self.format(self.temp) + "0019.7 " + 14 * "0000.1 " + 32 * "0" + "\r"
            return response
        elif command.startswith("$01?"):
            return "ASCII description of the protocol"
        elif command.startswith("$01E"):
            #print("Received command '", command[:-1], "'\n")
            return ""
        else:
            return "'" + command + "' is an unknown command."




def main():
    HOST = ''  # Symbolic name meaning all available interfaces
    PORT = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr, "\n")
            while True:
                data = conn.recv(1024)
                receivedCommand = data.decode('utf-8')
                print("Received: ", receivedCommand.strip(), "")
                if not data: break
                response = bytes(vötschFake().responseFunction(data.decode('utf-8'))+'\r', 'utf-8')
                conn.sendall(response)

    print("Socket is shut down or closed. Please restart.")


if __name__ == '__main__':
    main()

            
