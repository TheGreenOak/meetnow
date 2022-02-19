import { Socket } from "net";

/**
 * Singleton class for handling all client-side networking.
 */
export class Networking {
    private static instance?: Networking;
    private signalingSocket?: Socket;

    private constructor() {}

    public static getInstance(): Networking {
        if (this.instance == null) {
            this.instance = new Networking();
        }

        return this.instance;
    }

    /**
     * Starts a new meeting.
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
        this.signalingSocket.write("{\"request\": \"start\"}");
        this.signalingSocket.on("data", (data) => { console.log(data.toString()); } ); // no worky :(

        return ""; // TODO: UNUTILIZED!
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
     * This method will leave a meeting.
     * Upon improper usage, exceptions will be thrown.
     */
    public leave(): void {
        return; // TODO: UNUTILIZED!
    }

    /**
     * This method will fetch the user's public IP address via the STUN service.
     * 
     * @returns IP address or null (cannot connect via Peer to Peer).
     */
    public getIP(): string | null {
        return null; // TODO: UNUTILIZED!
    }

    /**
     * This method will negotiate a connection with the other peer, and store the appropriate details.
     * If calling this method worked, it will unlock the send method.
     * 
     * @returns true - a peer to peer connection is being utilized. false for TURN connections.
     * null - negotiation failed.
     */
    public negotiateConnection(): boolean | null {
        return null; // TODO: UNUTILIZED!
    }

    /**
     * This method will send a message to the user's peer.
     * It will only work after being unlocked by the negotiateConnection method.
     * 
     * Upon improper usage, exceptions will be thrown.
     */
    public send(): void {
        return; // TODO: UNUTILIZED!
    }
};

export function handleSignalingMessage(sock: Socket, message: string) {

    // Handle heartbeats
    if (message == "HEARTBEAT") {
        sock.write("HEARTBEAT");
        console.log("Sent a heart beat out to the server!");
    }

    /** TODO: Handle the following messages:
     * - Response: Error [ Show GUI message or something ]
     * - Response: Success [ Continue process / show GUI message / do GUI-related stuff ]
     * - Resposne: Info [ Could be join or something... ]
     */
}

export function handleICEMessage(sock: Socket, message: string) {

    // Handle heartbeats
    if (message == "HEARTBEAT") {
        sock.write("HEARTBEAT");
    }

    /** TODO: Handle the following messages:
     * - Response: Error [ Show GUI message or something ]
     * - Response: Success [ Continue process / show GUI message / do GUI-related stuff ]
     * - Resposne: Info [ Could be join or something... ]
     */
}

export function startMeeting(sock: Socket, message: SignalingMessage, id?: string, password?: string) {
    if (message == "start") {
        sock.write(`{"request": "start"}`);
    }
    
    if (message == "join") {
        sock.write(`{"request": "join", "id": "${id}", "password": "${password}"}`);
    }

    if (message == "switch") {
        sock.write(`{"request": "switch"}`);
    }

    if (message == "leave") {
        sock.write(`{"request": "leave"}`);
    }
    
    if (message == "end") {
        sock.write(`{"request": "end"}`);
    }
}

type SignalingMessage = "start" | "join" | "switch" | "leave" | "end";
type ICEMessage = "connect" | "leave"; 