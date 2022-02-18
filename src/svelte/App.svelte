<script lang="ts">
	import Webcam from "./components/Webcam.svelte";
	import Microphone from "./components/Microphone.svelte";

	let webcamOn: boolean = false;
	let micOn: boolean = false;

	function toggleWebcam() {
		webcamOn = webcamOn ? false : true;
	function toggleMicrophone() {
		micOn = micOn ? false : true;
	}
</script>

<main>
	{#if webcamOn}
		<Webcam height={720} width={1280} />
	{:else}
		<h1>Webcam turned off</h1>
	{/if}

	<button class={webcamOn ? "webcam-on" : ""} on:click={toggleWebcam}>[{webcamOn ? "(c)ON" : "(c)OFF"}]</button>

	{#if micOn}
		<Microphone/>
	{:else}
		<h1>Microphone turned off</h1>
	{/if}
	
	<button class={micOn ? "microphone-on" : "microphone-off"} on:click={toggleMicrophone}>[{micOn ? "(m)ON" : "(m)OFF"}]</button>
</main>

<style>
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