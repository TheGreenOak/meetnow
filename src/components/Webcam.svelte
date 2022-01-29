<script lang="ts">
    export let height: number = 848;
    export let width: number = 480;

    let videoSource = null;
    const videoStream = navigator.mediaDevices.getUserMedia({
        video: {
            width: { ideal: width },
            height: { ideal: height }
        }
    });

    videoStream.then((stream) => {
        videoSource.srcObject = stream;
        videoSource.play();
    }).catch((err) => console.error(err));
</script>

<!-- svelte-ignore a11y-media-has-caption -->
<video bind:this={videoSource} />