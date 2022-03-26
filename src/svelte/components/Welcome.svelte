<script lang="ts">
    import type { Networking } from "../../electron/backend";
    import { meeting } from "../stores";

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
    <button id="start-btn" class="btn" on:click={startMeeting}><span>Start Meeting</span></button>
    
    <form id="meeting-form" on:submit|preventDefault={joinMeeting}>
        <input type="text"     class="details form-length" name="meeting-id"       placeholder="ID"       bind:value={id} />
        <input type="password" class="details form-length" name="meeting-password" placeholder="Password" bind:value={password} />
		<input type="submit"  id="join-btn" class="btn form-length" value="Join">
	</form>
</div>

<style>
    #container {
        display: flex;
        flex-direction: column;
		align-items: center;
		align-self: center;
        margin-top: 24vh;
		width: 40vw;
    }
	
    #start-btn {
		user-select: none;
		width: 40vw;
    }

	#start-btn:active {
		transform: scale(0.9);
	}

	.form-length {
		width: 13vw;
	}

	#join-btn:active {
		transform: scale(0.9);
	}

    #meeting-form {
		display: flex;
		flex-direction: row;
		gap: 0.5vw;
		justify-content: center;
		white-space: nowrap;
    }

    #meeting-form .details {
		background-color: transparent;
		color: white;
		outline-color: transparent;
		border-color: #52595D;
		user-select: none;
	}

	#meeting-form .details:hover {
		border-color: #afa390;;
	}

    .btn {
		background-color: #125AB8;
		color: white;
		border: none;
		transition: all 0.5s;
		cursor: pointer;
	}

	.btn span {
		cursor: pointer;
		display: inline-block;
		position: relative;
		transition: 0.5s;
	}

	.btn span:after {
		content: '\00bb';
		position: absolute;
		opacity: 0;
		top: 0;
		right: -20px;
		transition: 0.5s;
	}

	.btn:hover span {
		padding-right: 25px;
	}

	.btn:hover span:after {
		opacity: 1;
		right: 0;
	}
</style>