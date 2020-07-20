<div class="embed-responsive embed-responsive-16by9">
    <video controls>
        <source class="embed-responsive-item" src="{video.contentUrl}" type="{video.mimeType}">
    </video>
</div>
<h2 class="row">{video.title}</h2>

<script context="module">
    export async function preload(page, session) {
        const {id} = page.params;

        const query = {
            "query": "query getVideoById($videoId: ID){video: getVideoById(id: $videoId){id title contentUrl mimeType}}",
            "variables": {"videoId": id}
        }
        const res = await this.fetch(process.env.API_ENDPOINT + '/graphql', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify(query)
        })
        const data = await res.json();

        if (data.data.video === null) {
            this.error(404, 'Video not found ¯\\_(ツ)_/¯')
        }

        return {video: data.data.video};
    }
</script>

<script>
    export let video;
</script>