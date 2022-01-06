from tester import Connection

import threading


DEFAULT_SPORT = 13477
SIGNALING_PORT = 1673
CONN_TYPE = 1 # TCP
RECV_SIZE = 128

CONNECT = 1
SEND = 2
DISCONNECT = 3
HEARTBEAT = 4

ID_INDEX = 0
PASSWORD_INDEX = 1


def print_menu():
    print("1 - Connect")
    print("2 - Send")
    print("3 - Disconnect")
    print("4 - Heartbeat")
    print()


def recv_continously(conn):
    try:
        while conn.keep_running:
            try:
                data = conn.recv(1024)
                if not data: # If the server has closed the connection, we'll get empty data
                    break

                print("\n[SERVER]", data)
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

    print("Please enter the port number you'd like to connect from (press 1 for port 13477): ", end="")
    sport = int(input(""))
    if sport == 1: sport = DEFAULT_SPORT
    print()

    conn = Connection(ip, sport, SIGNALING_PORT, CONN_TYPE)

    try:
        conn.connect()
        conn.toggle_blocking_mode()

        # We make a new thread for receiving data from the server without interrupting the main thread
        recv_thread = threading.Thread(target=recv_continously, args=(conn,))
        recv_thread.start()

        print("Connection established.")
        print_menu()

        while True:
            try:
                option = int(input(""))
            except ValueError:
                option = -1

            if option < 1 or option > 4:
                print("Invalid option.")
            else:
                if option == CONNECT:
                    print("Enter meeting ID: ", end="")
                    meeting_id = input("")

                    print("Enter password: ", end="")
                    password = input("")

                    conn.send('{{"request": "connect", "id":"{}", "password":"{}"}}'.format(meeting_id, password))
                
                elif option == SEND:
                    print("Enter message: ", end="")
                    message = input("")

                    conn.send('{{"request": "send", "message":"{}"}}'.format(message))
                
                elif option == DISCONNECT: conn.send('{"request": "disconnect"}')
                elif option == HEARTBEAT: conn.send("HEARTBEAT")
    except KeyboardInterrupt:
        print("Stopping...")
    except TimeoutError:
        print("Couldn't connect to server. Aborting!")
    except:
        print("An unknown error occurred.")
    finally:
        conn.keep_running = False
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()
