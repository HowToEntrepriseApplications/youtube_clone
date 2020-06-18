<svelte:head>
	<title>Youtube clone</title>
</svelte:head>

{#each videos as video}
	<div><h3>{video['name']}</h3></div>
{/each}

<script context="module">
	const videos = [{'name': '1'}, {'name': 2}]
</script>
