<script lang="ts">
    export let audioSource: HTMLAudioElement = null;
    const audioStream = navigator.mediaDevices.getUserMedia({audio: true});

    let aStream: MediaStream = null;

    audioStream.then((stream) => {
        aStream = stream;
        audioSource.srcObject =  aStream;
        audioSource.play();
        
    }).catch((err) => console.error(err));

    export const turnOff = () => aStream.getTracks().forEach(track => track.stop());
</script>

<audio bind:this={audioSource} />