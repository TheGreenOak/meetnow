<script>

    function reload(){
        location.reload();
    }
</script>

<header>
    <h1>
        <button class="logo-button" on:click={reload}>
            <img class="logo-img" src="assets/aperture.png" alt="logo" 
            width = "50">
        </button>
    </h1>
</header>

<style>

    .logo-button {
		background-color: transparent;
		color: transparent;
		border-radius: 50%;
		border: none;
		cursor: pointer;
		width: 60px;
		height: 60px;
        top: 20px;
	}
	
	.logo-button:hover {
		background-color: transparent;
		
	}

	.logo-img {
		-webkit-filter: invert(1);
   		filter: invert(1);
	}

    .message {
		color: white;
		background-color: blue;
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-family: Arial;
		font-weight: bold;
		font-size: 26px;
		border-radius: 10px;
		padding: 10px;
	}

	.message.success {
		background-color: green;
	}

	.message.error {
		background-color: red;
	}



</style>