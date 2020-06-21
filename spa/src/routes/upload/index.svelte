<form action="{presigned_url}" method="post" enctype="multipart/form-data">
    {#each Object.entries(form_fields) as [name, value] (name) }
        <input type="hidden" name="{ name }" value="{ value }" />
    {/each}
    <input type="file"   name="file" bind:files/> <br />
    <input type="submit" value="submit" disabled={!video_added}/>
    {video_added}
</form>


<script>
    let video_added = false;
    let presigned_url = undefined;
    let form_fields = {};
    let files;

    $: if (files){
        let file = files[0]
        video_added = true;
        let query = {
            "query": "mutation generateUploadData($fileName: String) {generateUploadData(name: $fileName)}",
            "variables": {"fileName": file.name}
        }
        fetch(process.env.API_ENDPOINT + '/graphql', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify(query)
        })
                .then(r => r.json())
                .then(data => enrichForm(JSON.parse(data['data']['generateUploadData'])));
    }

    let enrichForm = ({url, fields}) => {
        presigned_url = url
        form_fields = fields
    }
</script>
