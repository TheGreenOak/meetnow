from tester import Connection

import threading


SPORT = 13377
DPORT = 3478
CONN_TYPE = 2 # UDP


def send_continously(conn):
    try:
        while conn.keep_running:
            conn.send(input(""))
    except:
        print("Server aborted connection.")
        

def recv_continously(conn):
    try:
        while conn.keep_running:
            try:
                data = conn.recv(1024)
                if not data: # If the server has closed the connection, we'll get empty data
                    break

                print("[SERVER]", data)
            except BlockingIOError:
                pass
    except:
        print("Server aborted connection.")

def main():
    print("Welcome to the basic server tester.")

    print("Please enter the IP address of the server you want to connect to (press 1 if 127.0.0.1): ", end="")
    ip = input("")
    if ip == "1": ip = "localhost"
    print()

    conn = Connection(ip, SPORT, DPORT, CONN_TYPE)

    try:
        conn.connect()
        print("Connection established.")

        # Making this socket non-blocking so that we can abort the tester
        conn.toggle_blocking_mode() 

        # We make a new thread for receiving data from the server without interrupting the main thread
        recv_thread = threading.Thread(target=recv_continously, args=(conn,))
        recv_thread.start()

        try:
            send_continously(conn)
        except KeyboardInterrupt:
            conn.keep_running = False
            recv_thread.join()
    except TimeoutError:
        print("Couldn't connect to server. Aborting!")
    except:
        print("Connection refused. Aborting!")
    finally:
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()
