<script lang="ts">
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
			})

			.catch(err => console.error(err));
		}
	}

	function camHandler(event: CustomEvent<boolean>) {
		if (event.detail == true) {
			cam.srcObject = userMedia.getVideoStream();
			cam.play();

			webcamOn = true;
		}
	}

	function micHandler(event: CustomEvent<boolean>) {
		if (event.detail == true) {
			mic.srcObject = userMedia.getAudioStream();
			mic.play();

			micOn = true;
		}
	}

	let myCanvas: HTMLCanvasElement = null;
</script>

{#if ready}
    <button on:click={sendFrame}>Send frame</button>
{/if}

<canvas bind:this={myCanvas}></canvas>

<!-- svelte-ignore a11y-media-has-caption -->
<video bind:this={cam} width="848" height="480" />
<audio bind:this={mic}/>

<Control {userMedia} on:cam={camHandler} on:mic={micHandler} />

<style>
	:global(body) {
		background-color: rgb(26 28 29);;
	}
</style>