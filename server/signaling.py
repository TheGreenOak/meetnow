from server import TCPServer
from json import loads as deserialize, dumps as serialize
from threading import Thread
from uuid import uuid4 as generate_uuid

import secrets # Cryptographically secure way to randomly choose
import string  # For easy access to ASCII characters


# Constants
MAX_MESSAGE_LENGTH = 128
MAX_MEETING_LENGTH = 5 # In minutes
MAX_PARTICIPANTS = 2

PASSWORD_LENGTH = 12
MEETING_ID_LENGTH = 9

SERVER_PORT = 522


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
    

    def create_meeting(self, user_uuid) -> tuple[str, str]:
        """
        Attempts to create a new meeting, and store it in the database.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user_uuid (str): IP address or other unique identifier.

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
            "expiration": MAX_MEETING_LENGTH
        }

        # Log the meeting creator so that abuse can be prevented
        self.users[user_uuid] = { "created": True }

        return (meeting_id, password)


    def join_meeting(self, user_uuid, user_sock, meeting_id, password):
        """
        Attempts to join a meeting.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user_uuid (str): IP address or other unique identifier.
        user_sock (socket): The socket of the user.
        meeting_id (str): The ID of the meeting.
        password (str): The password of the meeting.

        Returns: 
        socket | None: The other user's socket.
        """

        # Check if the user is already in a meeting
        if self.users.get(user_uuid):
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
        user_uuid (str): IP address or other unique identifier.

        Returns:
        socket | None: The remaining user's socket.
        """

        # Check if the user is already in a meeting
        if self.users.get(user_uuid):
            if not self.users[user_uuid].get("id"):
                raise NotInMeeting

        # Remove the user from the meeting
        user = self.users[user_uuid]
        remaining_user = None
        meeting = self.meetings[user["id"]]

        meeting["participants"].remove(user_uuid)

        # Log the user out of the database
        if not user["created"]:
            del user
        else:
            del user["id"]
            del user["socket"]
            del user["host"]

        # Check if another user is still in the meeting
        if len(meeting["participants"]) == 1:
            remaining_user = self.users[meeting["participants"][0]]["socket"]
            remaining_user["host"] = True
        
        return remaining_user


    def switch_host(self, user_uuid):
        """
        Switches the host of the meeting.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user (str): IP address or other unique identifier.

        Returns:
        socket: The socket of the new host.
        """

        # Check if the user is already in a meeting
        if self.users.get(user_uuid):
            if not self.users[user_uuid].get("id"):
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
        new_host_index = 1 if meeting["participants"][0] == user else 0
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
        user_uuid (str): IP address or other unique identifier.

        Returns:
        socket | none: The socket of the remaining participant.
        """

        # Check if the user is already in a meeting
        if self.users.get(user_uuid):
            if not self.users[user_uuid].get("id"):
                raise NotInMeeting
        
        user = self.users[user_uuid]
        second_user_sock = None
        meeting = self.meetings[user["id"]]

        # Check if the user is the host
        if not user["host"]:
            raise InsufficientPermissions
        
        # Check if the meeting has another user
        if len(meeting["participants"]) == MAX_PARTICIPANTS:
            second_user_index = 1 if meeting["participants"][0] == user else 0
            second_user = self.users[meeting["participants"][second_user_index]]
        
        # Remove the meeting from the database
        del meeting

        # Log the user out of the database
        if not user["created"]:
            del user
        else:
            del user["id"]
            del user["socket"]
            del user["host"]

        # Log the second user out of the database
        if second_user:
            second_user_sock = [second_user["socket"]][:][0] # We do this mess to copy the socket by value
            if not second_user["created"]:
                del second_user
            else:
                del second_user["id"]
                del second_user["socket"]
                del second_user["host"]
        
        return second_user_sock


    def handle_client(self, client, address):
        try:
            while self.keep_running:
                try:
                    data = client.recv(MAX_MESSAGE_LENGTH)
                    if not data:
                        break

                    for sock, message in self.handle_message(address[0], client, data.decode()):
                        sock.send(message.encode())
                except BlockingIOError:
                    pass
        except:
            pass
        finally:
            print("[DISCONNECTED] {}:{}".format(address[0], address[1]))
            client.close()


    def handle_message(self, ip, sock, message):
        """
        Handles all requests from the client.
        Returns the messages that need to be sent to each client after the request.

        Parameters:
        ip (str): The client's IP
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
                id, password = self.create_meeting(ip)
                responses.append((sock, serialize({"response": "success", "id": id, "password": password})))
            
            elif request["request"] == "join":
                if not request.get("id") or not request.get("password"):
                    raise InvalidRequest
                
                other_client = self.join_meeting(ip, sock, request["id"], request["password"])
                if other_client:
                    responses.append((sock, serialize({"response": "success", "host": False})))
                    responses.append((other_client, serialize({"response": "info", "type": "joined"})))
                else:
                    responses.append((sock, serialize({"response": "success", "host": True})))
            
            elif request["request"] == "switch":
                new_host = self.switch_host(ip)
                responses.append((sock, serialize({"response": "success"})))
                responses.append((new_host, serialize({"response": "info", "type": "switched"})))
            
            elif request["request"] == "leave":
                remaining_user = self.leave_meeting(ip)
                responses.append((sock, serialize({"response": "success"})))
                if remaining_user:
                    responses.append((remaining_user, serialize({"response": "info", "type": "left"})))

            elif request["request"] == "end":
                remaining_user = self.end_meeting(ip)
                responses.append((sock, serialize({"response": "success"})))
                if remaining_user:
                    responses.append((remaining_user, serialize({"response": "info", "type": "ended"})))

            else:
                raise InvalidRequest

        except Exception as e:
            responses.append((sock, serialize({"response": "error", "reason": e.reason})))
        
        return responses
    

    def run(self):
        clients = []

        try:
            while True:
                try:
                    client, address = self.accept()
                    print("[CONNECTED] {}:{}".format(address[0], address[1]))

                    # Make a new thread to handle the client, and store it in the list.
                    client_thread = Thread(target=self.handle_client, args=(client, address))
                    client_thread.start()
                    clients.append(client_thread)
                except BlockingIOError:
                    pass
        except KeyboardInterrupt:
            self.keep_running = False

            for thread in clients:
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


"""
Client
- {"request": "start"} Start new meeting ✅
- {"request": "stop"} Stop meeting (only if you're host) ✅
- {"request": "switch"} Transfer host ✅
- {"request": "join", "id": "string, "password": "string" } Join meeting (takes ID, pass) ✅
- {"request": "leave"} Leave meeting ✅

Server
- {"response": "success", "type": "started", "id": "string", "message": "Meeting started."} Meeting started ✅
- {"response": "success", "type": "stopped", "message": "Meeting stopped."} Meeting stopped ✅

- {"response": "success", "type": "joined", "host": boolean, "message": "You've joined the meeting"} You joined the meeting ✅
- {"response": "success", "type": "left", "message": "You've left the meeting"} You left the meeting ✅

- {"response": "info", "type": "joined", "message": "User has joined your meeting."} User joined your meeting
- {"response": "info", "type": "left", "message": "User has left your meeting."} User left your meeting

- {"response": "success", "type": "switched", "message": "You've transferred the host."} Transferred host ✅
- {"response": "info", "type": "switched", "message": "You're now the host."} You're now the host ✅

- {"response": "error", "reason": "You're already in a meeting."} Error creating (you're already in a meeting) ✅
- {"response": "error", "reason": "You've already created a meeting in the past x minutes"} Error creating (you've already created a meeting in the past x minutes) ✅
- {"response": "error", "reason": "Invalid meeting ID."} Error joining (invalid ID) ✅
- {"response": "error", "reason": "Incorrect password."} Error joining (invalid pass) ✅
- {"response": "error", "reason": "You're already in a meeting."} Error joining (you're already in a meeting) ✅
- {"response": "error", "reason": "Meeting is full."} Error joining (meeting is full) ✅
- {"response": "error", "reason": "You're not in a meeting"} Error leaving (you're not in a meeting) ✅
- {"response": "error", "reason": "Insufficient permissions."} Error switching (you're not the host) ✅
- {"response": "error", "reason": "You're not in a meeting"} Error switching (you're not in a meeting) ✅
- {"response": "error", "reason": "You're alone in the meeting"} Error switching (you're alone in the meeting) ✅
- {"response": "error", "reason": "Insufficient permissions."} Error ending (you're not the host) ✅
- {"response": "error", "reason": "You're not in a meeting."} Error ending (you're not in a meeting) ✅

Request Types: ["start", "stop", "switch", "join", "leave"]
Responses: ["success", "info", "error"]
Response Types: ["started", "stopped", "joined", "left", "switched"] 

Database
Python Dictionary

{"meeting id": {
  "password": "hashed pass",
  "participants": int,
  "creator": "ip",
  "ttl": int
  }
}

{"ip": {
  "created": boolean
  "id": "meeting id",
  "is_host": boolean
}
 
    """