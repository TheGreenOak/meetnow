from tester import Connection

import threading


DEFAULT_SPORT = 13377
SIGNALING_PORT = 5060
CONN_TYPE = 1 # TCP
RECV_SIZE = 128

START = 1
JOIN = 2
SWITCH = 3
LEAVE = 4
END = 5

ID_INDEX = 0
PASSWORD_INDEX = 1


def print_menu():
    print("1 - Start")
    print("2 - Join")
    print("3 - Switch")
    print("4 - Leave")
    print("5 - End")
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

    print("Please enter the port number you'd like to connect from (press 1 for port 13377): ", end="")
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
            option = int(input(""))

            if option < 1 or option > 5:
                print("Invalid option.")
            else:
                if option == START: conn.send('{"request": "start"}')

                elif option == JOIN:
                    print("Enter meeting ID: ", end="")
                    meeting_id = input("")

                    print("Enter password: ", end="")
                    password = input("")

                    conn.send('{{"request": "join", "id":"{}", "password":"{}"}}'.format(meeting_id, password))
                    
                elif option == SWITCH: conn.send('{"request": "switch"}')
                elif option == LEAVE: conn.send('{"request": "leave"}')
                elif option == END: conn.send('{"request": "end"}')
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
