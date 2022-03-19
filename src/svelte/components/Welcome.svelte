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

<div id="container">
    <button id="start-btn" class="btn" on:click={startMeeting}>Start Meeting</button>
    
    <form id="meeting-form" on:submit|preventDefault={joinMeeting}>
        <input type="text"     class="details" name="meeting-id"       placeholder="ID"       bind:value={id} />
        <input type="password" class="details" name="meeting-password" placeholder="Password" bind:value={password} />

        <input type="submit" id="join-btn" class="btn" value="Join" />
    </form>
</div>

<style>
    #container {
        display: flex;
        flex-direction: column;
        align-items: center;

        margin-top: 24vh;
    }

    #start-btn {
        width: 40vw;
    }

    #container button {
        user-select: none;
    }

    #meeting-form {
        display: flex;
        flex-direction: row;
    }

    #meeting-form .details {
		background-color: transparent;
		color: white;
		outline-color: transparent;
		border-color: #52595D;
	}

	#meeting-form .details:hover {
		border-color: #afa390;;
	}

    .btn {
		background-color: #125AB8;
		color: white;
		border: none;
		cursor: pointer;
	}

	.btn:hover {
		background-color: #1350A0;
	}
</style>