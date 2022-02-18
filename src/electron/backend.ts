import type { Socket } from "net";

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