<script>
	/** @type {{children: import('svelte').Snippet}} */
	let { children } = $props();
</script>

<div class="flex flex-col gap-3 md:flex-row md:flex-wrap md:items-center">{@render children()}</div>
