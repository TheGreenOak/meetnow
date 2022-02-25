import { Socket } from "net";
import { EventEmitter } from "events";

/**
 * Stateful, event emitting, singleton class for handling all client-side networking.
 */
export class Networking extends EventEmitter {
    private static instance?: Networking;
    private static signalingSocket?: Socket;

    private static connected: boolean = false;
    private static canSend: boolean = false; 

    private constructor() {
        super();
    }

    public static getInstance(): Networking {
        if (this.instance == null) {
            this.instance = new Networking();
        }

        return this.instance;
    }

    public handleSignalingMessage(data: string) {
        if (data == "HEARTBEAT") {
            Networking.signalingSocket?.write("HEARTBEAT");
            return; // No need for any further action.
        }

        let deserialized: SignalingServerResponse = JSON.parse(data);

        if (deserialized.response == "success") {
            if (deserialized.type == "created") {
                this.emit("stateChange", {
                    newState: "started",
                    me: true,
                    id: deserialized.id,
                    password: deserialized.password
                });
            }

            if (deserialized.type == "joined") {
                if (!deserialized.host) {
                    
                }

                Networking.connected = true;
                this.emit("stateChange", {
                    newState: "joined",
                    me: true,
                    host: deserialized.host
                });
            }

            if (deserialized.type == "switched") {
                this.emit("hostChange", false); // false indicates the user is no longer the host
            }

            if (deserialized.type == "left") {
                Networking.connected = false;
                Networking.signalingSocket?.destroy();
                Networking.signalingSocket = undefined;

                this.emit("stateChange", {
                    newState: "left",
                    me: true
                });
            }

            if (deserialized.type == "ended") {
                Networking.connected = false;
                Networking.signalingSocket?.destroy();
                Networking.signalingSocket = undefined;

                this.emit("stateChange", {
                    newState: "ended",
                    me: true
                });
            }
        }

        else if (deserialized.response == "info") {
            if (deserialized.type == "joined") {
                // do something about it
            }

            if (deserialized.type == "switched") {
                this.emit("hostChange", true); // true indicating the user is the new host
            }

            if (deserialized.type == "left") {
                this.emit("stateChange", {
                    newState: "left",
                    me: false
                });
            }

            if (deserialized.type == "ended") {
                Networking.connected = false;
                this.emit("stateChange", {
                    newState: "ended",
                    me: false
                });
            }
        }

        else if (deserialized.response == "error") {
            this.emit("error", deserialized?.reason);
        }
    }

    public makeSignalingSocket() {
        Networking.signalingSocket = new Socket();

        Networking.signalingSocket.on("data", (data) => handleSignalingMessage(data.toString()));
        Networking.signalingSocket.on("error", () => {
            Networking.signalingSocket?.destroy();
            Networking.signalingSocket = undefined;
            this.emit("error", "Could not connect to signaling server.");
        });

        Networking.signalingSocket.connect(5060, "127.0.0.1");
    }


      /////////////////////////////////////////
     ///        CLIENT-SIDE METHODS        ///
    /////////////////////////////////////////

    /**
     * Starts a new meeting, and automatically joins it.
     * Upon improper usage, exceptions will be thrown.
     */
    public start() {
        if (Networking.signalingSocket == undefined) {
            makeSignalingSocket();
        }

        Networking.signalingSocket?.write(JSON.stringify({request: "start"}));
    }

    /**
     * This method will attempt to join a meeting.
     * Upon improper usage, exceptions will be thrown.
     */
    public join(id: string, password: string) {
        if (Networking.signalingSocket == undefined) {
            makeSignalingSocket();
        }

        Networking.signalingSocket?.write(JSON.stringify({request: "join", id: id, password: password}));
    }

    /**
     * This method will attempt to switch the meeting's host, thereby granting the other user ending rights.
     * Upon improper usage, exceptions will be thrown.
     */
    public switch(): void {
        if (Networking.connected != true) {
            throw new Error();
        }

        Networking.signalingSocket?.write(JSON.stringify({request: "switch"}));
    }

    /**
     * This method will leave a meeting.
     * Upon improper usage, exceptions will be thrown.
     */
    public leave(): void {
        if (Networking.connected != true) {
            throw new Error();
        }

        Networking.signalingSocket?.write(JSON.stringify({request: "leave"}));
    }

    /**
     * This method will attempt to end the meeting.
     * Upon improper usage, exceptions will be thrown.
     */
    public end(): void {
        if (Networking.connected) {
            throw new Error();
        }

        Networking.signalingSocket?.write(JSON.stringify({request: "end"}));
    }

    /**
     * This method will send a message to the user's peer.
     * It will only work after being unlocked  by a join method.
     * 
     * Upon improper usage, exceptions will be thrown.
     */
    public send(): void {
        if (Networking.canSend != true) {
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

type SignalingServerResponse = {
    response: SignalingResponseStatus;
    type: SignalingResponseType;
    reason?: string; // Used for errors

    id?: string;
    password?: string;
    host?: boolean;
}

export type SignalingState = {
    newState: SignalingResponseType;
    me: boolean;

    id?: string;
    password?: string;
    host?: boolean;
}

type SignalingResponseStatus = "success" | "info" | "error";
type SignalingResponseType = "created" | "joined" | "switched" | "left" | "ended";

// Perhaps make a better function system?

function makeSignalingSocket() {
    Networking.getInstance().makeSignalingSocket();
}

function handleSignalingMessage(data: string) {
    Networking.getInstance().handleSignalingMessage(data);
}