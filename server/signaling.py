from server import TCPServer
from threading import Thread, Event
from json import loads as deserialize, dumps as serialize
from uuid import uuid4 as generate_uuid

import secrets   # Cryptographically secure way to randomly choose
import string    # For easy access to ASCII characters
import traceback # Error reporting


# Constants
MAX_MESSAGE_LENGTH = 128
EMPTY_MEETING_EXPIRY = 5 # In minutes | Serves as TTL for the meeting
MAX_PARTICIPANTS = 2

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
    The Signaling server is responsible for creating and assigning ID's to meetings.
    The server will be based on our basic TCP server.

    The point of it is to connect clients together. It does not have any other responsibilities,
    and does not care what happens to the clients beyond connecting them.
    """
    
    def __init__(self, port):
        super().__init__(port)

        # Make two new databases for meetings and clients
        self.meetings = {}
        self.users = {}
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
        if self.users.get(user_uuid):
            if self.users[user_uuid]["created"]:
                raise AlreadyCreated
            else:
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

        # Log the meeting creator so that abuse can be prevented
        self.users[user_uuid] = { "created": True }

        return (meeting_id, password)


    def join_meeting(self, user_uuid, user_sock, meeting_id, password):
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
        if self.users.get(user_uuid) and self.users[user_uuid].get("id"):
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

        # Log the user into the database
        if not self.users.get(user_uuid):
            self.users[user_uuid] = { "created": False }
        
        user = self.users[user_uuid]
        other_user = None

        user["id"] = meeting_id
        user["socket"] = user_sock
        
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
        socket | None: The remaining user's socket.
        """

        # Check if the user is already in a meeting
        if not self.users.get(user_uuid) or not self.users[user_uuid].get('id'):
            raise NotInMeeting

        # Remove the user from the meeting
        user = self.users[user_uuid]
        remaining_user_sock = None
        meeting = self.meetings[user["id"]]

        meeting["participants"].remove(user_uuid)

        # Log the user out of the database
        if not user["created"]:
            del self.users[user_uuid]
        else:
            del user["id"]
            del user["socket"]
            del user["host"]

        # Check if another user is still in the meeting
        if len(meeting["participants"]) == 1:
            remaining_user = self.users[meeting["participants"][0]]
            remaining_user["host"] = True
            remaining_user_sock = remaining_user["socket"]
        
        return remaining_user_sock


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
        if not self.users.get(user_uuid) or not self.users[user_uuid].get('id'):
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
        if not self.users.get(user_uuid) or not self.users[user_uuid].get('id'):
            raise NotInMeeting
        
        user = self.users[user_uuid]
        second_user = None
        second_user_sock = None
        meeting = self.meetings[user["id"]]

        # Check if the user is the host
        if not user["host"]:
            raise InsufficientPermissions
        
        # Check if the meeting has another user
        if len(meeting["participants"]) == MAX_PARTICIPANTS:
            second_user_index = 1 if self.users[meeting["participants"][0]] == user else 0
            second_user = self.users[meeting["participants"][second_user_index]]

        # Remove the meeting from the database
        del self.meetings[user["id"]]

        # Log the user out of the database
        if not user["created"]:
            del self.users[user_uuid]
        else:
            del user["id"]
            del user["socket"]
            del user["host"]

        # Log the second user out of the database
        if second_user:
            second_user_sock = [second_user["socket"]][:][0] # We do this mess to copy the socket by value

            if not second_user["created"]:
                del self.users[meeting["participants"][second_user_index]]
            else:
                del second_user["id"]
                del second_user["socket"]
                del second_user["host"]

        # Remove creator status
        if self.users.get(meeting["creator"]):
            creator = self.users[meeting["creator"]]
            if creator.get("id"):
                creator["created"] = False
            else:
                del self.users[meeting["creator"]]
        
        return second_user_sock
    

    def expiry_worker(self):
        """
        This method is responsible for checking the current meeting's TTL
        every minute.

        If a meeting is empty, the method will check if the TTL is 0. If yes,
        the meeting will be deleted, and the user's "creator" flag will be set to False.
        
        If the TTL isn't 0, the method will deduct it by 1.
        """
        while not self.expiry_stopper.is_set():
            count = 0

            for id, meeting in self.meetings.copy().items():
                if len(meeting["participants"]) == 0:
                    if meeting["expiration"] <= 1: # The meeting has expired.
                        del self.meetings[id]
                        count += 1

                        creator = self.users[meeting["creator"]]
                        
                        if creator.get("id"):
                            creator["created"] = False
                        else:
                            del self.users[meeting["creator"]]
                    else:
                        meeting["expiration"] = meeting["expiration"] - 1

            if count > 0:
                print("[EXPIRY WORKER] Cleaned up {} meeting{}".format(count, 's' if count > 1 else ''))
            self.expiry_stopper.wait(MINUTE) # We put this function to "sleep" that can be awoken

    
    def disconnect_client(self, user_uuid):
        """
        This method is responsible for removing a client from the database.

        user_uuid (tuple): Address tuple or other unique identifier.

        returns: tuple | None: The message that needs to be sent to the socket (both in tuple).
        """
        if not self.users.get(user_uuid):
            return None
        
        user = self.users[user_uuid]
        second_user = None

        if user.get("id"):
            second_user = self.leave_meeting(user_uuid)
        
        if second_user:
            return (second_user, serialize({"response": "info", "type": "left"}))


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
        except ConnectionError:
            pass
        except:
            # An unknown error has occurred
            print("CRITICAL: An unknown error has occurred.")
            print("Client: {}:{}".format(address[0], address[1]))
            print("Message: {}".format(data.decode()))
            print(traceback.format_exc())

            client.send(serialize({"response": "error", "reason": "An unknown error occurred"}).encode())
            
        finally:
            print("[DISCONNECTED] {}:{}".format(address[0], address[1]))
            client.close()

            # Clean up the database
            update = self.disconnect_client(address)
            if update:
                update[SOCK_INDEX].send(update[MSG_INDEX].encode())


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
            try:
                request = deserialize(message)
            except:
                raise InvalidRequest
                
            if not request.get("request"):
                raise InvalidRequest
            
            if request["request"] == "start":
                id, password = self.create_meeting(addr)
                responses.append((sock, serialize({"response": "success", "id": id, "password": password})))
            
            elif request["request"] == "join":
                if not request.get("id") or not request.get("password"):
                    raise InvalidRequest
                
                other_client = self.join_meeting(addr, sock, request["id"], request["password"])
                if other_client:
                    responses.append((sock, serialize({"response": "success", "host": False})))
                    responses.append((other_client, serialize({"response": "info", "type": "joined"})))
                else:
                    responses.append((sock, serialize({"response": "success", "host": True})))
            
            elif request["request"] == "switch":
                new_host = self.switch_host(addr)
                responses.append((sock, serialize({"response": "success"})))
                responses.append((new_host, serialize({"response": "info", "type": "switched"})))
            
            elif request["request"] == "leave":
                remaining_user = self.leave_meeting(addr)
                responses.append((sock, serialize({"response": "success"})))
                if remaining_user:
                    responses.append((remaining_user, serialize({"response": "info", "type": "left"})))

            elif request["request"] == "end":
                remaining_user = self.end_meeting(addr)
                responses.append((sock, serialize({"response": "success"})))
                if remaining_user:
                    responses.append((remaining_user, serialize({"response": "info", "type": "ended"})))

            else:
                raise InvalidRequest

        except Exception as e:
            responses.append((sock, serialize({"response": "error", "reason": e.reason})))
        
        return responses
    

    def run(self):
        threads = []

        try:
            while True:
                try:
                    client, address = self.accept()
                    print("[CONNECTED] {}:{}".format(address[0], address[1]))

                    # Make a new thread to handle the client, and store it in the list.
                    expiry_worker = Thread(target=self.expiry_worker)
                    client_thread = Thread(target=self.handle_client, args=(client, address))

                    expiry_worker.start()
                    client_thread.start()

                    threads.append(expiry_worker)
                    threads.append(client_thread)
                except BlockingIOError:
                    pass
        except KeyboardInterrupt:
            self.keep_running = False
            self.expiry_stopper.set()

            for thread in threads:
                thread.join()


def main():
    server = Signaling(SERVER_PORT)
    server.start()
    server.toggle_blocking_mode()

    print("Signaling server started")
    server.run() # Blocking method - will continue running until the admin presses Ctrl+C

    print("\nStopping server...")
    server.stop()


if __name__ == "__main__":
    main()
