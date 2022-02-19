import { contextBridge } from "electron";
import { Networking } from "./backend";

const net = Networking.getInstance();

/*
What's going on here?

To allow for seamless communication inside of the renderer process,
we expose basic networking methods that assist the renderer process in handling basic networking.

We only expose abstractions that help the renderer do connections. We never expose raw sockets,
since they're useless either way, considering the Renderer process can't make use of them.
*/
contextBridge.exposeInMainWorld("networking", {
    start: net.start,
    join: net.join,
    leave: net.leave,
    getIP: net.getIP,
    negotiateConnection: net.negotiateConnection,
    send: net.send
});