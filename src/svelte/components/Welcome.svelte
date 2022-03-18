<script lang="ts">
    import type { Writable } from "svelte/store";
    import type { Networking } from "../../electron/backend";

    export let meeting: Writable<{}>;
    const net: Networking = (window as any).networking;

    let id: string | undefined;
    let password: string | undefined;

    function startMeeting() {
		net.start();
	}

	function joinMeeting() {
        meeting.set({
            id: id,
            password: password,
            temporary: true
        });
        
		net.join(id, password);
	}
</script>

<button id="start-btn" on:click={startMeeting}>Start Meeting</button>

<form id="meeting-form" class="pre-meeting" on:submit|preventDefault={joinMeeting}>
    <input type="text" id="meeting-id" name="meeting-id" placeholder="ID" bind:value={id} />
    <input type="password" id="meeting-password" name="meeting-password" placeholder="Password" bind:value={password} />
</form>

<button id="join-btn" type="submit" value="Join" on:click={joinMeeting}>Join Meeting</button>

<style>
    #start-btn {
        width:25%;
        margin-left:37.5%;
        margin-right:37.5%;
	}

    #join-btn {
        width:25%;
        margin-left:37.5%;
        margin-right:37.5%;
    }

    #meeting-form {
        width:25%;
        margin-left:37.5%;
        margin-right:37.5%;
    }
</style>