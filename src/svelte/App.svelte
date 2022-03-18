<script lang="ts">
	import { Writable, writable } from "svelte/store";
	import type { Networking, SignalingState } from "../electron/backend";

	import Header from "./components/Header.svelte";
	import Welcome from "./components/Welcome.svelte";
	import Meeting from "./components/Meeting.svelte";
	
	const net: Networking = (window as any).networking;
	const meeting: Writable<MeetingInfo> = writable();

	let id: string | undefined;
	let password: string | undefined;
	let inMeeting: boolean = false;

	meeting.subscribe(info => {
		id = info?.id;
		password = info?.password;
	});

	// Handle networking
	net.on("state-change", (state: SignalingState) => {
		if (state.newState == "created") {
			id = state.id;
			password = state.password;

			net.join(state.id, state.password);
		}

		else if (state.newState == "connected" && state.me) {
			inMeeting = true;

			meeting.set({
				id: id,
				password: password,
				temporary: false
			});
		}

		else if (state.newState == "ended" || (state.newState == "disconnected" && state.me)) {
			meeting.set({ temporary: false });

			inMeeting = false;
		}
	});

	type MeetingInfo = {
        id?: string;
        password?: string;
        temporary: boolean;
    };
</script>

<main>
	<Header {meeting} />

    {#if inMeeting}
        <Meeting />
    {:else}
        <Welcome {meeting} />
    {/if}
</main>