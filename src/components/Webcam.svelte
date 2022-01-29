<script lang="ts">
    let videoSource = null;
    const videoStream = navigator.mediaDevices.getUserMedia({
        video: true
    });

    videoStream.then((stream) => {
        videoSource.srcObject = stream;
        videoSource.play();
    }).catch((err) => console.error(err));
</script>

<!-- svelte-ignore a11y-media-has-caption -->
<video bind:this={videoSource} />