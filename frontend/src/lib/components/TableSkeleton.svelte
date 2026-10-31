<script>
	import { Skeleton } from './ui/skeleton/index.js';
	let { rows = 5 } = $props();
</script>

<div role="status" aria-label="Loading records" class="flex flex-col gap-4 p-6">
	{#each Array.from({ length: rows }, (_, index) => index) as row (row)}<Skeleton
			class="h-10 w-full"
		/>{/each}<span class="sr-only">Loading records…</span>
</div>
