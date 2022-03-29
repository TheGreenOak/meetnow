import { Socket as UDPSocket, createSocket as createUDPSocket } from "dgram";
import { Socket as TCPSocket } from "net";
import { EventEmitter } from "events";

import ffi from "ffi-napi";
import ref from "ref-napi";
import path from "path";

const DEFAULT_IP = "meetnow.yeho.dev";
const STARTING_PORT = 34200;
const PORT_RANGE = 99;

const PORTS = {
    SIGNALING: 5060,
    STUN: 3478,
    ICE: 1673,
    TURN: 3479
}

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

    private readonly codec;

    private constructor() {
        super();

        this.state = {
            connected: false,
            joinAttempted: false,
            attempts: 0
        };
        this.sockets = {};

        this.codec = ffi.Library(path.join(__dirname, "..", "codec.so"), {
            "encode": ["string", ["string", "string", ref.types.ushort, ref.types.ushort, ref.types.uchar]],
            "decode": ["string", ["string", "string", ref.types.ushort, ref.types.ushort]] 
        });
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

      /////////////////////////////////////////
     ///         SOCKET GENERATORS         ///
    /////////////////////////////////////////

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
            this.sockets.signaling?.removeAllListeners();
            this.sockets.signaling?.destroy();
            this.sockets.signaling = undefined;
            this.emit("error", "Could not connect to signaling server.");
        });

        this.sockets.signaling.on("timeout", () => {
            this.sockets.signaling?.removeAllListeners();
            this.sockets.signaling?.destroy();
            this.sockets.signaling = undefined;
            this.emit("error", "Could not connect to signaling server.");
        });

        this.sockets.signaling.on("connect", () => {
            this.sockets.signaling?.setTimeout(0);
        });

        this.sockets.signaling.setTimeout(3000);
        this.sockets.signaling.connect(PORTS.SIGNALING, DEFAULT_IP);
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

        // Handle messages
        this.sockets.communication.on("message", (data) => {
            let msg = data.toString();

            if (msg == "HEARTBEAT") {
                this.sockets.communication?.send("HEARTBEAT");
            }

            if (this.state.remoteAddress!.ip == DEFAULT_IP) {
                if (msg[0] == "C") {
                    this.emit("message", msg.substring(1));
                }
            } else {
                this.emit("message", msg);
            }
        });

        // Handle socket errors
        this.sockets.communication.on("error", (err) => {
            this.sockets.communication?.close();
            this.sockets.communication = undefined;
            this.emit("comm-error", err);
        });

        // Send initial TURN message, and emit "ready"
        this.sockets.communication.once("connect", () => {
            if (this.state.remoteAddress?.ip == DEFAULT_IP) {
                this.sockets.communication?.send(JSON.stringify({
                    request: "connect",
                    id: this.state.id,
                    password: this.state.password
                }));
            }

            this.emit("ready");
        });
    }

      /////////////////////////////////////////
     ///         PEER COMMUNICATION        ///
    /////////////////////////////////////////

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
                    port: PORTS.TURN
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
     * This method will terminate the P2P/TURN connection that has been established.
     * Note, after calling this, you will no longer be able to communicate with the other user.
     */
    private async terminateConnection() {
        if (this.sockets.communication != undefined) {
            this.sockets.communication.send("F");
            this.sockets.communication.removeAllListeners();
            this.sockets.communication.close();
            this.sockets.communication = undefined;

            this.state.remoteAddress = undefined;
            if (this.state.localAddress) this.state.localAddress.port = -1;
        }
    }

      /////////////////////////////////////////
     ///      ICE NEGOTIATION METHODS      ///
    /////////////////////////////////////////

    /**
     * This methods attempt to negotiate a connection with the other peer.
     * Upon success, it will return an address.
     *
     * @returns A promise, which resolves to an IP and port
     */
    private negotiateConnection(): Promise<Address> {
        return new Promise<Address>((resolve, reject) => {
            this.sockets.ice = new TCPSocket();
            this.sockets.ice.connect(PORTS.ICE, DEFAULT_IP);

            this.sockets.ice.on("data", (data) => {
                this.handleICEMessage(data.toString()).then((success) => {
                    if (success) {
                        this.terminateICE();
                        resolve(this.state.remoteAddress!);
                    }
                })

                .catch(() => {
                    this.terminateICE();
                    reject("Unable to negotiate a connection with remote peer.");
                });
            });

            this.sockets.ice.once("error", () => {
                this.terminateICE();
                reject("Unable to negotiate a connection with remote peer.");
            });

            this.sockets.ice.once("timeout", () => {
                this.terminateICE();
                reject("Unable to connect to the ICE server.");
            });

            this.sockets.ice.on("connect", () => {
                this.sockets.ice?.setTimeout(0);
            });

            this.sockets.ice.setTimeout(3000);
            this.sockets.ice.write(JSON.stringify({
                request: "connect",
                id: this.state.id,
                password: this.state.password
            }));
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
            stunSocket.connect(PORTS.STUN, DEFAULT_IP);

            stunSocket.once("message", (data) => {
                stunSocket.removeAllListeners();
                stunSocket.close();
                resolve(JSON.parse(data.toString()).ip);
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
     * This method will generate a random source port.
     */
    private generatePort(): number {
        return Math.floor(Math.random() * PORT_RANGE) + STARTING_PORT;
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

      /////////////////////////////////////////
     ///            TERMINATORS            ///
    /////////////////////////////////////////

    /**
     * This method properly disposes of the ICE socket, and resets the state associated with it.
     */
    private terminateICE(): void {
        this.sockets.ice?.removeAllListeners();
        this.sockets.ice?.destroy();
        this.sockets.ice = undefined;

        this.state.iceStep = undefined;
        this.state.attempts = 0;
    }

    /**
     * This method will set the meeting state (id, password, host) to undefined.
     * Quick and handy shortcut, nothing else.
     */
    private invalidateMeetingState(): void {
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
    private handleSignalingMessage(data: string): void {
        if (data == "HEARTBEAT") {
            this.sockets.signaling?.write("HEARTBEAT");
            return; // No need for any further action.
        }

        let deserialized: ServerResponse = JSON.parse(data);

        // Handle server response to requests
        if (deserialized.response == "success") {
            if (deserialized.type == "created") {
                this.emit("state-change", {
                    newState: "created",
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

                this.emit("state-change", {
                    newState: "connected",
                    me: true,
                    host: deserialized.waiting
                });
            }

            else if (deserialized.type == "switched") {
                this.state.host = false;
                this.emit("host-change", false); // false indicates the user is no longer the host
            }

            else if (deserialized.type == "disconnected") {
                this.state.connected = false;
                this.invalidateMeetingState();
                this.terminateConnection();

                this.sockets.signaling?.destroy();
                this.sockets.signaling = undefined;

                this.emit("state-change", {
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

                this.emit("state-change", {
                    newState: "ended",
                    me: true
                });
            }
        }

        // Handle server events
        else if (deserialized.response == "info") {
            if (deserialized.type == "connected") {
                this.establishConnection();

                this.emit("state-change", {
                    newState: "connected",
                    me: false
                });
            }

            else if (deserialized.type == "switched") {
                this.state.host = true;
                this.emit("host-change", true); // true indicating the user is the new host
            }

            else if (deserialized.type == "disconnected") {
                this.state.host = true;
                this.terminateConnection();

                this.emit("state-change", {
                    newState: "disconnected",
                    me: false
                });
            }

            else if (deserialized.type == "ended") {
                this.state.connected = false;
                this.invalidateMeetingState();
                this.terminateConnection();

                this.emit("state-change", {
                    newState: "ended",
                    me: false
                });
            }
        }

        // Handle request errors
        else if (deserialized.response == "error") {
            this.emit("error", deserialized.reason);

            if (this.state.joinAttempted) {
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
    private handleICEMessage(data: string): Promise<boolean> {
        return new Promise<boolean>((resolve, reject) => {
            if (data == "HEARTBEAT") {
                this.sockets.ice?.write("HEARTBEAT");
                resolve(false); // No need for further action.
            }

            // Handle user message
            if (data[0] == "C") {
                data = data.substring(1);

                if (data[0] == "A") {
                    if (this.state.iceStep == "TURN" || this.state.iceStep == "PORT") {
                        resolve(true);
                    }

                    data = data.substring(1);
                }

                // The other peer has rejected the previous message.
                else if (data[0] == "R") {
                    if (this.state.iceStep == "TURN" || this.state.iceStep == "IP") {
                        reject("Client did not accept communication proposal.");
                    }

                    else if (this.state.iceStep == "PORT") {
                        // Unimplemented
                    }
                }

                // The other peer wants to use the TURN service.
                else if (data[0] == "T") {
                    this.state.remoteAddress = {
                        ip: DEFAULT_IP,
                        port: PORTS.TURN
                    };

                    this.sockets.ice?.write("A");
                    resolve(true);
                }

                // The other peer has sent in an IP request.
                if (data[0] == "I") {

                    // If we already have a remote address, it's TURN's address.
                    if (this.state.remoteAddress) {
                        this.state.iceStep = "TURN";
                        this.sockets.ice?.write("T");
                    } else {
                        this.state.remoteAddress = {
                            ip: data.substring(1),
                            port: -1
                        };

                        // If the state is undefined, the other peer initiated the negotiation.
                        if (this.state.iceStep == undefined) {
                            this.state.iceStep = "IP";
                            this.sockets.ice?.write("AI" + this.state.localAddress!.ip);

                        // Otherwise, we initiated it, and it's safe to assume they already have our IP.
                        } else {
                            this.state.iceStep = "PORT";
                            this.state.localAddress!.port = this.generatePort();
                            this.sockets.ice?.write("AP" + this.state.localAddress!.port);
                        }
                    }
                }

                else if (data[0] == "P") {
                    this.state.remoteAddress!.port = parseInt(data.substring(1));

                    // If the state is IP, the other has already received our port.
                    if (this.state.iceStep == "PORT") {
                        this.sockets.ice?.write("A");
                        resolve(true);

                    // Otherwise, we need to send our port as-well.
                    } else {
                        do {
                            this.state.localAddress!.port = this.generatePort();
                        } while (this.state.localAddress!.port == this.state.remoteAddress!.port);

                        this.state.iceStep = "PORT";
                        this.sockets.ice?.write("AP" + this.state.localAddress!.port);
                    }
                }

                else {
                    reject("Client sent an invalid message");
                }

            // Handle server response
            } else {
                let deserialized: ServerResponse = JSON.parse(data);

                if (deserialized.response == "info" && deserialized.type == "connected") {
                    if (this.state.remoteAddress) {
                        this.state.iceStep = "TURN";
                        this.sockets.ice?.write("T");
                    } else {
                        this.state.iceStep = "IP";
                        this.sockets.ice?.write("I" + this.state.localAddress!.ip);
                    }
                }

                else if (deserialized.response == "error") {
                    reject("An ICE error occurred");
                }
            }

            return false;
        });
    }

      /////////////////////////////////////////
     ///         RENDERER METHODS          ///
    /////////////////////////////////////////

    /**
     * Starts a new meeting, and automatically joins it.
     * Upon improper usage, exceptions will be thrown.
     */
    public start(): void {
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
    public join(id: string, password: string): void {
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

      /////////////////////////////////////////
     ///           CODEC METHODS           ///
    /////////////////////////////////////////

    public encode(frame: string, previousFrame: string, height: number, width: number, threshold: number): string | null {
        return this.codec.encode(frame, previousFrame, height, width, threshold);
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
    iceStep?: ICEState;
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
type ICEState = "IP" | "PORT" | "TURN";
