import App from './App.svelte';
import { handleSignalingMessage, handleICEMessage } from './backend';
import { Socket } from 'net';

const signalingSocket = new Socket();
const iceSocket = new Socket();

signalingSocket.on("data", (data) => handleSignalingMessage(signalingSocket, data.toString()));
iceSocket.on("data", (data) => handleICEMessage(iceSocket, data.toString()));

const app = new App({
	target: document.body,
	props: {
		signalingSocket: signalingSocket,
		iceSocket: iceSocket
	}
});

export default app;