from server import UDPServer
from threading import Thread, Event
from json import loads as deserialize, dumps as serialize

 # TODO: 
SERVER_PORT = 3479 # The TURN port except for the last number  - https://www.3cx.com/blog/voip-howto/stun-voip-1/
MINUTE = 60
USER_TTL_MESSAGES = 2


class NoMeetingID(Exception):
    reason = "No meeting ID found"

class WrongPassword(Exception):
    reason = "Wrong meeting password"

class InvalidRequest(Exception):
    reason = "Invalid request"

class AloneInMeeting(Exception):
    reason = "You're alone in this meeting"

class OtherUserNotConnected(Exception):
    reason = "The other user is not connected yet"


class Turn(UDPServer):
    """
    The TURN server is responsible for connecting two users that can't communicate through P2P.
    """
    

    def __init__(self, port):
        super().__init__(port)

        self.users = {}
                # ("127.0.0.1", 1337) : {"ttl": 2, "peer" : ("128.0.0.1", 42069)},
                # ("128.0.0.1", 42069) : {"ttl": 2, "peer" : ("127.0.0.1", 1337)}
            # }

        self.expiry_stopper = Event()

    def run(self):
        threads = []

        try:
            # Create expiration worker threads
            expiry_workers = [Thread(target=self.user_cleaner)]
            for worker in expiry_workers:
                worker.start()
                threads.append(worker)

            while True:
                try:
                    # In UDP, there are no sockets. Therefore, we just need to receive data.
                    data, address = self.recv()
                    if (address[0], address[1]) not in self.users:
                        other_user = self.check_meeting_valid(address)
                    # If the user is not in the database, check who's the other user in the meeting and add him
                    # Else, if the user is already in the database, just update his ttl because he's online.
                    self.users[(address[0], address[1])] = {"ttl" : USER_TTL_MESSAGES, "peer" : (other_user)}
                    
                    print(self.users)
                    data = data.decode()
                    print(f"[{address[0]}:{address[1]}] {data}")

                    try:
                        dest = self.check_meeting_valid(address)
                    except Exception as e:
                        print(e)
                        self.return_exception(address, e)
                    
                    self.forward(dest, data)

                except BlockingIOError:
                    pass
        except KeyboardInterrupt:
            self.keep_running = False


    def check_meeting_valid(self, address):
        if 1!=1: # the meeting id is not in the database
            raise NoMeetingID
        if 1!= 1: # if the password is incorrect
            raise WrongPassword
        if 1!=1: # if there is only 1 user
            raise AloneInMeeting
        if 1!=1: # check if the user is connected to the turn server
            raise OtherUserNotConnected
        # return participant to send to
        return ("127.0.0.1", 1337)
    
    def return_exception(self, address, exception):
        exception = "S" + exception 
        exception = exception.encode()
        self.send(address, exception)

    def forward(self, address, data):
        data = "U" + data
        data = data.encode()
        self.send(address, data)
    
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

        del self.users[user_uuid]
        print("[DISCONNECTED] {}:{}".format(user_uuid[0], user_uuid[1]))

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
        second_user = None

        # If the user disconnects in a meeting, remove them from the meeting
        if user.get("id"):
            second_user = self.disconnect_peer(address)
        
        del self.users[address]

        if second_user:
            return (second_user, serialize({"response": "info", "type": "left"}))


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