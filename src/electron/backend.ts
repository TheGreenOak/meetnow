import { Socket as UDPSocket, createSocket as createUDPSocket } from "dgram";
import { Socket as TCPSocket } from "net";
import { EventEmitter } from "events";

const DEFAULT_IP = "127.0.0.1";

/*
yeho's little think box
-----------------------

P2P/TURN Protocol:
First char is the identifier char

A - AUDIO
V - VIDEO
C - CHAT MESSAGE
I - INFO (Used for identification)
F - GOODBYE (F stands for FIN)
T - TEST

------------------------

establishConnection() ; emits event "ready", or "fail"
  -> Gets IP address (if not in cache) | getIP(): Promise<string>
  -> Negotiates connection with remote client | negotiateConnection(): Promise<Address>
    -> Gets IP & port from the remote
    -> Tests connection | testConnection(): Promise<void> ; error means failed test
    -> 3 tests allowed before falling back to TURN
  -> Creates communication socket

------------------------

ICE Protocol:
I [ip]
P [port]
T (TURN)
A (accepted)
R (rejected)

*/

/**
 * Stateful, event emitting, singleton class for handling all client-side this.
 */
export class Networking extends EventEmitter {
    private static instance?: Networking;
    private state: NetworkingState;
    private sockets: NetworkingSockets;

    private constructor() {
        super();

        this.state = {
            connected: false,
            joinAttempted: false,
            attempts: 0
        };
        this.sockets = {};
    }

    /**
     * Acquire the singleton instance of this class.
     */
    public static getInstance(): Networking {
        if (this.instance == undefined) {
            this.instance = new Networking();
        }

        return this.instance;
    }

    /**
     * This method makes a new Signaling socket, and binds all event listeners.
     * It will also automatically attempt connecting to the Signaling server.
     * 
     * Note, if the connection fails, the socket will be destroyed, and an error event will be emitted.
     */
    private makeSignalingSocket() {
        this.sockets.signaling = new TCPSocket();

        this.sockets.signaling.on("data", (data) => this.handleSignalingMessage(data.toString()));
        this.sockets.signaling.on("error", () => {
            this.sockets.signaling?.destroy();
            this.sockets.signaling = undefined;
            this.emit("error", "Could not connect to signaling server.");
        });

        this.sockets.signaling.connect(5060, DEFAULT_IP);
    }

    /**
     * This methods will make a new communication socket, and bind all event listeners to it.
     * 
     * @param addr The address of the remote
     */
    private makeCommunicationSocket(addr: Address, sourcePort?: number) {
        this.sockets.communication = createUDPSocket("udp4");
        if (sourcePort) this.sockets.communication.bind(sourcePort);
        this.sockets.communication.connect(addr.port, addr.ip);

        this.sockets.communication.on("message", (data) => { this.emit("message", data); });
        this.sockets.communication.on("error", () => {
            this.sockets.communication?.close();
            this.sockets.communication = undefined;
            this.emit("comm-error", "There was an error with the UDP communication socket.");
        });

        this.sockets.communication.once("connect", () => { this.emit("ready"); });
    }

    /**
     * This method will attempt to establish a P2P/TURN connection with the other user.
     * 
     * Firstly, it will attempt to get your public IP address.
     * Then, it will attempt to negotiate a connection with the other user.
     * Once the details have been negotiated and tested, a UDP socket will be created,
     * and the connection will be established.
     * 
     * The public IP will get stored in cache.
     */
    private async establishConnection() {
        // Step 1. Get IP address
        if (this.state.localAddress == undefined) {
            this.getIP().then((ip) => {
                this.state.localAddress = { ip: ip, port: -1 };  
            })

            .catch(() => {
                this.state.remoteAddress = {
                    ip: DEFAULT_IP,
                    port: 3479
                };
            });
        }

        // Step 2. Negotitate connection via ICE
        this.negotiateConnection().then((remoteAddress) => {
            this.makeCommunicationSocket(remoteAddress, this.state.localAddress?.port); // Step 3. Create the socket
        })

        .catch(() => {
            this.emit("comm-error", "There was an error with the UDP communication socket.");
        });
    }

    /**
     * This method attempts to get your public IP from the STUN service.
     * 
     * @returns An IP address promise, which resolves to an IP address string
     */
    private getIP(): Promise<string> {
        return new Promise<string>((resolve, reject) => {
            let stunSocket: UDPSocket = createUDPSocket("udp4");
            stunSocket.connect(3478, DEFAULT_IP);

            stunSocket.once("message", (data) => {
                stunSocket.removeAllListeners();
                stunSocket.close();
                resolve(data.toString());
            });

            stunSocket.once("error", () => {
                stunSocket.removeAllListeners();
                stunSocket.close();
                reject("Unable to get your IP address.");
            });

            stunSocket.once("connect", () => {
                stunSocket.send("getIP");
            });
        });
    }

    /**
     * This methods attempt to negotiate a connection with the other peer.
     * Upon success, it will return an address.
     * 
     * @returns A promise, which resolves to an IP and port
     */
    private negotiateConnection(): Promise<Address> {
        return new Promise<Address>((resolve, reject) => {
            this.sockets.ice = new TCPSocket();
            this.sockets.ice.connect(1673, DEFAULT_IP);

            this.sockets.ice.on("data", (data) => {
                if (this.handleICEMessage(data.toString())) {
                    this.sockets.ice?.removeAllListeners();
                    this.sockets.ice?.destroy();
                    this.sockets.ice = undefined;

                    resolve(this.state.remoteAddress!);
                }
            });

            this.sockets.ice.once("error", () => {
                this.sockets.ice?.removeAllListeners();
                this.sockets.ice?.destroy();
                this.sockets.ice = undefined;

                reject("Unable to negotiate a connection with remote peer.");
            });

            this.sockets.ice.write(JSON.stringify({
                request: "connect",
                id: this.state.id,
                password: this.state.password
            }));
        });
    }

    /**
     * This method will test the remote address by sending two test messages.
     * 
     * If the promise resolved, the connection succeded. Otherwise, it failed upon being rejected.
     */
    private testConnection(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            // Unimplemented
        });
    }

    /**
     * This method will terminate the P2P/TURN connection that has been established.
     * Note, after calling this, you will no longer be able to communicate with the other user.
     */
    private async terminateConnection() {
        if (this.sockets.communication == undefined) {
            throw new Error();
        }

        this.sockets.communication.send("F");
        this.sockets.communication.removeAllListeners();
        this.sockets.communication.close();
        this.sockets.communication = undefined;
    }

    /**
     * This method will set the meeting state (id, password, host) to undefined.
     * Quick and handy shortcut, nothing else.
     */
    private invalidateMeetingState() {
        this.state.id = undefined;
        this.state.password = undefined;
        this.state.host = undefined;
    }

      /////////////////////////////////////////
     ///      SOCKET MESSAGE HANDLERS      ///
    /////////////////////////////////////////

    /**
     * This methods handles any and all incoming signaling messages.
     * If necessary, it will emit events according to the message.
     * 
     * @param data The message data.
     */
    private handleSignalingMessage(data: string) {
        if (data == "HEARTBEAT") {
            this.sockets.signaling?.write("HEARTBEAT");
            return; // No need for any further action.
        }

        let deserialized: ServerResponse = JSON.parse(data);

        // Handle server response to requests
        if (deserialized.response == "success") {
            if (deserialized.type == "created") {
                this.emit("stateChange", {
                    newState: "started",
                    me: true,
                    id: deserialized.id,
                    password: deserialized.password
                });
            }

            else if (deserialized.type == "connected") {
                if (!deserialized.waiting) {
                    this.establishConnection();
                }

                this.state.connected = true;
                this.state.host = deserialized.waiting;
                this.state.joinAttempted = false;

                this.emit("stateChange", {
                    newState: "connected",
                    me: true,
                    host: deserialized.waiting
                });
            }

            else if (deserialized.type == "switched") {
                this.state.host = false;
                this.emit("hostChange", false); // false indicates the user is no longer the host
            }

            else if (deserialized.type == "disconnected") {
                this.state.connected = false;
                this.invalidateMeetingState();
                this.terminateConnection();

                this.sockets.signaling?.destroy();
                this.sockets.signaling = undefined;

                this.emit("stateChange", {
                    newState: "disconnected",
                    me: true
                });
            }

            else if (deserialized.type == "ended") {
                this.state.connected = false;
                this.invalidateMeetingState();
                this.terminateConnection();

                this.sockets.signaling?.destroy();
                this.sockets.signaling = undefined;

                this.emit("stateChange", {
                    newState: "ended",
                    me: true
                });
            }
        }

        // Handle server events
        else if (deserialized.response == "info") {
            if (deserialized.type == "connected") {
                this.establishConnection();

                this.emit("newState", {
                    newState: "connected",
                    me: false
                });
            }

            else if (deserialized.type == "switched") {
                this.state.host = true;
                this.emit("hostChange", true); // true indicating the user is the new host
            }

            else if (deserialized.type == "disconnected") {
                this.state.host = true;
                this.terminateConnection();
                
                this.emit("stateChange", {
                    newState: "disconnected",
                    me: false
                });
            }

            else if (deserialized.type == "ended") {
                this.state.connected = false;
                this.invalidateMeetingState();
                this.terminateConnection();

                this.emit("stateChange", {
                    newState: "ended",
                    me: false
                });
            }
        }

        // Handle request errors
        else if (deserialized.response == "error") {
            this.emit("error", deserialized.reason);

            // If we have attempted joining a meeting, and we got a join error, invalidate the local meeting state.
            if ((deserialized.reason?.search("meeting ID") != -1 || deserialized.reason?.search("password") != -1)
                && this.state.joinAttempted) {
                
                this.state.joinAttempted = false;
                this.invalidateMeetingState();
            }
        }
    }

    /**
     * This method handles any and all incoming ICE messages.
     * 
     * @param data The message data.
     * @returns If connection details were tested and approved.
     */
    private handleICEMessage(data: string): boolean {
        if (data == "HEARTBEAT") {
            this.sockets.ice?.write("HEARTBEAT");
            return false; // No need for further action.
        }

        // Handle user message
        if (data[0] == "C") {
            data = data.substring(1);


        // Handle server response
        } else {
            let deserialized: ServerResponse = JSON.parse(data);

            if (deserialized.response == "success") {
                if (deserialized.type == "connected") {
                    return false;
                }

                else if (deserialized.type == "disconnected") {
                    
                }
            }

            else if (deserialized.response == "info") {
                if (deserialized.type == "connected") {
                    if (this.state.remoteAddress) {
                        this.sockets.ice?.write("T");
                    } else {
                        this.sockets.ice?.write("I" + this.state.localAddress!.ip);
                    }
                }

                else if (deserialized.type == "disconnected") {

                }
            }

            else if (deserialized.response == "error") {
                this.state.remoteAddress = {
                    ip: DEFAULT_IP,
                    port: 3479
                };

                return true;
            }
        }

        return false;
    }

      /////////////////////////////////////////
     ///         RENDERER METHODS          ///
    /////////////////////////////////////////

    /**
     * Starts a new meeting, and automatically joins it.
     * Upon improper usage, exceptions will be thrown.
     */
    public start() {
        if (this.state.connected) {
            throw new Error();
        }

        if (this.sockets.signaling == undefined) {
            this.makeSignalingSocket();
        }

        this.sockets.signaling?.write(JSON.stringify({request: "start"}));
    }

    /**
     * This method will attempt to join a meeting.
     * Upon improper usage, exceptions will be thrown.
     * 
     * @param id The meeting ID.
     * @param password The meeting password.
     */
    public join(id: string, password: string) {
        if (this.state.connected || this.state.joinAttempted) {
            throw new Error();
        }

        if (this.sockets.signaling == undefined) {
            this.makeSignalingSocket();
        }
        
        this.state.id = id;
        this.state.password = password;
        this.state.joinAttempted = true;

        this.sockets.signaling?.write(JSON.stringify({request: "join", id: id, password: password}));
    }

    /**
     * This method will attempt to switch the meeting's host, thereby granting the other user ending rights.
     * Upon improper usage, exceptions will be thrown.
     */
    public switch(): void {
        if (this.state.connected != true || this.state.host == false) {
            throw new Error();
        }

        this.sockets.signaling?.write(JSON.stringify({request: "switch"}));
    }

    /**
     * This method will leave a meeting.
     * Upon improper usage, exceptions will be thrown.
     */
    public leave(): void {
        if (this.state.connected != true) {
            throw new Error();
        }

        this.sockets.signaling?.write(JSON.stringify({request: "leave"}));
    }

    /**
     * This method will attempt to end the meeting.
     * Upon improper usage, exceptions will be thrown.
     */
    public end(): void {
        if (this.state.connected != true || this.state.host == false) {
            throw new Error();
        }

        this.sockets.signaling?.write(JSON.stringify({request: "end"}));
    }

    /**
     * This method will send a message to the user's peer.
     * You may call this method after a "ready" event has been emitted.
     * 
     * Upon improper usage, exceptions will be thrown.
     * 
     * @param message The message to send.
     */
    public send(data: string): void {
        if (this.sockets.communication == undefined) {
            throw new Error();
        }

        this.sockets.communication.send(Buffer.from(data));
    }
};

  /////////////////////////////////////////
 ///          TYPESCRIPT TYPES         ///
/////////////////////////////////////////

type NetworkingSockets = {
    signaling?: TCPSocket;
    ice?: TCPSocket;
    communication?: UDPSocket;
};

type NetworkingState = {
    // Signaling State
    id?: string;
    password?: string;
    host?: boolean;
    
    connected: boolean;
    joinAttempted: boolean;

    // ICE State
    attempts: number;
    localAddress?: Address;
    remoteAddress?: Address;
};

export type SignalingState = {
    newState: ResponseType;
    me: boolean;

    id?: string;
    password?: string;
    host?: boolean;
};

type ServerResponse = {
    response: ResponseStatus;
    type: ResponseType;
    reason?: string; // Used for errors

    id?: string;
    password?: string;
    waiting?: boolean;
};

type Address = {
    ip: string;
    port: number;
};

type ResponseStatus = "success" | "info" | "error";
type ResponseType = "created" | "connected" | "switched" | "disconnected" | "ended";
