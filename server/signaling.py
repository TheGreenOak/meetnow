from server import TCPServer, serialize, deserialize
from uuid import uuid4 as generate_uuid

import secrets # Cryptographically secure way to randomly choose
import string  # For easy access to ASCII characters


# Constants
MAX_MESSAGE_LENGTH = 128
MAX_MEETING_LENGTH = 5 # In minutes
MAX_PARTICIPANTS = 2
PASSWORD_LENGTH = 12
MEETING_ID_LENGTH = 9

SOCKET = 0
IP_ADDRESS = 1


class AlreadyCreated(Exception):
    pass


class InMeeting(Exception):
    pass


class NotInMeeting(Exception):
    pass


class InvalidMeetingID(Exception):
    pass


class InvalidPassword(Exception):
    pass


class MeetingFull(Exception):
    pass


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
    

    def create_meeting(self, user):
        """
        Attempts to create a new meeting, and store it in the database.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user (str): IP address or other unique identifier.

        Returns: 
        tuple: The ID of the meeting, and its password.
        """

        # Check if the user is already in a meeting, or if they are already created one
        if self.users.get(user):
            if self.users[user]["created"]:
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
            "creator": user,
            "expiration": MAX_MEETING_LENGTH
        }

        # Log the meeting creator so that abuse can be prevented
        self.users[user] = { "created": True }

        return (meeting_id, password)


    def join_meeting(self, user, meeting_id, password):
        """
        Attempts to join a meeting.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user (socket, str): Tuple of socket and IP address or other unique identifier.
        meeting_id (str): The ID of the meeting.
        password (str): The password of the meeting.

        Returns: 
        bool: Whether the user is a host or not.
        """

        # Check if the user is already in a meeting
        if self.users.get(user[IP_ADDRESS]):
            if not self.users[user]["created"]:
                raise InMeeting

        # Check if the meeting exists
        if not self.meetings.get(meeting_id):
            raise InvalidMeetingID

        # Check if the password is correct
        if self.meetings[meeting_id]["password"] != password:
            raise InvalidPassword

        # Check if the meeting is full
        if len(self.meetings[meeting_id]["participants"]) >= MAX_PARTICIPANTS:
            raise MeetingFull

        # Add the user to the meeting
        self.meetings[meeting_id]["participants"].append(user)

        # Log the user into the database
        if not self.users.get(user):
            self.users[user[IP_ADDRESS]] = { "created": False }
        self.users[user[IP_ADDRESS]]["id"] = meeting_id
        self.users[user[IP_ADDRESS]]["socket"] = user[SOCKET]
        
        # Check if user deserves host privileges
        if len(self.meetings[meeting_id]["participants"]) == 1:
            self.users[user[IP_ADDRESS]]["host"] = True
        else:
            self.users[user[IP_ADDRESS]]["host"] = False
        
        return self.users[user[IP_ADDRESS]]["host"]


    def leave_meeting(self, user):
        """
        Attempts to leave the meeting.
        If the user cannot do so, an exception will be raised.

        Parameters:
        user (str): IP address or other unique identifier.
        """

        # Check if the user is already in a meeting
        if not self.users.get(user):
            raise NotInMeeting

        # Remove the user from the meeting
        self.meetings[self.users[user]["id"]]["participants"].remove(user)

        # Log the user out of the database
        del self.users[user]["id"]
        del self.users[user]["socket"]
        del self.users[user]["host"]

        if not self.users[user]["created"]:
            del self.users[user]


    def handle_client(self, client):
        pass


    def handle_message(self, client, message):
        pass

    
def test():
    s = Signaling(522)
    
    # Randomness tester
    print("Random Test")
    for i in range(10):
        print(s.create_meeting(str(i)))
    print("Passed", end="\n\n")
    
    # Already created tester
    print("Already Created Test - ", end='')
    try:
        s.create_meeting("1")
    except AlreadyCreated:
        print("Passed")
    except:
        print("Failed")
    
    # Join meeting tester
    print("Join Meeting Test - ", end='')
    try:
        meeting = s.create_meeting("100")
        s.join_meeting("100", meeting[0], meeting[1])
        s.join_meeting("101", meeting[0], meeting[1])
        s.join_meeting("101", meeting[0], meeting[1])
    except InMeeting:
        print("Passed")


def main():
    test()


if __name__ == "__main__":
    main()


"""
Client
- {"request": "start"} Start new meeting ✅
- {"request": "stop"} Stop meeting (only if you're host)
- {"request": "switch"} Transfer host
- {"request": "join", "id": "string, "password": "string" } Join meeting (takes ID, pass)
- {"request": "leave"} Leave meeting

Server
- {"response": "success", "type": "started", "id": "string", "message": "Meeting started."} Meeting started ✅
- {"response": "success", "type": "stopped", "message": "Meeting stopped."} Meeting stopped

- {"response": "success", "type": "joined", "host": boolean, "message": "You've joined the meeting"} You joined the meeting
- {"response": "success", "type": "left", "message": "You've left the meeting"} You left the meeting

- {"response": "info", "type": "joined", "message": "User has joined your meeting."} User joined your meeting
- {"response": "info", "type": "left", "message": "User has left your meeting."} User left your meeting

- {"response": "success", "type": "switched", "message": "You've transferred the host."} Transferred host
- {"response": "info", "type": "switched", "message": "You're now the host."} You're now the host

- {"response": "error", "reason": "You're already in a meeting."} Error creating (you're already in a meeting) ✅
- {"response": "error", "reason": "You've already created a meeting in the past x minutes"} Error creating (you've already created a meeting in the past x minutes) ✅
- {"response": "error", "reason": "Invalid meeting ID."} Error joining (invalid ID)
- {"response": "error", "reason": "Incorrect password."} Error joining (invalid pass)
- {"response": "error", "reason": "You're already in a meeting."} Error joining (you're already in a meeting)
- {"response": "error", "reason": "Meeting is full."} Error joining (meeting is full)
- {"response": "error", "reason": "You're not in a meeting"} Error leaving (you're not in a meeting)
- {"response": "error", "reason": "Insufficient permissions."} Error transferring (you're not the host)
- {"response": "error", "reason": "Insufficient permissions."} Error ending (you're not the host)
- {"response": "error", "reason": "You're not in a meeting."} Error ending (you're not in a meeting) 

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