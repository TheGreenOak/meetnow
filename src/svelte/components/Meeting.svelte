<script lang="ts">
	import { onDestroy } from "svelte";
	import type { Networking } from "../../electron/backend";

	import Media from "../media";
	import Control from "./Control.svelte";

	const net: Networking = (window as any).networking;
	const userMedia: Media = new Media();
	
	let cam: HTMLVideoElement;
	let mic: HTMLAudioElement;

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
		}
	}

	function micHandler(event: CustomEvent<boolean>) {
		if (event.detail == true) {
			mic.srcObject = userMedia.getAudioStream();
		}
	}

	onDestroy(() => {
		userMedia.disableVideo();
		userMedia.disableAudio();
		userMedia.disableScreenshare();
	});

	let peerVideo: HTMLCanvasElement;
</script>

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
</style>