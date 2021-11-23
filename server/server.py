import socket
import json
from threading import Thread


TCP = 1
UDP = 2


class TCPServer:
    def __init__(self, port):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_blocked = True
        self.keep_running = True


    def toggle_blocking_mode(self):
        """
        Toggles the blocking mode of the server socket.
        """
        self.is_blocked = not self.is_blocked
        self.socket.setblocking(self.is_blocked)

    def start(self):
        """
        Starts the server.
        """
        self.socket.bind(("", self.port))
        self.socket.listen()

    def accept(self):
        """
        Accepts a new client.
        """
        return self.socket.accept()

    def recv(self, client, size):
        """
        Receives data from a client.
        """

        return client.recv(size)

    def send(self, client, data):
        """
        Sends data to a client.
        """
        client.send(data)

    def stop(self):
        """
        Stops the server.
        """
        self.socket.close()


class UDPServer:
    def __init__(self, port):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.is_blocked = True


    def toggle_blocking_mode(self):
        """
        Toggles the blocking mode of the server socket.
        """
        self.is_blocked = not self.is_blocked
        self.socket.setblocking(self.is_blocked)

    def start(self):
        """
        Starts the server.
        """
        self.socket.bind(("", self.port))

    def recv(self, size):
        """
        Receives data from a client.
        """
        return self.socket.recvfrom(size)

    def send(self, address, data):
        """
        Sends data to a client.
        """
        self.socket.sendto(data, address)

    def stop(self):
        """
        Stops the server.
        """
        self.socket.close()


def serialize(data):
    """
    Serializes a data object into a JSON string.
    Error handling is not implemented. You're on your own.
    """
    return json.dumps(data)


def deserialize(data):
    """
    Deserializes a JSON string into a data object.
    Error handling is not implemented. You're on your own.
    """
    return json.loads(data)


def handle_tcp_client(server, client, address):
    """
    Handles a TCP client.
    """

    try:
        while server.keep_running:
            try:
                data = server.recv(client, 1024)
                if not data:
                    break

                print("[{}:{}] {}".format(address[0], address[1], data.decode()))
                server.send(client, data)
            except BlockingIOError:
                pass
    except:
        pass
    finally:
        print("[DISCONNECTED] {}:{}".format(address[0], address[1]))
        client.close()


def main():
    print("Welcome to a basic I/O server.")

    print("Please enter the port you'd like to listen to: ", end="")
    port = int(input())

    print("1 - TCP")
    print("2 - UDP")
    print("Please enter the connection type: ", end="")
    conn_type = int(input())

    if conn_type == TCP:
        server = TCPServer(port)
    elif conn_type == UDP:
        server = UDPServer(port)
    else:
        raise ValueError("Invalid connection type.")
    
    server.start()
    server.toggle_blocking_mode() # We want to be able to stop the server at any time.
    print("Server started. Listening on port", port)

    # Store the client threads in a list so we can later join them.
    TCP_threads = []

    try:
        if conn_type == TCP:
            while True:
                try:
                    client, address = server.accept()
                    print("[CONNECTED] {}:{}".format(address[0], address[1]))

                    # Make a new thread to handle the client, and store it in the list.
                    client_thread = Thread(target=handle_tcp_client, args=(server, client, address))
                    client_thread.start()
                    TCP_threads.append(client_thread)
                except BlockingIOError:
                    pass
        elif conn_type == UDP:
            while True:
                try:
                    # In UDP, there are no sockets. Therefore, we just need to receive data.
                    data, address = server.recv(1024)
                    print("[{}:{}] {}".format(address[0], address[1], data.decode()))
                    server.send(address, data)
                except BlockingIOError:
                    pass
    except KeyboardInterrupt:
        server.keep_running = False

        for thread in TCP_threads:
            thread.join()

        print("\nStopping server...")
        server.stop()


if __name__ == "__main__":
    main()