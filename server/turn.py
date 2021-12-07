from server import UDPServer
from threading import Thread, Event
from json import loads as deserialize, dumps as serialize

SERVER_PORT = 3479 # # The TURN port exept for the last  - https://www.3cx.com/blog/voip-howto/stun-voip-1/

class Turn(UDPServer):
    """
    The TURN server is responsible for connecting two users that can't communicate through P2P.
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
            self.keep_running = False

            print("\nStopping server...")
            self.stop()


def main():
    server = Turn(SERVER_PORT)
    server.start()
    server.toggle_blocking_mode()

    print("TURN server started")
    server.run() # Blocking method - will continue running until the admin presses Ctrl+C

    print("\nStopping server...")
    server.stop()

if __name__ == "__main__":
    main()