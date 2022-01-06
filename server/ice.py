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
            other_user = self.connections[meeting_id][0]
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
        user_index = 0
        
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
        user_index = connection.index(user)
        peer = connection[user_index ^ 1] # XOR shortcut

        # Return the peer's socket
        return self.users[peer]["socket"]

    """
    ICE Server User Commands
    [REQUEST]

    connect:
    requires(ID[str], Password[str]);

    send:
    requires(Message[str]);

    disconnect:
    requires(None)


    [RESPONSE]
    connected:
    params(waiting)
    ["response": "success", "waiting": {bool}]

    error:
    params(reason)
    ["response": "error", "reason": {str}]

    info:
    connected
    ["response": "info", "type": "connected"]

    message
    ["response": "message", "content": [ICE Protocol]]
    """

    """
    ICE User Control Protocol

    [P2P Exchange]
    IP[IP Address]
    PORT[Port Number]
    
    ACCEPT
    REJECT

    [NO P2P Exchange]
    TURN

    ACCEPT
    REJECT

    [Call Demo] [Data is binary]
    A: IP10.0.0.127
    B: ACCEPT
    B: IP10.0.0.172
    A: ACCEPT

    A: PORT2833
    B: ACCEPT
    B: PORT9283
    A: ACCEPT/REJECT
    B: PORT2332
    A: ACCEPT

    // -- //
    A: IP10.0.0.127
    B: TURN
    A: ACCEPT/REJECT

    """


    def disconnect_client(self, address):
        """
        This method is responsible for removing a client from the database, and disconnecting their socket.

        No checks are performed to ensure that the client is in the database.
        Call this method only after checking that the client is in the database.

        address (tuple): Address tuple or other unique identifier.

        returns: tuple | None: The message that needs to be sent to the socket (both in tuple).
        """

        # Setup temporary variables
        user = self.users[address]
        client = user["socket"]
        second_user = None

        # If the user disconnects in a meeting, remove them from the meeting
        if user.get("id"):
            second_user = self.leave_meeting(address)
        
        del self.users[address]
        
        # Disconnect the socket
        client.shutdown(socket.SHUT_RDWR)
        client.close()
        print("[DISCONNECTED] {}:{}".format(address[0], address[1]))

        if second_user:
            return (second_user, serialize({"response": "info", "type": "left"}))
    

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
                    user["ttl"] = user["ttl"] - 1
                    user["socket"].send(b"HEARTBEAT")

            if counter > 0:
                print("[EXPIRY WORKER] Disconnected {} client{}".format(counter, 's' if counter > 1 else ''))

            self.expiry_stopper.wait(MINUTE) # We put this function to "sleep" that can be awoken


    def handle_client(self, client, address):
        """
        A thread for handling a Signaling client.

        Parameters:
        client (socket): The client's socket.
        address (tuple): The client's address.
        """

        try:
            # We want to run until the server is forcefully shut down
            while self.keep_running:
                try:
                    data = client.recv(MAX_MESSAGE_LENGTH)
                    if not data:
                        break

                    # Forward the message to the handler, and send all the responses to the respective clients
                    for sock, message in self.handle_message(address, client, data.decode()):
                        sock.send(message.encode())
                except BlockingIOError:
                    pass
        except (ConnectionError, OSError):
            pass
        except:
            # An unknown error has occurred
            print("CRITICAL: An unknown error has occurred.")
            print("Client: {}:{}".format(address[0], address[1]))
            print("Message: {}".format(data.decode()))
            print(traceback.format_exc())

            client.send(serialize({"response": "error", "reason": "An unknown error occurred"}).encode())
            
        finally:
            if self.users.get(address):
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
            except:
                raise InvalidRequest
                
            if not request.get("request"):
                raise InvalidRequest

            if request["request"] == "connect":
                if not request.get("id") or not request.get("password"):
                    raise InvalidRequest
                
                other_client = self.connect_peer(addr, request["id"], request["password"])
                if other_client:
                    responses.append((sock, serialize({"response": "success", "waiting": False})))
                    responses.append((other_client, serialize({"response": "info", "type": "connected"})))
                else:
                    responses.append((sock, serialize({"response": "success", "waiting": False})))
            
            elif request["request"] == "send":
                if not request.get("message"):
                    raise InvalidRequest
                
                peer = self.get_peer(addr)
                responses.append((sock, serialize({"response": "success", "message": "Sent your message!"})))
                responses.append((peer, serialize({"response": "message", "content": message})))

            elif request["request"] == "disconnect":
                remaining_user = self.disconnect_peer(addr)
                responses.append((sock, serialize({"response": "success"})))
                if remaining_user:
                    responses.append((remaining_user, serialize({"response": "info", "type": "disconnected"})))

            else:
                raise InvalidRequest

        except Exception as e:
            responses.append((sock, serialize({"response": "error", "reason": e.reason})))
        
        return responses
    

    def run(self):
        threads = []

        try:
            # Create an expiration worker thread
            expiry_worker = Thread(target=self.user_cleaner)
            expiry_worker.start()
            threads.append(expiry_worker)

            # Accept new clients and handle them
            while True:
                try:
                    client, address = self.accept()
                    self.users[address] = {"ttl": USER_TTL_MESSAGES, "socket": client, "status": "disconnected"}
                    print("[CONNECTED] {}:{}".format(address[0], address[1]))

                    # Make a new thread to handle the client
                    client_thread = Thread(target=self.handle_client, args=(client, address)) # TODO: make this single-threaded
                    client_thread.start()
                    threads.append(client_thread)
                except BlockingIOError:
                    pass
        except KeyboardInterrupt:
            self.keep_running = False
            self.expiry_stopper.set()

            for thread in threads:
                thread.join()


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
