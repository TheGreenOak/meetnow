<script lang="ts">
	import type { Networking, SignalingState } from "../electron/backend";
	import Webcam from "./components/Webcam.svelte";
	import Microphone from "./components/Microphone.svelte";

	// We cast window as any to avoid getting a TypeScript error.
	// This is usually dangerous, however, we know window does have the networking attribute from Electron's preload.
	const net: Networking = (window as any).networking;
	
	let webcamOn: boolean = false;
	let micOn: boolean = false;
	
	let cam: Webcam = null;
	let mic: Microphone = null;
	
	let error: boolean = false;
	let errContent: string = "";
	
	let message: boolean = false;
	let msgContent: string = "";

	let success: boolean = false;
	let successContent: string = "";
	
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

	/*
	For meeting buttons n' stuff
	*/

	let id: string | undefined;
	let password: string | undefined;
	let hide: string = "";
	let ready: string = "";
	let peerMsg: string;

	net.on("state-change", (state: SignalingState) => {
		if (state.newState == "created") {
			id = state.id;
			password = state.password;

			net.join(state.id, state.password);
		}

		else if (state.newState == "connected" && state.me) {
			showMessage("Connected!");
			console.log("ID: " + id);
			console.log("Password: " + password);
			hide = "hide";
		}

		else if (state.newState == "connected" && !state.me) {
			showMessage("A peer has connected!");
		}

		else if (state.newState == "disconnected" && state.me) {
			hide = "";
			ready = "";
		}

		else if (state.newState == "disconnected" && !state.me) {
			ready = "";
			showMessage("Peer disconnected!");
		}
	});

	net.on("ready", () => {
		ready = "ready";
	});

	net.on("error", (err) => {
		showError(err);
	});

	net.on("message", (content) => {
		showSuccess(content);
		console.log("PEER: " + content);
	});

	function showError(err: string) {
		error = true;
		errContent = err;

		setTimeout(() => {
			error = false;
		}, 1000);
	}

	function showMessage(msg: string) {
		message = true;
		msgContent = msg;

		setTimeout(() => {
			message = false;
		}, 1500);
	}

	function showSuccess(msg: string) {
		success = true;
		successContent = msg;

		setTimeout(() => {
			success = false;
		}, 1500);
	}

	function startMeeting() {
		net.start();
	}

	function joinMeeting(e: Event) {
		e.preventDefault();
		net.join(id, password);
	}

	function leaveMeeting() {
		net.leave();
	}

	function sendMessage(e: Event) {
		e.preventDefault();
		net.send(peerMsg);
		peerMsg = "";
	}
</script>

<main>
	<!-- Starting Buttons -->
	<button id="start-btn" class="pre-meeting {hide}" on:click={startMeeting}>Start Meeting</button>
	<form id="meeting-form" class="pre-meeting {hide}" on:submit={joinMeeting}>
		<input type="text" id="meeting-id" name="meeting-id" placeholder="ID" bind:value={id} />
		<input type="password" id="meeting-password" name="meeting-password" placeholder="Password" bind:value={password} />
		<input type="submit" value="Join" />
	</form>

	<button id="leave-btn" class="pre-meeting {hide ? "" : "hide"}" on:click={leaveMeeting}>Leave Meeting</button>
	<form id="send-msg" class={ready} on:submit={sendMessage}>
		<input type="text" placeholder="Enter your message..." bind:value={peerMsg} />
		<input type="submit" value="Send" />
	</form>
	
	{#if webcamOn}
		<Webcam bind:this={cam} height={720} width={1280}/>
	{:else}
		<h1>Webcam turned off</h1>
	{/if}


	{#if micOn}
		<Microphone bind:this={mic}/>
	{:else}
		<h1>Microphone turned off</h1>
	{/if}
	<div class="horizontal-center">
		<button class="{webcamOn ? "webcam-on" : "webcam-off"} btn" on:click={toggleWebcam}>
			<img src="assets/cam_{webcamOn ? "on" : "off"}.png" alt="cam"
			width = "76"
			class = "centerbuttonimg">
		</button>
		<button class="{micOn ? "microphone-on" : "microphone-off"} btn" on:click={toggleMicrophone}>
			<img src="assets/mic_{micOn ? "on" : "off"}.png" alt="mic"
			width = "76"
			class = "centerbuttonimg">
		</button>
	</div>


	{#if message}
		<div class="message">{msgContent}</div>
	{/if}

	{#if error}
		<div class="message error">{errContent}</div>
	{/if}

	{#if success}
		<div class="message success">{successContent}</div>
	{/if}
</main>

<style>
	button.pre-meeting {
		background-color: aqua;
		font-size: 16px;
	}

	.hide {
		display: none;
	}

	#send-msg {
		display: none;
	}

	#send-msg.ready {
		display: block;
	}

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

	.horizontal-center {
	position: absolute;
	top: 98%;
	left: 43.5%;
	transform: translate(-50%, -50%);
	}

	.centerbuttonimg{
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
	}

	.btn {
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

	.btn:hover {
		background-color: rgb(126, 126, 126);
	}

	.btn.webcam-on {
		background-color:rgb(77, 77, 77);
	}

	.btn.webcam-off {
		background-color: rgb(234, 67, 53);
		
	}
	
	.btn.webcam-off:hover{
		background-color: rgb(224,80,67);
	}

	.btn.webcam-on:hover {
		background-color: rgb(59, 58, 58);
	}

	.btn.microphone-on {
		color: rgb(19, 19, 19);
		background-color:rgb(77, 77, 77);
		left: 100px;
	}

	.btn.microphone-off {
		background-color: rgb(234, 67, 53);
		left: 100px;
	}

	.btn.microphone-off:hover{
		background-color: rgb(224,80,67);
	}

	.btn.microphone-on:hover {
		background-color: rgb(59, 58, 58);
	}
</style>