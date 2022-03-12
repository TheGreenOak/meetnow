<script lang="ts">
	import type { Networking, SignalingState } from "../electron/backend";
	import Media from "./media";

	// We cast window as any to avoid getting a TypeScript error.
	// This is usually dangerous, however, we know window does have the networking attribute from Electron's preload.
	const net: Networking = (window as any).networking;
	const userMedia: Media = new Media();
	
	let webcamOn: boolean = false;
	let micOn: boolean = false;
	
	let cam: HTMLVideoElement;
	let mic: HTMLAudioElement;
	
	function toggleWebcam() {
		webcamOn = webcamOn ? false : true;

		if (webcamOn) {
			// 480p video
			userMedia.enableVideo(848, 480).then(() => {
				cam.srcObject = userMedia.getVideoStream();
				cam.play();
			});
		} else {
			userMedia.disableVideo();
		}
	}

	function toggleMicrophone() {
		micOn = micOn ? false : true;

		if (micOn) {
			userMedia.enableAudio(true).then(() => {
				mic.srcObject = userMedia.getAudioStream();
				mic.play();
			});
		} else {
			userMedia.disableAudio();
		}
	}

	/*
	For meeting buttons n' stuff
	*/

	let id: string | undefined;
	let password: string | undefined;
	let hide: string = "";
	let ready: string = "ready";
	let peerMsg: string;

	net.on("state-change", (state: SignalingState) => {
		if (state.newState == "created") {
			id = state.id;
			password = state.password;

			net.join(state.id, state.password);
		}

		else if (state.newState == "connected" && state.me) {
			console.log("Connected!");
			console.log("ID: " + id);
			console.log("Password: " + password);
			hide = "hide";
		}

		else if (state.newState == "connected" && !state.me) {
			console.log("A peer has connected!");
		}

		else if (state.newState == "disconnected" && state.me) {
			hide = "";
			ready = "";
		}

		else if (state.newState == "disconnected" && !state.me) {
			ready = "";
			console.log("Peer disconnected!");
		}
	});

	net.on("ready", () => {
		ready = "ready";
	});

	net.on("comm-error", (err) => {
		console.error("Unable to connect with peer B!");
		console.error("ERR: " + err);
	});

	net.on("error", (err) => {
		console.error(err);
	});

	net.on("message", (content) => {
		console.log("PEER: " + content);
	});

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

	function sendFrame() {
		if (webcamOn) {
			userMedia.getVideoFrame().then(async (frame) => {
				// how do i send it plz

				/*
				let j = 0;
				for (let i = 0; i < frame.length; i += 10000) {
					if (i + 10000 >= frame.length) {
						net.send(frame.substring(i));
					} else {
						net.send(frame.substring(i, i + 10000));
					}

					await new Promise(r => setTimeout(r, 100));
					j++;
				}

				console.log("ENDED!");
				console.log("Num of transitions: " + (j + 1));
				net.send("END");
				*/
			})

			.catch(err => console.error(err));
		}
	}

	let myCanvas: HTMLCanvasElement = null;
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

	{#if ready}
		<button on:click={sendFrame}>Send frame</button>
	{/if}
	
	<canvas bind:this={myCanvas}></canvas>

	<!-- svelte-ignore a11y-media-has-caption -->
	<video bind:this={cam} width="848" height="480" />
	<audio bind:this={mic}/>

	<button class="btn {webcamOn ? "webcam-on" : "webcam-off"}" on:click={toggleWebcam}>
		<img src="assets/cam_{webcamOn ? "on" : "off"}.png" alt="cam"
		width = "76"
		class = "centerbutton">
	</button>
	
	<button class="btn {micOn ? "microphone-on" : "microphone-off"}" on:click={toggleMicrophone}>
		<img src="assets/mic_{micOn ? "on" : "off"}.png" alt="mic"
		width = "76"
		class = "centerbutton">
	</button>
</main>

<style>
	button.pre-meeting {
		background-color: aqua;
		font-size: 16px;
	}

	.hide {
		display: none;
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

	.centerbutton{
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