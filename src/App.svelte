<script lang="ts">
	import Webcam from "./components/Webcam.svelte";

	let webcamOn: boolean = false;

	function toggleWebcam() {
		webcamOn = webcamOn ? false : true;
	}
</script>

<main>
	{#if webcamOn}
		<Webcam />
	{:else}
		<h1>Webcam turned off</h1>
	{/if}

	<button on:click={toggleWebcam}>Toggle Webcam</button>
</main>