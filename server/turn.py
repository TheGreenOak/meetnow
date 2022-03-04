from http.client import responses
from lib2to3.pgen2.token import EQUAL
from logging import exception
from server import UDPServer
from threading import Thread, Event
from json import loads as deserialize, dumps as serialize
from database.redisdb import RedisDictDB

import traceback
import ast


SERVER_PORT = 3479 # The TURN port except for the last number  - https://www.3cx.com/blog/voip-howto/stun-voip-1/
MINUTE = 60
USER_TTL_MESSAGES = 2

class MeetingFull(Exception):
    reason = "Meeting is full."

class NotJsonFormat(Exception):
    reason = "Request not in JSON format."

class NoMeetingID(Exception):
    reason = "No meeting ID found."

class WrongPassword(Exception):
    reason = "Wrong meeting password."

class InvalidRequest(Exception):
    reason = "Invalid request."

class AloneInMeeting(Exception):
    reason = "You're alone in this meeting."

class OtherUserNotConnected(Exception):
    reason = "The other user is not connected yet."


class Turn(UDPServer):
    """
    [ SERVER INFORMATION ]
    The TURN (Traversal Using Relays around NAT) server is responsible for connecting
    both clients, and forwarding messages between them. This is done so that the clients
    will be able communicate with each other by when their NAT doesn't allow P2P communication.

    [ DATABASE INFORMATION ]
    The TURN server maintains two internal databases, and has read access for the public one.
    The two internal databases are used mainly for checking request validity and to know where to forward the messages.

    [self.users]
    (ip, port): {
        ttl: int,
        peer: (other ip, other port),
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
        

    def find_other_user(self, address, meeting_id, password):
        """
        This method cheks the validity of the data sent by the user and connects him to the connections meeting.
        Then the method finds the other user and returns it.
        
        Parameters:
        address (tuple of str and list): The address of the user.
        meeting_id (int): The meeting ID sent by the user.
        password (str): The password sent by the user.

        Returns:
        tuple | none: The other user in the public meeting.

        """
        # Checking if the meeting ID is existing
        try:
            meeting = self.public_db[meeting_id]
            if not meeting:
                raise NoMeetingID
        except:
            raise NoMeetingID
        
        # Checking if the password is correct
        if meeting.get("password") != password:  
            raise WrongPassword

        # Checking if if there is only 1 user in the meeting
        # The meeting["patricipants"] is for some reason a string so we need to turn it into a list.
        if len(ast.literal_eval(meeting["participants"])) != 2:
            raise AloneInMeeting


        # If there are two users in the public database, check how much users are in the connections meeting
        try:
            both_users = self.connections[meeting_id]
            if len(both_users) == 1: # If there is only one user, go to the except below this try
                raise Exception
            raise MeetingFull # Else, the connections meeting is full and a third user is trying to connect

        except MeetingFull: # Send the MeetingFull excepting to the connect_user function to handle
            raise MeetingFull
        # If the connections meeting exsit, add this user and send the other one
        except:
            if self.connections.get(meeting_id):
                self.connections[meeting_id].append(address)
                return self.connections[meeting_id][0]
            else: # Otherwise, create it and return nothing
                self.connections[meeting_id] = [(address)]
                return None


    def handle_responses(self, responses):
        """
        This method puts the addresses in a list and the data in a differant list.
        then it send the data to the matching addresses.
        the responses are always server messages in a JSON format.

        Parameters:
        responses (list of tuples of string and string): A list of tuples made of the address to send to and the data.
        """
        # Getting all the addresses to a list and the data to send to a differant list
        addresses = [address[0] for address in responses]
        data_to_send = [data[1] for data in responses]

        # Sending all of the data
        for i in range(len(addresses)):

            address = addresses[i]
            data = data_to_send[i].encode()
            self.send(address, data)

    def forward(self, address, data):
        """
        The method forwards the data sent from one user to the other in the same meeting.

        Parameters:
        address (tuple of str and int): The address of the user to send to.
        data (str): The data to forward.
        """
        data = "C" + data
        data = data.encode()
        other_user = self.users[address]["peer"]

        if other_user:
            self.send(other_user, data)
        else:
            raise OtherUserNotConnected


    def user_cleaner(self):
        """
        This method is responsible for checking the user's TTL, and will send a heartbeat every minute.
        If the user's TTL is 0, they will be disconnected.
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
                    self.send(user_uuid, b"HEARTBEAT")

            if counter > 0:
                print("[EXPIRY WORKER] Disconnected {} client{}".format(counter, 's' if counter > 1 else ''))

            self.expiry_stopper.wait(MINUTE) # We put this function to "sleep" that can be awoken


    def disconnect_client(self, address):
        """
        This method is responsible for removing a client from the database, and sending a message to the other user.

        No checks are performed to ensure that the client is in the database.
        Call this method only after checking that the client is in the database.

        Parameters:
        address (tuple of str and int): The address of the user that is supposesd to be deleted.
        """

        # Setup temporary variables
        user = self.users[address]
        other_user = user["peer"]
        
        del self.users[address]

        # Telling the other user that the user has been disconnected
        if other_user:
            self.handle_responses([(other_user, serialize({"response": "info", "type": "left"}))])


    def connect_user(self, address, data):
        """
        This method makes sure the connect request is sent by the format and connects the user to the database.
        It check if the other user is connect too and sends him an update that the other user is connected.

        Parameters:
        address (tuple of str and int): The address of the user that wants to connect.
        data (str): The data the user has sent.

        Returns:
        responses: A list of responses that need to be sent to the users. 
        """

        responses = []

        # Checking if the message is in the JSON format
        try:
            request = deserialize(data)
        except:
            responses.append((address, serialize({"response": "error", "reason": NotJsonFormat.reason})))
            return responses

        # Checking if the message is not a request
        if not request.get("request"):
            responses.append((address, serialize({"response": "error", "reason": InvalidRequest.reason})))
            return responses

        # Checking if there is a meeting ID and password sent
        if request["request"] == "connect":
            if not request.get("id") or not request.get("password"):
                responses.append((address, serialize({"response": "error", "reason": InvalidRequest.reason})))
                return responses

            try:
                other_user = self.find_other_user(address, request.get("id"), request.get("password"))
                if other_user:
                    # Adding the user with peer : other_user
                    self.users[address] = {"ttl" : USER_TTL_MESSAGES, "peer" : other_user}
                    self.users[other_user]["peer"] = address
                    responses.append((address, serialize({"response": "success", "waiting": False})))
                    responses.append((other_user, serialize({"response": "info", "type": "connected"})))
                else:
                    # Adding the user with peer : None
                    self.users[address] = {"ttl" : USER_TTL_MESSAGES, "peer" : None}
                    responses.append((address, serialize({"response": "success", "waiting": True})))
            
            except (NoMeetingID, NotJsonFormat, WrongPassword, MeetingFull, AloneInMeeting) as e:
                # Catches the exceptions from find_other_user and sends them to the user
                responses.append((address, serialize({"response": "error", "reason": e.reason})))

            except Exception as e:
                # If something happend and i dont know what, tell the user unknown error
                # An unknown error has occurred
                print("CRITICAL: An unknown error has occurred.")
                print(f"Client: {address[0]}:{address[1]}")
                print(f"Message: {data}")
                print(traceback.format_exc())

                responses.append((address, serialize({"response": "error", "reason" : "Unknown error occured"})))

        else:
            responses.append((address, serialize({"response": "error", "reason": InvalidRequest.reason})))
            
        return responses


    def run(self):
        threads = []

        try:
            # Create expiration worker threads
            expiry_worker = Thread(target=self.user_cleaner)
            expiry_worker.start()
            threads.append(expiry_worker)

            while True:
                try:
                    # In UDP, there are no sockets. Therefore, we just need to receive data.
                    data, address = self.recv()
                    data = data.decode()

                    try:
                        # If we received a message from the user, they're alive.
                        self.users[address]["ttl"] = USER_TTL_MESSAGES
                        
                    except:
                        # If they are not in the database, connect them.
                        responses = self.connect_user(address, data)

                    print(f"[{address[0]}:{address[1]}] {data}")

                    # If there are responses that supposed to be sent, send them.
                    if responses:
                        self.handle_responses(responses)
                        responses = []

                    elif data == "HEARTBEAT": 
                        # If the message is heartbeat, we don't need to do anything, we already updated the TTL.
                        pass
                    
                    else:
                        # If the user is connected, and is not "HEARTBEAT" forward it to the other user
                        try:
                            self.forward(address, data)
                        except OtherUserNotConnected as e:
                            responses.append((address, serialize({"response": "error", "reason": e.reason})))
                            self.handle_responses(responses)
                            responses = []

                except BlockingIOError:
                    pass
        
        except KeyboardInterrupt:
            self.keep_running = False
            self.expiry_stopper.set()

            for thread in threads:
                thread.join()


def main():
    try:
        public_db = RedisDictDB("meetings")
    except:
        print("Could not connect to the Redis Database.")
        print("Please make sure that Redis is running on the local machine with the default parameters.")
        exit(1)

    server = Turn(SERVER_PORT, public_db)
    server.start()
    server.toggle_blocking_mode()

    print("TURN server started")
    server.run() # Blocking method - will continue running until the admin presses Ctrl+C

    print("\nStopping server...")
    server.stop()

if __name__ == "__main__":
    main()