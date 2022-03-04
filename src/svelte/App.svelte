<script lang="ts">
	import type { Networking, SignalingState } from "../electron/backend";
	import Webcam from "./components/Webcam.svelte";
	import Microphone from "./components/Microphone.svelte";

	// We cast window as any to avoid getting a TypeScript error.
	// This is usually dangerous, however, we know window does have the networking attribute from Electron's preload.
	const net: Networking = (window as any).networking;
	
	net.on("stateChange", (data: SignalingState) => {
		console.log(data);
		showMessage(data.newState, 3000);
	});

	net.on("hostChange", (data: boolean) => { 
		if (data == true) {
			showHost(true, 2000);
		} else {
			showHost(false, 2000);
		}
	});

	net.on("error", (data: string) => {
		showError(data, 3000);
	});

	net.on("ready", () => {
		console.log("The connection has been successfully created!");
	});

	net.on("comm-error", (err) => {
		console.error(err);
	});

	net.on("message", (data) => {
		console.log("PEER: " + data);
	});
	
	let webcamOn: boolean = false;
	let micOn: boolean = false;

	let cam: Webcam = null;
	let mic: Microphone = null;

	let error: boolean = false;
	let errContent: string = "";

	let host: boolean = false;
	let isHost: boolean = false;

	let message: boolean = false;
	let msgContent: string = "";

	function toggleWebcam() {
		webcamOn = webcamOn ? false : true;
		if(!webcamOn) {
			cam.turnOff()
		}
	}

	function toggleMicrophone() {
		micOn = micOn ? false : true;
		if(!micOn) {
			mic.turnOff();
		}
	}

	function showMessage(content: string, timeout: number) {
		message = true;
		msgContent = content;

		setTimeout(() => {
			message = false;
		}, timeout);
	}

	function showError(content: string, timeout: number) {
		error = true;
		errContent = content;

		setTimeout(() => {
			error = false;
		}, timeout);
	}

	function showHost(state: boolean, timeout: number) {
		host = true;
		isHost = state;

		setTimeout(() => {
			host = false;
		}, timeout);
	}

</script>

<main>
	{#if webcamOn}
		<Webcam bind:this={cam} height={720} width={1280}/>
	{:else}
		<h1>Webcam turned off</h1>
	{/if}

	<button class={webcamOn ? "webcam-on" : ""} on:click={toggleWebcam}>[{webcamOn ? "(c)ON" : "(c)OFF"}]</button>

	{#if micOn}
		<Microphone bind:this={mic}/>
	{:else}
		<h1>Microphone turned off</h1>
	{/if}
	
	<button class={micOn ? "microphone-on" : "microphone-off"} on:click={toggleMicrophone}>[{micOn ? "(m)ON" : "(m)OFF"}]</button>

	{#if message}
		<div class="message">{msgContent}</div>
	{/if}

	{#if error}
		<div class="message error">{errContent}</div>
	{/if}

	{#if host}
		<div class="message success">You're {isHost ? "now" : "no longer"} the host.</div>
	{/if}
</main>

<style>
	.message {
		color: white;
		background-color: blue;
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-family: Arial;
		font-weight: bold;
		font-size: 26px;
		border-radius: 10px;
		padding: 10px;
	}

	.message.success {
		background-color: green;
	}

	.message.error {
		background-color: red;
	}

	button {
		color: white;
		background-color: rgb(77, 77, 77);
		border-radius: 50%;
		height: 70px;
		width: 70px;
		cursor: pointer;
		transition: color ease 0.5s;
		transition: background-color ease 0.5s;
		position: absolute;
		bottom: 1px;
		left: 1px;
	}

	button:hover {
		background-color: rgb(126, 126, 126);
	}

	button.webcam-on {
		color: rgb(19, 19, 19);
		background-color:rgb(219, 219, 219);
	}

	button.webcam-on:hover {
		color: black;
		background-color: rgb(230, 230, 230);
	}

	button.microphone-on {
		color: rgb(19, 19, 19);
		background-color:rgb(219, 219, 219);
		left: 100px;
	}

	button.microphone-off {
		left: 100px;
	}

	button.microphone-on:hover {
		color: black;
		background-color: rgb(230, 230, 230);
	}
</style>