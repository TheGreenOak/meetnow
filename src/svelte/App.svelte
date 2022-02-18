<script lang="ts">
	import Webcam from "./components/Webcam.svelte";
	let webcamOn: boolean = false;

	function toggleWebcam() {
		webcamOn = webcamOn ? false : true;
	}
</script>

<main>
	{#if webcamOn}
		<Webcam height={720} width={1280} />
	{:else}
		<h1>Webcam turned off</h1>
	{/if}

	<button class={webcamOn ? "webcam-on" : ""} on:click={toggleWebcam}>[{webcamOn ? "ON" : "OFF"}]</button>
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
</style>