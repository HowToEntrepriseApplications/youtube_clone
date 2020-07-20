<form action="{presigned_url}" method="post" enctype="multipart/form-data">
    {#each Object.entries(form_fields) as [name, value] (name) }
        <input type="hidden" name="{ name }" value="{ value }" />
    {/each}
    <div class="input-group">
      <div class="custom-file">
        <input type="file" name="file" class="custom-file-input" id="customFile" bind:files>
        <label class="custom-file-label" for="customFile">Choose file</label>
      </div>
      <div class="input-group-append">
        <button class="btn btn-outline-secondary" type="submit" disabled={!video_added}>Upload</button>
      </div>
    </div>
</form>


<script>
    import { onMount } from 'svelte';
    import { jwt } from '../../store.js';

    let video_added = false;
    let presigned_url = undefined;
    let form_fields = {};
    let files;

    onMount(async () => {
        const bsCustomFileInput = (await import('bs-custom-file-input')).default
        bsCustomFileInput.init()
    })

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
                'Authorization': `Bearer ` + $jwt,
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
