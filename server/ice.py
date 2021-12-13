from server import TCPServer


# Constants
SERVER_PORT = 1673 # I and E are in 1 and 3 in Leet speech. C = 67 in the ASCII table.
                   # TL;DR we didn't find the "normal" ICE port lol


class ICE(TCPServer):
    """
    The ICE (Internet Connectivity Establishment) server is responsible for temporarily connecting
    both clients, and transporting ICE messages between them. This is done so that the clients
    will be able communicate with each other by synchronizing communication ports and IP addresses.
    """

    def __init__(self, port):
        super().__init__(port)


def main():
    server = ICE(SERVER_PORT)
    server.start()
    
    print("Signaling server started")
    # TODO: server.run() 

    print("\nStopping server...")
    server.stop()


if __name__ == "__main__":
    main()
