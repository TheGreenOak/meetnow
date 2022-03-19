<script lang="ts">
	import type { Writable } from "svelte/store";

	import Info from "./Info.svelte";
	import Time from "./Time.svelte";

	export let meeting: Writable<MeetingInfo>;

    function reload(){
        location.reload();
    }

	type MeetingInfo = {
        id?: string;
        password?: string;
        temporary: boolean;
    };
</script>

<header>
	<div id="logo" title="MeetNow">
		<button on:click={reload}>
			<img src="assets/aperture.png" alt="logo" width = "20px">
			<h1>MeetNow</h1>
		</button>
	</div>

	<Time />
	<Info {meeting} />
</header>

<style>
	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-direction: row;
		margin-bottom: 20px;
		padding: 0 20px;
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