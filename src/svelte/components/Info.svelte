<script lang="ts">
    import type { Writable } from "svelte/store";

    export let meeting: Writable<MeetingInfo>;

    let id: string | undefined;
    let password: string | undefined;
    let inMeeting: boolean = false;

    $: {
        if (id && password) {
            inMeeting = true;
        } else {
            inMeeting = false;
        }
    }

    meeting.subscribe(info => {
        if (info?.temporary == false) {
            id = info?.id;
            password = info?.password;
        }
    });

    type MeetingInfo = {
        id?: string;
        password?: string;
        temporary: boolean;
    };

    function copyDetails() {
        navigator.clipboard.writeText("Join my meeting!\nmeetnow.yeho.dev/" + id + "|" + password);
    }
</script>

{#if inMeeting}
    <div on:click={copyDetails} title="Click to copy!">
        <h3>ID: {id}</h3>
        <h3>Pass: {password}</h3>
        
        <!--TODO: use ●●●●●●●● for password-->
    </div>
{:else}
    <h2>Not in a meeting</h2>
{/if}

<style>
    div {
        display: flex;
        flex-direction: column;
        cursor: pointer;
        text-align: right;
    }

    h2 {
        color: white;
    }

    h3 {
        color: white;
        margin: 0;
    }
</style>