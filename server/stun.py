from server import UDPServer
import socket

SERVER_PORT = 11111

class Stun(UDPServer):
    """
    The stun server is responsible for telling the user his ip.
    In addition to the ip the server tells the user if his NAT is allowing P2P.
    """

    def __init__(self, port):
        super().__init__(port)

    
    def run(self):
        try:
            while True:
                try:
                    # In UDP, there are no sockets. Therefore, we just need to receive data.
                    data, address = self.recv()
                    print("[{}:{}] {}".format(address[0], address[1], data.decode()))
                    self.send(address, data)
                except BlockingIOError:
                    pass
        except KeyboardInterrupt:
            server.keep_running = False

            print("\nStopping server...")
            server.stop()


def main():
    server = Stun(SERVER_PORT)
    server.start()
    server.toggle_blocking_mode()

    print("STUN server started")
    server.run()
    #server.run() # Blocking method - will continue running until the admin presses Ctrl+C
    print("The user's ip is: " + str(ip) + ", the user's port is: " + str(port))

    print("\nStopping server...")
    server.stop()

if __name__ == "__main__":
    main()