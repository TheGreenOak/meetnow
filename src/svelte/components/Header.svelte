<script lang="ts">
	import { meeting } from "../meetingStore";

	import Info from "./Info.svelte";
	import Time from "./Time.svelte";

    function reload(){
        location.reload();
    }
</script>

<header>
	<div id="logo" title="MeetNow">
		<button on:click={reload}>
			<img src="assets/aperture.png" alt="logo" width = "20px">
			<h1>MeetNow</h1>
		</button>
	</div>

	<Time />
	<Info />
</header>

<style>
	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-direction: row;
	}

	#logo {
		user-select: none;
	}

    #logo button {
		background-color: transparent;
		border: none;
		cursor: pointer;
        top: 20px;
	}
	
	#logo img {
		filter: invert(1);
		margin-right: 6px;
	}

	#logo h1 {
		color: white;
		font-size: 27px;
		display: inline;
	}
</style>