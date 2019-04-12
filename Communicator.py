import socket
import time
from abc import abstractmethod


class Communicator:

    @abstractmethod
    def start(self):
        pass


def toPrintable(unpretty):
    result = ""
    for char in unpretty:
        if char == '\r':
            result += '<CR>'
        elif char == '\n':
            result += '<LF>'
        else:
            result += char
    return result


class SocketCommunicator(Communicator):

    def __init__(self, resp_function):
        self.port = 2049  # Vötsch standard port. According to Wikipedia, it's usually used for nfs.
        self.responseEOL = "\r"
        self.responseFunction = resp_function

    def start(self):
        # DONE: se till att avslutning fungerar snyggare, utan felmeddelanden till terminalen
        # DONE: Se till att en session kan startas direkt efter att föregående har brutits.

        HOST = ''  # Symbolic name meaning all available interfaces
        PORT = self.port
        print("port is ", PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(1)
            while True:
                conn, addr = s.accept()
                print('Connected by', addr, "\n")
                with conn:
                    self.serveForever(conn)
                print("Exited 'with conn'")

    # TODO: Make this work correctly for a real stream, not just strings ended by CRLF
    def serveForever(self, conn):
        loopCount = 0
        while True:
            data = conn.recv(1024) # TODO: Read one character at a time, and sum up the resulting string/list
            print("%d: '%s'" % (loopCount, data.decode('utf-8')))
            loopCount += 1
            try:
                receivedCommand = data.decode('utf-8')
            except UnicodeDecodeError:
                print("UnicodeDecodeError")
                continue
            receivedText = receivedCommand.strip()
            if not data:
                print(".", end='', flush=True)
                time.sleep(0.1)  # Sleep for 100 ms before continuing
                # TODO: See if there is a better way to wait for commands without choking the CPU.
                break
            print("Received: '%s'" % toPrintable(receivedText))
            r = self.responseFunction(data.decode('utf-8'))
            response = bytes(r + self.responseEOL,
                             'utf-8')  # At least Vötsch doesn't send LF after response string.
            # TODO: Use a configurable post-response string that can be overridden.

            # Don't send empty responses.
            if r:
                # TODO: Don't print embedded CR characters on the same lime as the length info.
                print("Sent:     '%s' (length: %d)" % (r.strip(), len(response)))
                print()
                conn.sendall(response)
