<script>
	import AdminLayout from '#src/layouts/AdminLayout.svelte';
	/** @type {{children: import('svelte').Snippet}} */
	let { children } = $props();
</script>

<AdminLayout>{@render children()}</AdminLayout>
