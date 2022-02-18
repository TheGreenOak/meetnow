<script lang="ts">
    export let audioSource: HTMLAudioElement = null;
    const audioStream = navigator.mediaDevices.getUserMedia({audio: true});


    audioStream.then((stream) => {
        aStream = stream;
        audioSource.srcObject =  aStream;
        audioSource.play();
        
    }).catch((err) => console.error(err));

</script>

<audio bind:this={audioSource} />