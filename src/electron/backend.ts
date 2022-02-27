import { Socket as UDPSocket, createSocket as createUDPSocket } from "dgram";
import { Socket as TCPSocket } from "net";
import { EventEmitter } from "events";

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
            joinAttempted: false
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

    public makeSignalingSocket() {
        this.sockets.signaling = new TCPSocket();

        this.sockets.signaling.on("data", (data) => this.handleSignalingMessage(data.toString()));
        this.sockets.signaling.on("error", () => {
            this.sockets.signaling?.destroy();
            this.sockets.signaling = undefined;
            this.emit("error", "Could not connect to signaling server.");
        });

        this.sockets.signaling.connect(5060, "127.0.0.1");
    }

    public async establishConnection() {
        // Step 1. Get IP address
        if (this.state.localAddress == undefined) {
            this.state.localAddress = {
                ip: await this.getIP()
            }
        }

        // Step 2. Negotitate connection via ICE
        this.negotiateConnection().then((remoteAddress) => {
            // Step 3. Open a "generic" communication socket

        })

        .catch((err) => {

        });
    }

    /**
     * This method attempts to get your public IP from the STUN service.
     * 
     * @returns An IP address promise, which resolves to an IP address string
     */
    public getIP(): Promise<string> {
        return new Promise<string>((resolve, reject) => {
            let stunSocket: UDPSocket = createUDPSocket("udp4");
            stunSocket.connect(3478);

            stunSocket.once("message", (data) => {
                resolve(data.toString());
            });

            stunSocket.once("error", () => {
                reject("Unable to get your IP address.");
            });

            stunSocket.once("connect", () => {
                stunSocket.send("getIP");
            });
        });
    }

    public negotiateConnection() {
        return new Promise<Address>((resolve, reject) => {
            let remoteIP: string | undefined;
            let remotePort: number | undefined;

            let iceSocket: TCPSocket = new TCPSocket();
            iceSocket.connect(1673, "127.0.0.1");

            iceSocket.on("data", (data) => {
                this.handleICEMessage(data.toString());
            });

            iceSocket.on("error", () => {
                iceSocket.removeAllListeners();
                reject("Unable to negotiate a connection with remote peer.");
            });

            this.once("remoteIP", (ip: string) => { remoteIP = ip });
            this.once("remotePort", (port: number) => { remotePort = port });
            
            this.once("negotiated", (type: ConnectionType) => {

            });
        });
    }

      /////////////////////////////////////////
     ///      SOCKET MESSAGE HANDLERS      ///
    /////////////////////////////////////////

    public handleSignalingMessage(data: string) {
        if (data == "HEARTBEAT") {
            this.sockets.signaling?.write("HEARTBEAT");
            return; // No need for any further action.
        }

        let deserialized: ServerResponse = JSON.parse(data);

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
                this.emit("hostChange", false); // false indicates the user is no longer the host
            }

            else if (deserialized.type == "disconnected") {
                this.state.connected = false;
                this.sockets.signaling?.destroy();
                this.sockets.signaling = undefined;

                this.emit("stateChange", {
                    newState: "disconnected",
                    me: true
                });
            }

            else if (deserialized.type == "ended") {
                this.state.connected = false;
                this.sockets.signaling?.destroy();
                this.sockets.signaling = undefined;

                this.emit("stateChange", {
                    newState: "ended",
                    me: true
                });
            }
        }

        else if (deserialized.response == "info") {
            if (deserialized.type == "connected") {
                this.emit("newState", {
                    newState: "connected",
                    me: false
                });
            }

            else if (deserialized.type == "switched") {
                this.emit("hostChange", true); // true indicating the user is the new host
            }

            else if (deserialized.type == "disconnected") {
                this.emit("stateChange", {
                    newState: "disconnected",
                    me: false
                });
            }

            else if (deserialized.type == "ended") {
                this.state.connected = false;
                this.emit("stateChange", {
                    newState: "ended",
                    me: false
                });
            }
        }

        else if (deserialized.response == "error") {
            this.emit("error", deserialized.reason);

            // If we have attempted joining a meeting, and we got a join error, invalidate the local meeting state.
            if ((deserialized.reason?.search("meeting ID") != -1 || deserialized.reason?.search("password") != -1)
                && this.state.joinAttempted) {
                
                this.state.joinAttempted = false;
                this.state.id = undefined;
                this.state.password = undefined;
            }
        }
    }

    public handleICEMessage(data: string) {
        if (data == "HEARTBEAT") {
            this.sockets.ice?.write("HEARTBEAT");
            return; // No need for further action.
        }

        // Handle user message
        if (data[0] == "C") {

        // Handle server response
        } else {
            let deserialized: ServerResponse = JSON.parse(data);

            if (deserialized.response == "success") {
                if (deserialized.type == "connected") {
                    
                }

                else if (deserialized.type == "disconnected") {

                }
            }

            else if (deserialized.response == "info") {

            }

            else if (deserialized.response == "error") {

            }
        }
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
     */
    public join(id: string, password: string) {
        if (this.state.connected || this.state.joinAttempted) {
            throw new Error();
        }

        if (this.sockets.signaling == undefined) {
            this.makeSignalingSocket();
        }

        this.sockets.signaling?.write(JSON.stringify({request: "join", id: id, password: password}));

        this.state.id = id;
        this.state.password = password;
        this.state.joinAttempted = true;
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
     * It will only work after being unlocked  by a join method.
     * 
     * Upon improper usage, exceptions will be thrown.
     */
    public send(data: string): void {
        if (this.sockets.communication == undefined) {
            throw new Error();
        }

        this.sockets.communication.send(Buffer.from(data));
    }
};

  /////////////////////////////////////////
 ///          TypeScript Types         ///
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
    port?: number;
};

type ResponseStatus = "success" | "info" | "error";
type ResponseType = "created" | "connected" | "switched" | "disconnected" | "ended";