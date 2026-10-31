<script>
	import PortalLayout from '#src/layouts/PortalLayout.svelte';
	/** @type {{children: import('svelte').Snippet}} */
	let { children } = $props();
</script>

<PortalLayout>{@render children()}</PortalLayout>
