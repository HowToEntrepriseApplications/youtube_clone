<svelte:head>
	<title>Boring art</title>
</svelte:head>

{#each videos as video (video.id)}
	<div class="card h-100">
        <div class="row no-gutters">
            <div class="col-md-4">
                <img src="{video.previewUrl}" alt="video preview" class="card-img">
            </div>
            <div class="col-md-8">
              <div class="card-body">
                <a href="/video/{video.id}" class="card-title">{video.title}</a>
              </div>
            </div>
        </div>
    </div>
{/each}

<script context="module">
    export async function preload(page, session) {
        const query = {"query": "query videos {videos{id title previewUrl}}", "variables": null}
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
