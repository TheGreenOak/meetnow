from server import UDPServer
from threading import Thread, Event
from json import loads as deserialize, dumps as serialize

 # TODO: 
SERVER_PORT = 3479 # The TURN port except for the last number  - https://www.3cx.com/blog/voip-howto/stun-voip-1/



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
    
    connected_users = []

    def __init__(self, port):
        super().__init__(port)

        self.users = {} # {"user_uuid", (127.0.0.1, 13377)}

    def run(self):
        try:
            while True:
                try:
                    # In UDP, there are no sockets. Therefore, we just need to receive data.
                    data, address = self.recv()
                    data = data.decode()
                    if address not in self.connected_users:
                        self.connected_users.append(address)
                        
                    print("[{}:{}] {}".format(address[0], address[1], data))

                    try:
                        dest = self.check_meeting_valid(address, data)
                    except Exception as e:
                        self.return_exception(address, e)
                    
                    self.forward(data, dest)

                except BlockingIOError:
                    pass
        except KeyboardInterrupt:
            self.keep_running = False

            print("\nStopping server...")
            self.stop()

    def check_meeting_valid(self):
        if 1!=1: # the meeting id is not in the database
            raise NoMeetingID
        if 1!= 1: # if the password is incorrect
            raise WrongPassword
        if 1!=1: # if there is only 1 user
            raise AloneInMeeting
        if 1!=1: # check if the user is connected to the turn server
            raise OtherUserNotConnected
        # return participant to send to
    
    def return_exception(self, address, exception):
        exception = "S" + exception
        self.send(address, exception)

    def forward(self, address, data):
        data = "U" + data
        self.send(address, data)
    



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