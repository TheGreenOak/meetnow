import socket
import threading


TCP = 1
UDP = 2


class Connection:
    """
    A simple class that acts as a basic input/output tester for any server.

    Supports source ports, TCP and UDP.
    """

    def __init__(self, ip, sport, dport, type):
        self.ip = ip
        self.sport = sport
        self.dport = dport
        self.type = type
        self.sock = None
        self.keep_running = True

    def connect(self):
        """
        Attempts to connect to the server.

        Error handling is not implemented. You're on your own.
        """
        if self.type == TCP:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Set up TCP socket
        elif self.type == UDP:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Set up UDP socket

        self.sock.bind(("0.0.0.0", self.sport)) # Set up source port
        self.sock.connect((self.ip, self.dport)) # Connect to the server

    def send(self, data):
        self.sock.send(data.encode())

    def recv(self, size):
        return self.sock.recv(size).decode()
    
    def close(self):
        self.sock.close()


def sendContinously(conn):
    while True:
        conn.send(input(""))


def recvContinously(conn):
    try:
        while conn.keep_running:
            print("[SERVER]", conn.recv(1024))
    except ConnectionResetError:
        print("Server aborted connection.")


def main():
    print("Welcome to the basic server tester.")

    print("Please enter the IP address of the server you want to connect to: ", end="")
    ip = input("")
    print()

    print("Please enter the port number you'd like to connect from: ", end="")
    sport = int(input(""))
    print()

    print("Please enter the port number of the server you want to connect to: ", end="")
    dport = int(input(""))
    print()

    print("1 - TCP")
    print("2 - UDP")
    print("Please enter the type of connection you want to test: ", end="")
    connType = int(input(""))
    print()

    conn = Connection(ip, sport, dport, connType)

    try:
        conn.connect()
        print("Connection established.")

        # We make a new thread for receiving data from the server without interrupting the main thread
        recvThread = threading.Thread(target=recvContinously, args=(conn,))
        recvThread.start()

        try:
            sendContinously(conn)
        except KeyboardInterrupt:
            conn.keep_running = False
            recvThread.join()
        
        conn.close()
        print("Connection closed.")
    except TimeoutError:
        print("Couldn't connect to server. Aborting!")
    except ConnectionRefusedError:
        print("Connection refused. Aborting!")


if __name__ == "__main__":
    main()
