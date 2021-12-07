from tester import Connection


DEFAULT_SPORT = 13377
SIGNALING_PORT = 5060
CONN_TYPE = 1 # TCP
RECV_SIZE = 128

START = 1
JOIN = 2
SWITCH = 3
LEAVE = 4
END = 5


def print_menu():
    print("1 - Start")
    print("2 - Join")
    print("3 - Switch")
    print("4 - Leave")
    print("5 - End")
    print()


def main():
    print("Welcome to the basic server tester.")

    print("Please enter the IP address of the server you want to connect to (press 1 if 127.0.0.1): ", end="")
    ip = input("")
    if ip == "1": ip = "localhost"
    print()

    conn = Connection(ip, DEFAULT_SPORT, SIGNALING_PORT, CONN_TYPE)

    try:
        conn.connect()
        print("Connection established.")
        print_menu()

        while True:
            print("Select an option: ", end="")
            option = int(input(""))

            if option < 1 or option > 5:
                print("Invalid option.")
            else:
                if option == START:
                    conn.send('{"request": "start"}')
                    print("Response: ", conn.recv(RECV_SIZE))
                elif option == JOIN:
                    print("Enter meeting ID: ", end="")
                    meeting_id = input("")

                    print("Enter password: ", end="")
                    password = input("")

                    conn.send('{{"request": "join", "id":"{}", "password":"{}"}}'.format(meeting_id, password))
                    print("Response: ", conn.recv(RECV_SIZE))
                elif option == SWITCH:
                    conn.send('{"request": "switch"}')
                    print("Response: ", conn.recv(RECV_SIZE))
                elif option == LEAVE:
                    conn.send('{"request": "leave"}')
                    print("Response: ", conn.recv(RECV_SIZE))
                elif option == END:
                    conn.send('{"request": "end"}')
                    print("Response: ", conn.recv(RECV_SIZE))
    except KeyboardInterrupt:
        print("Stopping...")
    except TimeoutError:
        print("Couldn't connect to server. Aborting!")
    except:
        print("An unknown error occurred.")
    finally:
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()
