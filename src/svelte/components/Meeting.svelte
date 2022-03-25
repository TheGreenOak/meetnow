<script lang="ts">
	import { onDestroy } from "svelte";
	import type { Networking } from "../../electron/backend";

	import Media from "../media";
	import Control from "./Control.svelte";

	const net: Networking = (window as any).networking;
	const userMedia: Media = new Media();
	
	let webcamOn: boolean = false;
	let micOn: boolean = false;
	
	let cam: HTMLVideoElement;
	let mic: HTMLAudioElement;

	let ready: string = "ready";

	function sendFrame() {
		if (webcamOn) {
			userMedia.getVideoFrame().then(async (frame) => {
				// how do i send it plz

				let j = 0;
				for (let i = 0; i < frame.length; i += 10000) {
					if (i + 10000 >= frame.length) {
						net.send("V" + String.fromCharCode(j) + frame.substring(i));
					} else {
						net.send("V" + String.fromCharCode(j) + frame.substring(i, i + 10000));
					}

					await new Promise(r => setTimeout(r, 100));
					j++;
				}

				console.log("ENDED!");
				console.log("Num of transitions: " + (j + 1));
				net.send("VEND");
			})

			.catch(err => console.error(err));
		}
	}

	let videoBuffer: string;
	let videoBufferIndex: number = 0;

	net.on("message", (data: string) => {
		if (data[0] == "V") {
			data = data.substring(1);

			if (data == "END") {
				userMedia.stringToBitmap(videoBuffer, 640, 360).then(bitmap => {
					peerVideo.getContext("2d").drawImage(bitmap, 0, 0);
				});

				videoBuffer = "";
				videoBufferIndex = 0;
			}

			else {
				let index = data.charCodeAt(0);
				data = data.substring(1);

				while (videoBufferIndex < index) {
					for (let i = 0; i < 10000; i++) {
						videoBuffer += String.fromCharCode(0); // fill in with black space
					}

					videoBufferIndex++;
				}

				videoBuffer += data;
				videoBufferIndex++;
			}
		}
	});

	function camHandler(event: CustomEvent<boolean>) {
		if (event.detail == true) {
			cam.srcObject = userMedia.getVideoStream();
			cam.play();

			webcamOn = true;
		} else {
			webcamOn = false;
		}
	}

	function micHandler(event: CustomEvent<boolean>) {
		if (event.detail == true) {
			mic.srcObject = userMedia.getAudioStream();
			micOn = true;
		} else {
			micOn = false;
		}
	}

	onDestroy(() => {
		userMedia.disableVideo();
		userMedia.disableAudio();
		userMedia.disableScreenshare();
	});

	let peerVideo: HTMLCanvasElement = null;
</script>

{#if ready}
    <button class="temp" on:click={sendFrame}>Send frame</button>
{/if}

	<div class="video-container">
		<!-- svelte-ignore a11y-media-has-caption -->
		<video bind:this={cam} height="480" width="848"/>
		<canvas bind:this={peerVideo} height="360" width="640" />
	</div>
	<div id="footer">
		<Control {userMedia} on:cam={camHandler} on:mic={micHandler} />
	</div>

<style>
	.video-container {
		position: relative;
		bottom: 0;
	}

	video {
		position: fixed;
    	top: 50%;
    	left: 50%;
		transform: translate(-50%, -50%);
		width: 75vw;
		height: 75vh;
	}

	#footer {
		position: fixed;
		bottom: 0;
    	width: 98.5%
	}

	.temp {
		position: absolute;
	}
</style>