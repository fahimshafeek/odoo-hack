<script>
	import { page } from '$app/state';
	import { findRoute } from '#src/app/routes.js';
	let { data } = $props();
	const route = $derived(findRoute(page.url.pathname));
	const Component = $derived(route?.component);
</script>

{#if Component}<Component {...route?.props ?? {}} title={data.title} />{/if}
