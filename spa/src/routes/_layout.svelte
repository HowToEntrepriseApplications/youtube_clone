<header>
	<nav class="navbar navbar-expand-lg">
		<ul class="navbar-nav mr-auto">
			<li class="nav-item">
				<a href="/" class="nav-link">Boring art</a>
			</li>
			{#if is_authenticated}
			<li class="nav-item">
				<a href="/upload" class="nav-link">upload video</a>
			</li>
			{/if}
		</ul>
		<div class="my-2 my-lg-0">
			<Auth bind:is_authenticated/>
		</div>
	</nav>
</header>
<main>
	<div class="container">
		<slot></slot>
	</div>
</main>

<script>
	import Auth from '../components/Auth.svelte';
	let is_authenticated;
</script>
