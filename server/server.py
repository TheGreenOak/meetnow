import socket


TCP = 1
UDP = 2


class Server:
    """
    A basic server interface that has basic I/O support.
    """

    def __init__(self, port, conn_type, capacity):
        self.port = port

        if conn_type != TCP and conn_type != UDP:
            raise ValueError("Invalid connection type")
        
        self.conn_type = conn_type
        self.capacity = capacity
        self.sock = None
        self.is_blocked = False
    
    def start(self):
        """
        Starts the server, and listens on the specified port.
        """

        # Figure out which socket type to use
        if self.conn_type == TCP:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif self.conn_type == UDP:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.sock.bind(('', self.port))
        self.sock.listen(self.capacity) # TODO: Fix UDP bug
        print("[!] Server started on port:", self.port)
    
    def toggle_blocking_mode(self):
        """
        Toggles the blocking mode of the server socket.
        """

        self.is_blocked = not self.is_blocked
        print("[!] Blocking mode has been toggled.")
    
    def accept(self):
        """
        Accepts a connection from the client.
        """

        return self.sock.accept()
    
    def send(self, conn, data):
        """
        Sends data to the client.
        """

        conn.send(data)
    
    def recv(self, conn):
        """
        Receives data from the client.
        """

        return conn.recv(1024)
    
    def stop(self):
        """
        Stops the server.
        """

        self.sock.close()
        self.sock.shutdown(socket.SHUT_RDWR)
        print("[!] Server stopped.")
        print("[!] Server has stopped.")


def main():
    print("Welcome to a basic I/O server.")

    print("Please enter the port you'd like to listen to: ", end="")
    port = int(input())

    print("Please enter the connection type: ", end="")
    conn_type = int(input())

    print("Please enter the capacity of the server: ", end="")
    capacity = int(input())

    server = Server(port, conn_type, capacity)
    server.start()

    try:
        client = server.accept()[0]
        host, port = client.getpeername()
        print("Client {}:{} has connected.".format(host, port))

        while True:
            data = server.recv(client).decode()
            print("[{}:{} -> Server] {}".format(host, port, data))
            print("[Server -> {}:{}] {}".format(host, port, data))
            server.send(client, data.encode())
    except KeyboardInterrupt:
        server.stop()
        print("[!] Server has stopped.")


if __name__ == "__main__":
    main()