from server import TCPServer
from database.redisdb import RedisDictDB
from threading import Thread, Event
from json import loads as deserialize, dumps as serialize


import socket
import traceback


# Constants
SERVER_PORT = 1673 # I and E are in 1 and 3 in Leet speech. C = 67 in the ASCII table.
                   # TL;DR we didn't find the "normal" ICE port lol

MINUTE = 60
USER_TTL_MESSAGES = 2
MAX_MESSAGE_LENGTH = 128


class InvalidRequest(Exception):
    reason = "Invalid request"


class WaitingForPeer(Exception):
    reason = "You're waiting for a peer"


class AlreadyPaired(Exception):
    reason = "You already have a connected peer"


class NotConnected(Exception):
    reason = "You're not connected"


class MeetingFull(Exception):
    reason = "This meeting is full"


class InvalidMeetingID(Exception):
    reason = "An invalid meeting ID was entered"


class InvalidPassword(Exception):
    reason = "The password for this meeting is incorrect"


class InvalidUser(Exception):
    reason = "This IP address is not connected to this meeting via the Signaling service"


class PeerMessage(Exception):
    pass


class ICE(TCPServer):
    """
    [ SERVER INFORMATION ]
    The ICE (Internet Connectivity Establishment) server is responsible for temporarily connecting
    both clients, and transporting ICE messages between them. This is done so that the clients
    will be able communicate with each other by synchronizing communication ports and IP addresses.

    [ DATABASE INFORMATION ]
    The ICE server maintains two internal databases, and has read access for the public one.
    The two internal databases are used mainly for checking request validity.

    [self.users]
    (ip, port): {
        ttl: int,
        socket: socket object,
        id: str [optional]
    }

    [self.connections]
    "meeting id": [(ip, port), (ip, port)]

    [self.public_db]
    "meeting id": {
        password: str,
        participants: [ip, ip]
    }
    """

    def __init__(self, port, public_db):
        super().__init__(port)

        # Setup the databases needed
        self.users = {}
        self.connections = {}

        self.public_db = public_db

        self.expiry_stopper = Event()
    

    def connect_peer(self, user_uuid, meeting_id, password):
        """
        This method attempts to connect a user to another user.
        If all parameters are correct but there's no other user, the user will be put on hold.

        Parameters:
        user_uuid (any): Address tuple or other unique identifier.
        meeting_id (str): The ID of the meeting.
        password (str): The password of the meeting.

        Returns:
        socket | None: The other user's socket.
        """

        # Get the user
        user = self.users[user_uuid]
        other_user = None

        # If the user is already connected, they will receive an error.
        # We just want to see which error they should receive.
        if user.get("id"):
            connection = self.connections[user["id"]]

            if len(connection) > 1:
                raise AlreadyPaired
            else:
                raise WaitingForPeer
        
        # However, if the user isn't connected, we need to perform additional checks.
        else:
            # Check if the meeting ID is valid
            if self.public_db[meeting_id] is None:
                raise InvalidMeetingID
            
            # Check if the password is correct
            if self.public_db[meeting_id]["password"] != password:
                raise InvalidPassword
            
            # Check if the user can connect
            if user_uuid[0] not in deserialize(self.public_db[meeting_id]["participants"]):
                raise InvalidUser

            # Lastly, check if the connection is already utilized
            if self.connections.get(meeting_id) and len(self.connections[meeting_id]) > 1:
                raise MeetingFull
            
            
        # -- The user can connect to this meeting -- #

        # If another user is waiting
        if self.connections.get(meeting_id):
            self.connections[meeting_id].append(user_uuid)
            other_user = self.users[self.connections[meeting_id][0]]["socket"]
        else:
            self.connections[meeting_id] = [user_uuid]
        
        # Mark this user as connected
        user["id"] = meeting_id

        return other_user
    
    def get_peer(self, user_uuid):
        """
        This method is responsible for getting a user's peer

        Parameters:
        user_uuid (any): Tuple address or other unique identifier.

        Returns:
        socket: The peer's socket
        """

        # Get the user
        user = self.users[user_uuid]
        user_index = None
        
        connection = None
        peer = None
        
        # Check if the user is connected
        if not user.get("id"):
            raise NotConnected
        
        # Check if the user is waiting for a peer
        if len(self.connections[user["id"]]) == 1:
            raise WaitingForPeer
        

        # -- The user has another peer -- #

        # Get the connection
        connection = self.connections[user["id"]]

        # Determine the peer
        user_index = connection.index(user_uuid)
        peer = connection[user_index ^ 1] # XOR shortcut

        # Return the peer's socket
        return self.users[peer]["socket"]
    

    def disconnect_peer(self, user_uuid):
        """
        This method is responsible for disconnecting a user from another user.

        Parameters:
        user_uuid (any): Tuple address or other unique identifier.

        Returns:
        tuple | None: The remaining user's address and socket.
        """
        
        # Get the user
        user = self.users[user_uuid]
        user_index = None

        connection = None
        other_user = None
        other_user_address = None

        # Check if the user is connected
        if not user.get("id"):
            raise NotConnected
        
        # -- The user can disconnect -- #

        # Get the connection
        connection = self.connections[user["id"]]

        # Determine if we have another peer
        if len(connection) > 1:
            user_index = connection.index(user_uuid)
            other_user_address = connection[user_index ^ 1] # XOR shortcut
            other_user = self.users[other_user_address]
        
        # Remove the user from the connection
        connection.remove(user_uuid)

        # If there's no other peer, remove the connection
        if not other_user:
            del self.connections[user["id"]]
        
        # Mark the user as disconnected
        del user["id"]

        if other_user:
            return other_user_address, other_user


    def disconnect_client(self, address):
        """
        This method is responsible for removing a client from the database, and disconnecting their socket.

        No checks are performed to ensure that the client is in the database.
        Call this method only after checking that the client is in the database.

        address (tuple): Address tuple or other unique identifier.

        Returns:
        bool: Whether or not another client was disconnected
        """

        # Setup temporary variables
        user = self.users[address]
        client = user["socket"]

        second_user = None
        second_user_sock = None

        # If the user disconnects in a meeting, remove them from the meeting
        if user.get("id"):
            second_user = self.disconnect_peer(address)
            if second_user: # Unpack the tuple safely
                second_user, second_user_sock = second_user
        
        del self.users[address]
        
        # Disconnect the socket
        try:
            client.shutdown(socket.SHUT_RDWR)
            client.close()
        except OSError: pass
        
        print("[DISCONNECTED] {}:{}".format(address[0], address[1]))

        try:
            if second_user_sock:
                second_user_sock.send(serialize({"response": "info", "type": "left"}).encode())
        except BrokenPipeError:
            self.disconnect_client(second_user)
            return True
        
        return False
    

    def user_cleaner(self):
        """
        This method is responsible for checking the user's TTL, and will send a heartbeat every minute.
        If the user's TTL is 0, they will be disconnected.

        Works similary to meeting_cleaner.
        """

        # We want to run this worker until the server stops, at which point
        # this event will get set.
        while not self.expiry_stopper.is_set():
            counter = 0

            for user_uuid, user in self.users.copy().items():
                if user["ttl"] <= 0: # The user has probably disconnected
                    self.disconnect_client(user_uuid)
                    counter += 1
                else:
                    try:
                        user["ttl"] = user["ttl"] - 1
                        user["socket"].send(b"HEARTBEAT")
                    except BrokenPipeError: # User has disconnected abruptly.
                        if self.disconnect_client(user_uuid):
                            counter += 2
                        else:
                            counter += 1

            if counter > 0:
                print("[EXPIRY WORKER] Disconnected {} client{}".format(counter, 's' if counter > 1 else ''))

            self.expiry_stopper.wait(MINUTE) # We put this function to "sleep" that can be awoken


    def user_handler(self):
        """
        A thread for handling all the users currently connected.
        This is done so to eliminate the need for a thread for each user.
        """

        # We want to run this thread until the server stops
        while self.keep_running:

            # Iterate through all the connected users
            for address, user in self.users.copy().items():
                try:

                    # Attempt receiving a message
                    data = user["socket"].recv(MAX_MESSAGE_LENGTH)

                    if not data:  # The user has disconnected
                        self.disconnect_client(address)
                        continue
                        
                    # We got a message! Forward it to the handler, and try sending responses
                    try:
                        for sock, message in self.handle_message(address, user["socket"], data.decode()):
                            sock.send(message.encode())
                    except:
                        # An unknown error has occurred
                        print("CRITICAL: An unknown error has occurred.")
                        print("Client: {}:{}".format(address[0], address[1]))
                        print("Message: {}".format(data.decode()))
                        print(traceback.format_exc())

                        user["socket"].send(serialize({"response": "error", "reason": "An unknown error occurred"}).encode())
                except BlockingIOError:
                    pass

                except (ConnectionError, OSError):
                    self.disconnect_client(address)


    def handle_message(self, addr, sock, message):
        """
        Handles all requests from the client.
        Returns the messages that need to be sent to each client after the request.

        Parameters:
        addr (tuple): The client's IP and port
        sock (socket): The client's socket

        Returns:
        list: A list of tuples with the messages needed to be sent to each socket.
        """

        responses = []

        try:
            self.users[addr]["ttl"] = USER_TTL_MESSAGES # If we received a message from the user, they're alive.

            if message == "HEARTBEAT":
                return [] # No need to return a message

            try:
                request = deserialize(message)
                if type(request) is not dict:
                    raise Exception
            except:
                peer = self.get_peer(addr)
                responses.append((peer, "C" + message))
                raise PeerMessage
                
            if not request.get("request"):
                raise InvalidRequest

            if request["request"] == "connect":
                if not request.get("id") or not request.get("password"):
                    raise InvalidRequest
                
                other_peer = self.connect_peer(addr, request["id"], request["password"])
                if other_peer:
                    responses.append((sock, serialize({"response": "success", "waiting": False})))
                    responses.append((other_peer, serialize({"response": "info", "type": "connected"})))
                else:
                    responses.append((sock, serialize({"response": "success", "waiting": True})))
            
            elif request["request"] == "disconnect":
                other_peer = self.disconnect_peer(addr)
                responses.append((sock, serialize({"response": "success"})))
                if other_peer:
                    responses.append((other_peer[1], serialize({"response": "info", "type": "disconnected"})))

            else:
                raise InvalidRequest

        except PeerMessage: pass
        except Exception as e:
            responses.append((sock, serialize({"response": "error", "reason": e.reason})))
        
        return responses


    def run(self):
        # Worker thread list
        threads = [Thread(target=self.user_cleaner), Thread(target=self.user_handler)]

        try:
            # Start the threads
            for worker in threads: worker.start()

            # Accept new clients and handle them
            while True:
                try:
                    client, address = self.accept()
                    client.setblocking(False)
                    self.users[address] = {"ttl": USER_TTL_MESSAGES, "socket": client} # Insert the user to the database
                    print("[CONNECTED] {}:{}".format(address[0], address[1]))
                except BlockingIOError:
                    pass
        except KeyboardInterrupt:
            self.keep_running = False
            self.expiry_stopper.set()

            # Safely wait for all threads to end
            for thread in threads:
                thread.join()


def main():
    # Connect to the public database
    try:
        public_db = RedisDictDB("meetings")
    except:
        print("Could not connect to the Redis Database.")
        print("Please make sure that Redis is running on the local machine with the default parameters.")
        exit(1)

    server = ICE(SERVER_PORT, public_db)
    server.start()
    server.toggle_blocking_mode()
    
    try:
        print("ICE server started")
        server.run() # Blocking method - will continue running until the admin presses Ctrl+C
    except: pass

    print("\nStopping server...")
    server.stop()


if __name__ == "__main__":
    main()
