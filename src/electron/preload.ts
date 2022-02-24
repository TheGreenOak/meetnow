import { contextBridge, ipcRenderer } from "electron";
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
    switch: net.switch,
    leave: net.leave,
    end: net.end,
    send: net.send,
    onMessage: (callback: Function) => net.onMessage(callback),
    onStateChange: (callback: Function) => net.onStateChange(callback),
    onHostChange: (callback: Function) => net.onHostChange(callback),
    onError: (callback: Function) => net.onError(callback)
});