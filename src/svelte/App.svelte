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

	<button class={webcamOn ? "webcam-on" : "webcam-off"} on:click={toggleWebcam}>
		<img src="assets/cam_{webcamOn ? "on" : "off"}.png" alt="cam"
		width = "76"
		class = "centerbutton">
	</button>

	{#if micOn}
		<Microphone bind:this={mic}/>
	{:else}
		<h1>Microphone turned off</h1>
	{/if}
	
	<button class={micOn ? "microphone-on" : "microphone-off"} on:click={toggleMicrophone}>
		<img src="assets/mic_{micOn ? "on" : "off"}.png" alt="mic"
		width = "76"
		class = "centerbutton">
	</button>

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
	:global(body) {
		background-color: rgb(26 28 29);;
	}
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

	.centerbutton{
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
	}

	button {
		color: rgb(77, 77, 77);
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
		background-color:rgb(77, 77, 77);
	}

	button.webcam-off {
		background-color: rgb(234, 67, 53);
		
	}
	
	button.webcam-off:hover{
		background-color: rgb(224,80,67);
	}

	button.webcam-on:hover {
		background-color: rgb(59, 58, 58);
	}

	button.microphone-on {
		color: rgb(19, 19, 19);
		background-color:rgb(77, 77, 77);
		left: 100px;
	}

	button.microphone-off {
		background-color: rgb(234, 67, 53);
		left: 100px;
	}

	button.microphone-off:hover{
		background-color: rgb(224,80,67);
	}

	button.microphone-on:hover {
		background-color: rgb(59, 58, 58);
	}
</style>