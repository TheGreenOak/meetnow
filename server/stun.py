from server import UDPServer
from json import dumps as serialize

SERVER_PORT = 3478 # The STUN port - https://www.3cx.com/blog/voip-howto/stun-voip-1/

class Stun(UDPServer):
    """
    The stun server is responsible for telling the user his ip.
    In the future in addition to the ip the server will tell the user if his NAT is allowing P2P.
    """

    def __init__(self, port):
        super().__init__(port)

    def run(self):
        try:
            while True:
                try:
                    # In UDP, there are no sockets. Therefore, we just need to receive data.
                    data, address = self.recv()
                    print(f"[{address[0]}:{address[1]}] {data.decode()}")
                    ip = serialize({"ip": address[0]}).encode()
                    self.send(address, ip)
                except BlockingIOError:
                    pass
        except KeyboardInterrupt:
            self.keep_running = False




def main():
    server = Stun(SERVER_PORT)
    server.start()
    server.toggle_blocking_mode()

    try:
        print("STUN server started")
        server.run() # Blocking method - will continue running until the admin presses Ctrl+C
    except: pass

    print("\nStopping server...")
    server.stop()

if __name__ == "__main__":
    main()