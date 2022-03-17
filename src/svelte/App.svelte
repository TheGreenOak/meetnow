<script lang="ts">
	import Header from "./components/Header.svelte";
	import Welcome from "./components/Welcome.svelte";
	import Meeting from "./components/Meeting.svelte";
	
    let inMeeting: boolean = false;
</script>

<main>
	
	<Header />
    {#if inMeeting}
        <Meeting />
    {:else}
        <Welcome />
    {/if}


</main>

<style>
	
	:global(body) {
		background-color: rgb(26 28 29);;
	}


</style>
