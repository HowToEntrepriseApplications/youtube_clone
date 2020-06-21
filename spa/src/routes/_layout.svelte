<header>
	<nav>
		<a href="/">youtube clone</a>
		{#if is_authenticated}
			<a href="/upload">upload video</a>
		{/if}
		<Auth bind:is_authenticated />
	</nav>
</header>
<main>
	<slot></slot>
</main>

<script>
	import Auth from '../components/Auth.svelte';
	let is_authenticated;
</script>
