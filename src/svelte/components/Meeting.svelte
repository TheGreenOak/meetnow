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
				for (let i = 0; i < frame.length; i += 512) {
					if (i + 512 >= frame.length) {
						net.send("V" + toShortBytes(j) + frame.substring(i));
					} else {
						net.send("V" + toShortBytes(j) + frame.substring(i, i + 512));
					}

					await new Promise(r => setTimeout(r, 1));
					j++;
				}

				console.log("ENDED!");
				console.log("Num of transitions: " + (j + 1));
				net.send("VEND");
			})

			.catch(err => console.error(err));
		}
	}

	function toShortBytes(value: number): string {
		let highBytes = (value & 65280) >> 4; // 65280 == one byte ON,  one byte OFF
		let lowBytes = (value & 255);	      // 255   == one byte OFF, one byte ON

		return String.fromCharCode(highBytes) + String.fromCharCode(lowBytes);
	}

	function shortToNumber(value: string): number {
		let finalValue: number;

		finalValue = value.charCodeAt(0) << 4;
		finalValue += value.charCodeAt(1);

		return finalValue;
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
				let index = shortToNumber(data);
				data = data.substring(2);

				while (videoBufferIndex < index) {
					for (let i = 0; i < 512; i++) {
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

	let peerVideo: HTMLCanvasElement;
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
		display: flex;
		position: relative;
		bottom: 0;
	}

	video {
		position: fixed;
		bottom: 0;
		right: 0;
		background-color: transparent;
		width: 17vw;
		height: 45vh;
	}

	canvas {
		position: fixed;
    	top: 50%;
    	left: 45%;
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