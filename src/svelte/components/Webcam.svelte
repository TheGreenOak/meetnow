<script lang="ts">
    export let height: number = 848;
    export let width: number = 480;
    
    let videoSource: HTMLVideoElement = null;
    let vStream: MediaStream = null;

    const videoStream = navigator.mediaDevices.getUserMedia({
        video: {
            width: { ideal: width },
            height: { ideal: height }
        }
    });
    videoStream.then((stream) => {
        vStream = stream;
        videoSource.srcObject = vStream;
        videoSource.play();
    }).catch((err) => console.error(err));

    export const turnOff = () => vStream.getTracks().forEach(track => track.stop());
</script>

<!-- svelte-ignore a11y-media-has-caption -->
<video bind:this={videoSource} />