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

    private connected: boolean = false;

    private constructor() {
        super();
        this.state = { joinAttempted: false };
        this.sockets = {};
    }

    public static getInstance(): Networking {
        if (this.instance == undefined) {
            this.instance = new Networking();
        }

        return this.instance;
    }

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

                this.connected = true;
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
                this.connected = false;
                this.sockets.signaling?.destroy();
                this.sockets.signaling = undefined;

                this.emit("stateChange", {
                    newState: "disconnected",
                    me: true
                });
            }

            else if (deserialized.type == "ended") {
                this.connected = false;
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
                this.connected = false;
                this.emit("stateChange", {
                    newState: "ended",
                    me: false
                });
            }
        }

        else if (deserialized.response == "error") {
            this.emit("error", deserialized.reason);

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
            // Step 3. Open a "generic" communication socket, and unlock send method

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

            stunSocket.on("message", (data) => {
                stunSocket.removeAllListeners();
                resolve(data.toString());
            });

            stunSocket.on("error", () => {
                stunSocket.removeAllListeners();
                reject("Unable to get your IP address.");
            });

            stunSocket.send(Buffer.from("getIP"), 3478);
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
     ///        CLIENT-SIDE METHODS        ///
    /////////////////////////////////////////

    /**
     * Starts a new meeting, and automatically joins it.
     * Upon improper usage, exceptions will be thrown.
     */
    public start() {
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
        if (this.connected != true) {
            throw new Error();
        }

        this.sockets.signaling?.write(JSON.stringify({request: "switch"}));
    }

    /**
     * This method will leave a meeting.
     * Upon improper usage, exceptions will be thrown.
     */
    public leave(): void {
        if (this.connected != true) {
            throw new Error();
        }

        this.sockets.signaling?.write(JSON.stringify({request: "leave"}));
    }

    /**
     * This method will attempt to end the meeting.
     * Upon improper usage, exceptions will be thrown.
     */
    public end(): void {
        if (this.connected != true) {
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
    public send(): void {
        if (this.canSend != true) {
            throw new Error();
        }

        console.log("Unimplemented");
    }

    /**
     * This method will call the callback when you get a new client message.
     * 
     * @param callback The callback to be called when you receive a message.
     */
    public onMessage(callback: any) {
        this.on("message", callback);
    }

    /**
     * This method will call the callback when the networking state changes.
     * 
     * @param callback The callback to be called when the networking state changes.
     */
    public onStateChange(callback: any) {
        this.on("stateChange", callback);
    }

    /**
     * This method will call the callback when the meeting host changes.
     * 
     * @param callback The callback to be called when the meeting host changes.
     */
    public onHostChange(callback: any) {
        this.on("hostChange", callback);
    }

    /**
     * This method will call the callback when an error occurs.
     * 
     * @param callback The callback to be called when an error occurs.
     */
    public onError(callback: any) {
        this.on("error", callback);
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

    // ICE State
    localAddress?: Address;
    remoteAddress?: Address;

    joinAttempted: boolean;
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