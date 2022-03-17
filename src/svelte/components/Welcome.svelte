<script lang="ts">

    import type { Networking, SignalingState } from "../../electron/backend";

    const net: Networking = (window as any).networking;

    let id: string | undefined;
	let password: string | undefined;
	let hide: string = "";
	let ready: string = "ready";

    net.on("state-change", (state: SignalingState) => {
		if (state.newState == "created") {
			id = state.id;
			password = state.password;

			net.join(state.id, state.password);
		}

		else if (state.newState == "connected" && state.me) {
			console.log("Connected!");
			console.log("ID: " + id);
			console.log("Password: " + password);
			hide = "hide";
		}

		else if (state.newState == "connected" && !state.me) {
			console.log("A peer has connected!");
		}
    });

    net.on("ready", () => {
		ready = "ready";
	});

	net.on("comm-error", (err) => {
		console.error("Unable to connect with peer B!");
		console.error("ERR: " + err);
	});

	net.on("error", (err) => {
		console.error(err);
	});

	net.on("message", (content) => {
		console.log("PEER: " + content);
	});

    function startMeeting() {
		net.start();
	}

	function joinMeeting(e: Event) {
		e.preventDefault();
		net.join(id, password);
	}


</script>

<button id="start-btn" class="{hide}" on:click={startMeeting}>Start Meeting</button>

<form id="meeting-form" class="pre-meeting {hide}" on:submit={joinMeeting}>
    <input type="text" id="meeting-id" name="meeting-id" placeholder="ID" bind:value={id} />
    <input type="password" id="meeting-password" name="meeting-password" placeholder="Password" bind:value={password} />
</form>

<button id="join-btn" class="{hide}" type="submit" value="Join" on:click={joinMeeting}>Join Meeting</button>




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

	button.pre-meeting {
		background-color: aqua;
		font-size: 16px;
        width:50%;
        margin-left:25%;
        margin-right:25%;
	}

    .hide {
		display: none;
	}

</style>