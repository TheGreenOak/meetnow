<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import { meeting, notifications } from "../stores";

    import type { Networking } from "../../electron/backend";
    import type Media from "../media";

    export let userMedia: Media;

    const net: Networking = (window as any).networking;
    const dispatch = createEventDispatcher();

    let webcamOn = false;
    let micOn = false;

    let host = false;
    let statusMessage = "Waiting for peer...";

    let ready = false;

    meeting.subscribe(info => {
        if (info?.host) host = info.host;
        
        if (info?.connected) {
            statusMessage = "Connecting...";
        }

        else if (info?.disconnected) {
            statusMessage = "Waiting for peer...";
            ready = false;
        }

        else if (info?.ready) {
            statusMessage = "Connected";
            ready = true;
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

    function switchHost() {
        net.switch();
    }

    function leaveMeeting() {
        net.leave();
    }

    function endMeeting() {
        net.end();
    }

    function sendFrame() {
        if (ready) {
            if (webcamOn) {
                notifications.set({
                    type: "info",
                    data: "Sending current frame..."
                });

                userMedia.getVideoFrame().then(async (frame) => {
                    let j = 0;
                    for (let i = 0; i < frame.length; i += 512) {
                        if (i + 512 >= frame.length) {
                            net.send("V" + toShortBytes(j) + frame.substring(i));
                        } else {
                            net.send("V" + toShortBytes(j) + frame.substring(i, i + 512));
                        }
    
                        await new Promise(r => setTimeout(r, 1));
                        j++;
                    }
    
                    console.log("ENDED!");
                    console.log("Num of transitions: " + (j + 1));
                    net.send("VEND");

                    notifications.set({
                        type: "success",
                        data: "Transmission completed!"
                    });
                })
    
                .catch(err => console.error(err));
            } else {
                notifications.set({
                    type: "error",
                    data: "Your webcam isn't on"
                });
            }
        } else {
            notifications.set({
                type: "error",
                data: "You're not connected to anyone yet"
            });
        }
	}

	function toShortBytes(value: number): string {
		let highBytes = (value & 65280) >> 4; // 65280 == one byte ON,  one byte OFF
		let lowBytes = (value & 255);	      // 255   == one byte OFF, one byte ON

		return String.fromCharCode(highBytes) + String.fromCharCode(lowBytes);
	}
</script>

<div id="container">
    <div class="item">
        <h2>{statusMessage}</h2>
    </div>

    <div class="main-control item">
        <button class="{webcamOn ? "on" : "off"}" style="padding:15px 18px;" on:click={toggleWebcam}>
            <img src="assets/cam_{webcamOn ? "on" : "off"}.png" alt="Camera Icon" width="50" />
        </button>
        <button class="{micOn ? "on" : "off"}" style="padding:18px 19.5px;" on:click={toggleMicrophone}>
            <img src="assets/mic_{micOn ? "on" : "off"}.png" alt="Microphone Icon" width="45" />
        </button>
        <button class="send {!ready ? "disabled" : ""}" disabled="{!ready}" style="padding: 18px 21px;" on:click={sendFrame}>
            <img src="assets/upload.png" alt="Send Frame" width="43" />
        </button>
    </div>

    <div class="main-control item">
        {#if host}
            <button class="switch" on:click={switchHost} title="Switch Host">
                <img src="assets/switch.png"  style="padding:8px 8px;" alt="Switch Host" width="56" />
            </button>
        {/if}

        <button class="leave-control" on:click={leaveMeeting} title="Leave Meeting">
            <img src="assets/leave.png"   style="padding:15px 16px;" alt="Leave Meeting" width="45" />
        </button>

        {#if host}
            <button class="leave-control" on:click={endMeeting} title="End Meeting">
                <img src="assets/cross.png"  style="padding:15px 16px;" alt="End Meeting" width="40" />
            </button>
        {/if}
    </div>
</div>

<style>
    #container {
        display: flex;
        flex-direction: row;
    }

    .main-control {
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 10px;
        user-select: none;
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

	.item button {
		height: 70px;
		width: 70px;
        border-color: white;
        border-width: 3px;
		border-radius: 50%;
		cursor: pointer;
		transition: background-color ease 0.5s;
	}

    .item button img {
		position: relative;
		right: 10.5px;
		top: -10px;
    }

	.item button.on {
		background-color:rgb(77, 77, 77);
	}

	.item button.on:hover {
		background-color: rgb(59, 58, 58);
	}

	.item button.off {
		background-color: rgb(234, 67, 53);
	}
	
	.item button.off:hover {
		background-color: rgb(224,80,67);
	}

    .item button.send {
        background-color: #076fc6;
    }

    .item button.send:hover {
        background-color: #248add;
    }

    .item button.send.disabled {
        cursor: not-allowed;
        background-color: rgb(77, 77, 77);
    }

    .leave-control {
        background-color: rgb(234, 67, 53);
    }

    .leave-control:hover {
        background-color: rgb(231, 95, 82);
    }

    .switch {
        background-color: rgb(219, 143, 0);
    }

    .switch:hover {
        background-color: rgb(250, 150, 1);
    }
</style>