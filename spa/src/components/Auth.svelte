<auth>
    {#if is_authenticated}
        <button on:click={logout}>logout</button>
    {:else}
        <button on:click={login}>login</button>
    {/if}
</auth>

<script>
	import { onMount } from 'svelte';
	import { jwt } from '../store.js';

	export let is_authenticated = false;
	export let token = undefined;
	export let refreshToken = undefined;
	let login = () => {};
	let logout = () => {};

    onMount(async () => {

        const Keycloak = (await import('keycloak-js')).default
        const keycloak = Keycloak({
            url: process.env.KEYCLOAK_URL,
            realm: process.env.KEYCLOAK_REALM,
            clientId: process.env.KEYCLOAK_CLIENT_ID,
        });

        let onAuth = () => {
            is_authenticated = true;
            jwt.set(keycloak.token)
        }

        keycloak.init({
            onLoad: 'check-sso',
            silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html'
        }).then(authenticated => { if (authenticated) onAuth() })

        login = () => {
            keycloak.init({onLoad: 'login-required'}).then(authenticated => { if (authenticated) onAuth() })
        }

        logout = () => {
            keycloak.logout()
        }
	});
</script>
