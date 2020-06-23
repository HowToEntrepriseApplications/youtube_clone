<svelte:head>
	<title>Boring art</title>
</svelte:head>

{#each videos as video (video.id)}
	<div><h3><a href="/video/{video.id}">{video.title}</a></h3></div>
{/each}

<script context="module">
    export async function preload(page, session) {
        const query = {"query": "query videos {videos{id title}}", "variables": null}
        const res = await this.fetch(process.env.API_ENDPOINT + '/graphql', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify(query)
        })
        const data = await res.json();
        return data.data;
    }
</script>

<script>
	export let videos;
</script>
