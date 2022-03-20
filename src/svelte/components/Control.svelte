<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import { meeting } from "../meetingStore";

    import type { Networking } from "../../electron/backend";
    import type Media from "../media";

    export let userMedia: Media;

    const net: Networking = (window as any).networking;
    const dispatch = createEventDispatcher();

    let webcamOn = false;
    let micOn = false;

    let host = false;
    let statusMessage = "Waiting for peer...";

    meeting.subscribe(info => {
        if (info?.host) host = info.host;
        
        if (info?.connected) {
            statusMessage = "Connecting...";
        }

        else if (info?.disconnected) {
            statusMessage = "Waiting for peer...";
        }

        else if (info?.ready) {
            statusMessage = "Connected";
        }
    });

    function toggleWebcam() {
		webcamOn = webcamOn ? false : true;

		if (webcamOn) {
			// 360p video
			userMedia.enableVideo(640, 360).then(() => {
				dispatch("cam", true);
			});
		} else {
            dispatch("cam", false);
			userMedia.disableVideo();
		}
	}

	function toggleMicrophone() {
		micOn = micOn ? false : true;

		if (micOn) {
			userMedia.enableAudio(true).then(() => {
				dispatch("mic", true);
			});
		} else {
            dispatch("mic", false);
			userMedia.disableAudio();
		}
	}

    function leaveMeeting() {
        net.leave();
    }

    function endMeeting() {
        net.end();
    }
</script>

<div id="container">
    <div class="item">
        <h2>{statusMessage}</h2>
    </div>

    <div id="main-control" class="item">
        <button class="{webcamOn ? "on" : "off"}" on:click={toggleWebcam}>
            <img src="assets/cam_{webcamOn ? "on" : "off"}.png" alt="Camera Icon" width = "76" />
        </button>
        <button class="{micOn ? "on" : "off"}" on:click={toggleMicrophone}>
            <img src="assets/mic_{micOn ? "on" : "off"}.png" alt="Microphone Icon" width = "76" />
        </button>
    </div>

    <div class="item">
        <button class="leave-control" on:click={leaveMeeting}>
            Leave Meeting
        </button>

        {#if host}
            <button class="leave-control" on:click={endMeeting}>
                End Meeting
            </button>
        {/if}
    </div>
</div>

<style>
    #container {
        display: flex;
        flex-direction: row;
    }

    #main-control {
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 10px;
    }

    .item {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
        user-select: none;
    }

    .item:first-child > h2 {
        color: white;
        margin-right: auto;
    }

    .item:last-child > button {
        margin-left: auto;
        margin-bottom: 0;
    }
	
	/*call control related styles*/

	#main-control button {
		height: 70px;
		width: 70px;
		border-radius: 50%;
		cursor: pointer;
		transition: background-color ease 0.5s;
	}

    #main-control button img {
		position: relative;
		right: 10.5px;
		top: -10px;
    }

	#main-control button.on {
		background-color:rgb(77, 77, 77);
	}

	#main-control button.on:hover {
		background-color: rgb(59, 58, 58);
	}

	#main-control button.off {
		background-color: rgb(234, 67, 53);
	}
	
	#main-control button.off:hover {
		background-color: rgb(224,80,67);
	}

    .leave-control {
        color: white;
        font-weight: bold;
        font-size: 20px;

        background-color: rgb(234, 67, 53);
        transition: background-color ease 0.5s;

        border-radius: 20px;
        height: 50px;
        width: 160px;
        padding: 3px;

        cursor: pointer;
    }

    .leave-control:hover {
        background-color: rgb(231, 95, 82);
    }
</style>