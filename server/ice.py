from server import TCPServer
from database.redisdb import RedisDictDB
from threading import Thread, Event


# Constants
SERVER_PORT = 1673 # I and E are in 1 and 3 in Leet speech. C = 67 in the ASCII table.
                   # TL;DR we didn't find the "normal" ICE port lol


class ICE(TCPServer):
    """
    The ICE (Internet Connectivity Establishment) server is responsible for temporarily connecting
    both clients, and transporting ICE messages between them. This is done so that the clients
    will be able communicate with each other by synchronizing communication ports and IP addresses.
    """

    def __init__(self, port, public_db):
        super().__init__(port)

        # Setup the databases needed
        self.users = {}
        self.public_db = public_db

        self.expiry_stopper = Event()


def main():
    # Connect to the public database
    try:
        public_db = RedisDictDB("meetings")
    except RuntimeError:
        print("Could not connect to the Redis Database.")
        print("Please make sure that Redis is running on the local machine with the default parameters.")
        exit(1)

    server = ICE(SERVER_PORT, public_db)
    server.start()
    server.toggle_blocking_mode()
    
    print("Signaling server started")
    server.run() # Blocking method - will continue running until the admin presses Ctrl+C

    print("\nStopping server...")
    server.stop()


if __name__ == "__main__":
    main()
