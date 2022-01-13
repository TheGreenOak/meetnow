from server import UDPServer
from threading import Thread, Event
from json import loads as deserialize, dumps as serialize
from database.redisdb import RedisDictDB


SERVER_PORT = 3479 # The TURN port except for the last number  - https://www.3cx.com/blog/voip-howto/stun-voip-1/
MINUTE = 60
USER_TTL_MESSAGES = 2

NOT_FOUND_USER_YET = 0
OTHER_USER_NOT_CONNECTED = 1


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

class ForwardMessage(Exception):
    pass


class Turn(UDPServer):
    """
    The TURN server is responsible for connecting two users that can't communicate through P2P.
    """
    

    def __init__(self, port, public_db):
        super().__init__(port)

        self.users = {}
                # example of how the database looks:
                # ("127.0.0.1", 1337) : {"ttl": 2, meeting_id : 3456324, "peer" : ("128.0.0.1", 42069)},
                # ("128.0.0.1", 42069) : {"ttl": 2, meeting_id : 3456324, "peer" : ("127.0.0.1", 1337)}}
                # both of these users are in the same meeting and therefore they have each others "peers"

        self.expiry_stopper = Event()
        self.public_db = public_db



    def find_other_user(self, address, meeting_id, password):
        # Checking if the meeting ID is not existing
        try:
            meeting = self.public_db[meeting_id]
        except:
            raise NoMeetingID
        
        # Checking if the password is correct
        if self.meeting[meeting_id]["password"] != password:  
            raise WrongPassword

        # Checking if if there is only 1 user
        try:
            return self.meeting[meeting_id]["participants"][1]
        except:
            raise AloneInMeeting

    def server_message(self, responses):
        
        addresses = [address[0] for address in responses]
        data_to_send = [data[0] for data in responses]

        for i in range(len(addresses)):

            address = addresses[i]
            data = "S" + data_to_send[i]
            data = data.encode()
            self.send(address, data)

    def forward(self, address, data):
        data = "U" + data
        data = data.encode()
        self.send(address, data)

    def return_exception(self, address, exception):
        exception = "S" + exception 
        exception = exception.encode()
        self.send(address, exception)

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

    def handle_message(self, address, data):

        responses = []

        try:

            if data == "HEARTBEAT":
                return [] # No need to return a message

            try:
                request = deserialize(data)
                if type(request) is not dict: # Then the message if for the other user and should be forwarded
                    raise Exception
            except:
                self.forward(address, data)
                raise ForwardMessage

            if not request.get("request"):
                raise InvalidRequest

            if request["request"] == "connect":
                if not request.get("id") or not request.get("password"):
                    raise InvalidRequest
            
                try:
                    other_user = self.find_other_user(address, request["id"], request["password"])
                
                    if other_user:
                        respwnses.append((address, serialize({"response": "success", "waiting": False})))
                        responses.append((other_user, serialize({"response": "info", "type": "connected"})))
                    else:
                        responses.append((address, serialize({"response": "success", "waiting": True})))
                except AloneInMeeting:
                    responses.append((address, serialize({"response": "success", "waiting": True})))

            else:
                raise InvalidRequest

        except ForwardMessage:
            pass

        except Exception as e:
            response = (address, serialize({"response": "error", "reason": e.reason}))
        
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
                        self.users[address]["ttl"] = USER_TTL_MESSAGES # If we received a message from the user, they're alive.
                    except:
                        pass

                    responses = self.handle_message(address, data)
                    
                    print(self.users)
                    print(responses)

                    print(f"[{address[0]}:{address[1]}] {data}")

                    self.server_message(responses)

                except BlockingIOError:
                    pass
                except Exception as e:
                    self.return_exception(address, e)
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