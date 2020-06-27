<auth>
    {#if is_authenticated}
        <button on:click={logout}>logout</button>
    {:else}
        <button on:click={login}>login</button>
    {/if}
</auth>

<script>
	import { onMount } from 'svelte';

	export let is_authenticated = false;
	let login = () => {};
	let logout = () => {};

    onMount(async () => {

        const Keycloak = (await import('keycloak-js')).default
        const keycloak = Keycloak({
            url: process.env.KEYCLOAK_URL,
            realm: process.env.KEYCLOAK_REALM,
            clientId: process.env.KEYCLOAK_CLIENT_ID,
        });

        keycloak.init({
            onLoad: 'check-sso',
            silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html'
        }).then(authenticated => { is_authenticated = authenticated })

        login = () => {
            keycloak.init({onLoad: 'login-required'}).then(authenticated => { is_authenticated = authenticated })
        }

        logout = () => {
            keycloak.logout()
        }
	});
</script>
