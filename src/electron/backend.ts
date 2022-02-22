import { Socket } from "net";
import { EventEmitter } from "events";

/*
yeho's little think box
-----------------------

maybe create an event emitter for App.svelte to handle
it will emit stateChange events and such.

for instance, .on("stateChange", (newState) => {
    if newState is waiting:
    drop client in a fake meeting, waiting for someone to arrive.

    if newState is connecting:
    show client the connection is being made

    if newState is connected:
    unlock send method, and allow for communication

    if newState is disconnected:
    drop other client

    if newState is ended:
    drop yourself from the meeting
});

.on("hostChange", () => {
    unlock end meeting button.
});
*/

/**
 * Stateful singleton class for handling all client-side networking.
 */
export class Networking extends EventEmitter {
    private static instance?: Networking;
    private signalingSocket?: Socket;

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
            this.signalingSocket?.write("HEARTBEAT");
            return; // No need for any further action.
        }

        let deserialized: SignalingServerResponse = JSON.parse(data);

        if (deserialized.response == "success") {
            if (deserialized.type == "created") {
                this.emit("stateChange", {
                    newState: "started",
                    id: deserialized.id,
                    password: deserialized.password
                });
            }

            if (deserialized.type == "joined") {
                if (!deserialized.host) {

                }

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
                this.signalingSocket?.destroy();
                this.signalingSocket = undefined;

                this.emit("stateChange", {
                    newState: "left",
                    me: true
                });
            }

            if (deserialized.type == "ended") {
                this.signalingSocket?.destroy();
                this.signalingSocket = undefined;

                this.emit("stateChange", {
                    newState: "ended"
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
                this.emit("stateChange", {
                    newState: "ended"
                });
            }
        }

        else if (deserialized.response == "error") {
            this.emit("error", deserialized?.reason);
        }
    }


      /////////////////////////////////////////
     ///        CLIENT-SIDE METHODS        ///
    /////////////////////////////////////////

    /**
     * Starts a new meeting, and automatically joins it.
     * Upon improper usage, exceptions will be thrown.
     * 
     * @returns Meeting ID and password, seperated by a semicolon.
     */
    public start(): string {
        if (this.signalingSocket != null) {
            throw new Error(); // Maybe custom error?
        }

        this.signalingSocket = new Socket();
        this.signalingSocket.connect(5060, "127.0.0.1");
        this.signalingSocket.on("data", (data) => handleSignalingMessage(data.toString()));
        this.signalingSocket.write(JSON.stringify({request: "start"}));

        return "The function has returned. At last!"; // TODO: UNUTILIZED!
    }

    /**
     * This method will attempt to join a meeting.
     * 
     * Upon any errors (such as invalid ID, wrong password, full meeting etc..), exceptions will be thrown.
     * 
     * @param id The meeting ID
     * @param password The meeting password
     * @returns true - you're waiting for someone else, and therefore is the host. false for otherwise.
     */
    public join(id: string, password: string): boolean {
        return false; // TODO: UNUTILIZED!
    }

    /**
     * This method will attempt to switch the meeting's host, thereby granting the other user ending rights.
     * Upon improper usage, exceptions will be thrown.
     */
    public switch(): void {
        return; // TODO: UNUTILIZED!
    }

    /**
     * This method will leave a meeting.
     * Upon improper usage, exceptions will be thrown.
     */
    public leave(): void {
        return; // TODO: UNUTILIZED!
    }

    /**
     * This method will attempt to end the meeting.
     * Upon improper usage, exceptions will be thrown.
     */
    public end(): void {
        return; // TODO: UNUTILIZED!
    }

    /**
     * This method will send a message to the user's peer.
     * It will only work after being unlocked  by a join method.
     * 
     * Upon improper usage, exceptions will be thrown.
     */
    public send(): void {
        return; // TODO: UNUTILIZED!
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

type SignalingResponseStatus = "success" | "info" | "error";
type SignalingResponseType = "created" | "joined" | "switched" | "left" | "ended";

type NetworkingState = "connecting" | "connected"; // hmmmm

// Perhaps make a better function system?

function handleSignalingMessage(data: string) {
    Networking.getInstance().handleSignalingMessage(data);
}