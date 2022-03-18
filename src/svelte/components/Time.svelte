<script lang="ts">
    import { onMount } from "svelte";

    let time = new Date();

    $: hour = time.getHours().toString().padStart(2, '0');
    $: minute = time.getMinutes().toString().padStart(2, '0');

    onMount(() => {
        const interval = setInterval(() => {
            time = new Date();
        }, 1000);

        // Called upon destroyal of the object
        return () => { 
            clearInterval(interval);
        }
    });
</script>

<h1>{hour}:{minute}</h1>

<style>
    h1 {
        color: white;
    }
</style>