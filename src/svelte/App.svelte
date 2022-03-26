<script lang="ts">
	import type { Networking, SignalingState } from "../electron/backend";
	import { meeting, notifications } from "./stores";

	import Header from "./components/Header.svelte";
	import Welcome from "./components/Welcome.svelte";
	import Meeting from "./components/Meeting.svelte";
	import Notifications from "./components/Notifications.svelte";
	
	const net: Networking = (window as any).networking;

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
				host: state.host,
				connected: !state.host,
				temporary: false
			});

			notifications.set({
				data: "You've joined a meeting",
				type: "success"
			});
		}

		else if (state.newState == "connected" && !state.me) {
			meeting.set({
				connected: true,
				temporary: true
			});

			notifications.set({
				data: "A peer is connecting...",
				type: "info"
			});
		}

		else if (state.newState == "disconnected" && !state.me) {
			meeting.set({
				host: true,
				disconnected: true,
				temporary: true
			});

			notifications.set({
				data: "Your peer left the meeting",
				type: "info"
			});
		}

		else if (state.newState == "ended" || (state.newState == "disconnected" && state.me)) {			
			meeting.set({ temporary: false });
			
			let notificationData: string;
			let notificationType: "success" | "info" | "error" = "success";

			if (state.newState == "disconnected") {
				notificationData = "You've left the meeting";
			}

			else if (state.newState == "ended" && state.me) {
				notificationData = "You've ended the meeting";
			}

			else {
				notificationData = "The meeting you were in has ended";
				notificationType = "info";
			}

			notifications.set({
				data: notificationData,
				type: notificationType
			});

			inMeeting = false;
		}
	});

	net.on("error", err => {
		notifications.set({
			data: err,
			type: "error"
		});
	});

	net.on("ready", () => {
		meeting.set({
			ready: true,
			temporary: true
		});
	});

	net.on("host-change", newState => {
		meeting.set({
			host: newState,
			temporary: true
		});

		notifications.set({
			data: `You're ${newState ? "now" : "no longer"} the host`,
			type: "info"
		});
	});
</script>

<Notifications />
<Header />

{#if inMeeting}
	<Meeting />
{:else}
	<Welcome />
{/if}

<style>
	:global(body) {
		background-color: rgb(26 28 29);;
		display: flex;
		flex-direction: column;
	}
</style>