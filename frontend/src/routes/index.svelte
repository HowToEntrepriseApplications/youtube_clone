<svelte:head>
	<title>Youtube clone</title>
</svelte:head>

{#if is_authenticated}
	<button on:click={logout}>logout</button>
{:else}
	<button on:click={login}>login</button>
{/if}

{#each videos as video}
	<div><h3>{video['name']}</h3></div>
{/each}

<script context="module">
		const videos = [{'name': '1'}, {'name': 2}];
</script>

<script>
	import { onMount } from 'svelte';

	let is_authenticated = false;
	let login = () => {};
	let logout = () => {};

	onMount(async () => {
		const Keycloak = (await import('keycloak-js')).default
		const keycloak = Keycloak('/keycloak.json');

		keycloak.init({onLoad: 'check-sso'}).then(authenticated => { is_authenticated = authenticated})

		login = () => {
			keycloak.init({onLoad: 'login-required'}).then(authenticated => { is_authenticated = authenticated})
		}

		logout = () => {
			keycloak.logout()
		}
	});
</script>
