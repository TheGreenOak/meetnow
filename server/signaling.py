from server import TCPServer
from threading import Thread, Event
from json import loads as deserialize, dumps as serialize
from uuid import uuid4 as generate_uuid
from database.redisdb import RedisDictDB

import secrets   # Cryptographically secure way to randomly choose
import string    # For easy access to ASCII characters
import traceback # Error reporting
import socket    # Socket logic


# Constants
MAX_MESSAGE_LENGTH = 128
MAX_PARTICIPANTS = 2

EMPTY_MEETING_EXPIRY = 5 # In minutes | Serves as TTL for the meeting
USER_TTL_MESSAGES = 2    # How many heartbeats to send before logging out the user

PASSWORD_LENGTH = 12
MEETING_ID_LENGTH = 9
MINUTE = 60

SOCK_INDEX = 0
MSG_INDEX = 1

SERVER_PORT = 5060


class InvalidRequest(Exception):
    reason = "Invalid request"


class AlreadyCreated(Exception):
    reason = "You've already created a meeting recently"


class InMeeting(Exception):
    reason = "You're already in a meeting"


class NotInMeeting(Exception):
    reason = "You're not in a meeting"


class InvalidMeetingID(Exception):
    reason = "An invalid meeting ID was entered"


class InvalidPassword(Exception):
    reason = "The password for this meeting is incorrect"


class MeetingFull(Exception):
    reason = "This meeting is full"


class AloneInMeeting(Exception):
    reason = "You're alone in this meeting"


class InsufficientPermissions(Exception):
    reason = "Insufficient permissions"


class Signaling(TCPServer):
    """
    [ SERVER INFORMATION ]
    The Signaling server is responsible for creating and assigning ID's to meetings.
    The server will be based on our basic TCP server.

    The point of it is to connect clients together. It does not have any other responsibilities,
    and does not care what happens to the clients beyond connecting them.

    [ DATABASE INFORMATION ]
    The signaling server maintains two internal databases, and has read/write responsibility for a public one.
    The two internal databases are used mainly for checking the requests' validity.

    [self.meetings]
    "id": {
        password: str,
        creator: (ip, port),
        expiration: int (ttl),
        participants: [(ip, port), (ip, port)]
    }

    [self.users] - saves users in the form of:
    (ip, port): {
        socket: socket object,
        ttl: int,
        id: str [optional],
        host: bool [optional]
    }

    [self.public_db] - saves meetings in the public database for the ice server in the form of:
    "id": {
        password: str,
        participants: [ip, ip]
    }
    """
    
    def __init__(self, port, public_db=None):
        super().__init__(port)

        # Make two new databases for meetings and clients
        self.meetings = {}
        self.users = {}

        # Get the public database
        self.public_db = public_db

        self.expiry_stopper = Event()
    

    def create_meeting(self, user_uuid):
        """
        Attempts to create a new meeting, and store it in the database.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user_uuid (str): Address tuple or other unique identifier.

        Returns: 
        tuple: The ID of the meeting, and its password.
        """

        # Check if the user is already in a meeting, or if they are already created one
        if self.users[user_uuid].get("created") and self.users[user_uuid]["created"] == True:
            raise AlreadyCreated
        elif self.users[user_uuid].get("id"):
            raise InMeeting

        # Create the new meeting details
        meeting_id = str(generate_uuid().int)[:MEETING_ID_LENGTH]
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(PASSWORD_LENGTH))

        # Store them in our database
        self.meetings[meeting_id] = {
            "password": password,
            "participants": [],
            "creator": user_uuid,
            "expiration": EMPTY_MEETING_EXPIRY
        }

        # Store the meeting in the public database
        self.store_meeting(meeting_id, self.meetings[meeting_id])

        # Log the meeting creator so that abuse can be prevented
        self.users[user_uuid]["created"] = True

        return (meeting_id, password)


    def join_meeting(self, user_uuid, meeting_id, password):
        """
        Attempts to join a meeting.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user_uuid (str): Address tuple or other unique identifier.
        user_sock (socket): The socket of the user.
        meeting_id (str): The ID of the meeting.
        password (str): The password of the meeting.

        Returns: 
        socket | None: The other user's socket.
        """

        # Check if the user is already in a meeting
        if self.users[user_uuid].get("id"):
            raise InMeeting

        # Check if the meeting exists
        if not self.meetings.get(meeting_id):
            raise InvalidMeetingID
        
        meeting = self.meetings[meeting_id]

        # Check if the password is correct
        if meeting["password"] != password:
            raise InvalidPassword

        # Check if the meeting is full
        if len(meeting["participants"]) >= MAX_PARTICIPANTS:
            raise MeetingFull

        # Add the user to the meeting
        meeting["participants"].append(user_uuid)
        meeting["expiry"] = EMPTY_MEETING_EXPIRY

        # Add the user to the public database
        self.store_meeting(meeting_id, meeting)
        
        # Setup access variables
        user = self.users[user_uuid]
        other_user = None

        user["id"] = meeting_id
        
        # Check if user deserves host privileges
        if len(meeting["participants"]) == 1:
            user["host"] = True
        else:
            user["host"] = False
            other_user = self.users[meeting["participants"][0]]["socket"]
        
        return other_user


    def leave_meeting(self, user_uuid):
        """
        Attempts to leave the meeting.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user_uuid (str): Address tuple or other unique identifier.

        Returns:
        tuple | None: The remaining user's address and socket.
        """

        # Check if the user is already in a meeting
        if not self.users[user_uuid].get('id'):
            raise NotInMeeting

        # Remove the user from the meeting
        user = self.users[user_uuid]
        meeting = self.meetings[user["id"]]

        remaining_user = None
        remaining_user_address = None

        # Update the meeting and the public database
        meeting["participants"].remove(user_uuid)
        self.store_meeting(user["id"], meeting)

        # Log the user out of the meeting
        del user["id"]
        del user["host"]

        # Check if another user is still in the meeting
        if len(meeting["participants"]) == 1:
            remaining_user_address = meeting["participants"][0]
            remaining_user = self.users[remaining_user_address]
            remaining_user["host"] = True
        
        if remaining_user:
            return remaining_user_address, remaining_user["socket"]


    def switch_host(self, user_uuid):
        """
        Switches the host of the meeting.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user (str): Address tuple or other unique identifier.

        Returns:
        socket: The socket of the new host.
        """

        # Check if the user is already in a meeting
        if not self.users[user_uuid].get('id'):
            raise NotInMeeting
        
        user = self.users[user_uuid]
        meeting = self.meetings[user["id"]]

        # Check if the user is the host
        if not user["host"]:
            raise InsufficientPermissions
        
        # Check if the meeting has another user
        if len(meeting["participants"]) < MAX_PARTICIPANTS:
            raise AloneInMeeting

        # Acquire the new host
        new_host_index = 1 if self.users[meeting["participants"][0]] == user else 0
        new_host = self.users[meeting["participants"][new_host_index]]

        # Switch the host
        user["host"] = False
        new_host["host"] = True

        return new_host["socket"]
    

    def end_meeting(self, user_uuid):
        """
        Attempts to end the meeting.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user_uuid (str): Address tuple or other unique identifier.

        Returns:
        socket | none: The socket of the remaining participant.
        """

        # Check if the user is already in a meeting
        if not self.users[user_uuid].get('id'):
            raise NotInMeeting
        
        user = self.users[user_uuid]
        meeting = self.meetings[user["id"]]

        second_user = None
        second_user_sock = None

        # Check if the user is the host
        if not user["host"]:
            raise InsufficientPermissions
        
        # Check if the meeting has another user
        if len(meeting["participants"]) == MAX_PARTICIPANTS:
            second_user_index = 1 if self.users[meeting["participants"][0]] == user else 0
            second_user = self.users[meeting["participants"][second_user_index]]

        # Remove the meeting from the database
        del self.meetings[user["id"]]
        del self.public_db[user["id"]]

        # Log the user out of the meeting
        del user["id"]
        del user["host"]

        # Log the second user out of the meeting
        if second_user:
            second_user_sock = [second_user["socket"]][:][0] # We do this mess to copy the socket by value

            del second_user["id"]
            del second_user["host"]

        # Remove creator status
        creator = self.users[meeting["creator"]]
        if creator.get("id"):
            creator["created"] = False
        else:
            del creator["created"]
        
        return second_user_sock
    

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
            second_user = self.leave_meeting(address)
            if second_user: # We need to unpack the tuple safely
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
                second_user_sock.send(serialize({"response": "info", "type": "disconnected"}).encode())
        except BrokenPipeError:
            self.disconnect_client(second_user)
            return True
        
        return False


    def meeting_cleaner(self):
        """
        This method is responsible for checking the meeting's TTL every minute.

        If a meeting is empty, the method will check if the TTL is 0. If yes,
        the meeting will be deleted, and the user's "creator" flag will be set to False.
        
        If the TTL isn't 0, the method will deduct it by 1.
        """
        
        # We want to run this worker until the server stops, at which point
        # this event will get set.
        while not self.expiry_stopper.is_set():
            counter = 0

            for id, meeting in self.meetings.copy().items():
                if len(meeting["participants"]) == 0:
                    if meeting["expiration"] <= 1: # The meeting has expired.
                        del self.meetings[id]
                        if self.public_db:
                            del self.public_db[id]
                            
                        counter += 1

                        # Get the creator
                        if self.users.get(meeting["creator"]) and self.users[meeting["creator"]].get("created"):
                            creator = self.users[meeting["creator"]]
                            
                            # Remove the user's creation status
                            if creator.get("id"):
                                creator["created"] = False
                            else:
                                del creator["created"]
                    else:
                        # If the meeting hasn't expired, and it's empty, deduct the TTL.
                        meeting["expiration"] = meeting["expiration"] - 1

            if counter > 0:
                print("[EXPIRY WORKER] Cleaned up {} meeting{}".format(counter, 's' if counter > 1 else ''))

            self.expiry_stopper.wait(MINUTE) # We put this function to "sleep" that can be awoken
    

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
                    except (BrokenPipeError, ConnectionResetError): # User has disconnected abruptly.
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
                    raise InvalidRequest
            except:
                raise InvalidRequest
                
            if not request.get("request"):
                raise InvalidRequest
            
            if request["request"] == "start":
                id, password = self.create_meeting(addr)
                responses.append((sock, serialize({"response": "success","type": "created", "id": id, "password": password})))
            
            elif request["request"] == "join":
                if not request.get("id") or not request.get("password"):
                    raise InvalidRequest
                
                other_client = self.join_meeting(addr, request["id"], request["password"])
                if other_client:
                    responses.append((sock, serialize({"response": "success","type": "connected", "waiting": False})))
                    responses.append((other_client, serialize({"response": "info", "type": "connected"})))
                else:
                    responses.append((sock, serialize({"response": "success", "type": "connected", "waiting": True})))
            
            elif request["request"] == "switch":
                new_host = self.switch_host(addr)
                responses.append((sock, serialize({"response": "success", "type" : "switched"})))
                responses.append((new_host, serialize({"response": "info", "type" : "switched"})))
            
            elif request["request"] == "leave":
                remaining_user = self.leave_meeting(addr)
                responses.append((sock, serialize({"response": "success", "type" : "disconnected"})))
                if remaining_user:
                    responses.append((remaining_user[1], serialize({"response": "info", "type": "disconnected"})))

            elif request["request"] == "end":
                remaining_user = self.end_meeting(addr)
                responses.append((sock, serialize({"response": "success", "type" : "ended"})))
                if remaining_user:
                    responses.append((remaining_user, serialize({"response": "info", "type": "ended"})))

            else:
                raise InvalidRequest

        except Exception as e:
            responses.append((sock, serialize({"response": "error", "reason": e.reason})))
        
        return responses
    

    def store_meeting(self, id, meeting):
        """
        Stores the meeting in the public database,
        discarding any information that doesn't need to be public.

        Parameters:
        id (str): The meeting ID.
        meeting (dict): The meeting to store.
        """

        # We only need to store the users' IP's. We do not care about their ports.
        participants = [participant[0] for participant in meeting["participants"]]

        # First, check if there is a public database available
        if self.public_db:
            self.public_db[id] = {
                "password": meeting["password"],
                "participants": serialize(participants) # Serialization is needed due to Redis' limitations.
            }
    

    def run(self):
        # Worker thread list
        workers = [Thread(target=self.meeting_cleaner), Thread(target=self.user_cleaner), Thread(target=self.user_handler)]

        try:
            # Start the threads
            for worker in workers: worker.start()

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
            for worker in workers:
                worker.join()


def main():
    public_db = None

    # Connect to the public database
    try:
        public_db = RedisDictDB("meetings")
        public_db.flush()
    except:
        public_db = None
        print("Couldn't connect to the Redis Database.")
        print("Public functionality with other servers will not work properly.")

    # Start the server
    server = Signaling(SERVER_PORT, public_db)
    server.start()
    server.toggle_blocking_mode()

    try:
        print("Signaling server started")
        server.run() # Blocking method - will continue running until the admin presses Ctrl+C
    except: pass

    print("\nStopping server...")
    server.stop()

    # Flush the database
    try:
        public_db.flush()
    except: pass


if __name__ == "__main__":
    main()
