<script>
	import { page } from '$app/state';
	import { Button } from '#lib/components/ui/button/index.js';
</script>

<svelte:head><title>{page.status} · Brightloop</title></svelte:head>
<main id="main-content" class="grid min-h-svh place-items-center p-6">
	<div class="flex max-w-md flex-col items-center gap-4 text-center">
		<p class="text-sm font-medium text-primary">{page.status}</p>
		<h1 class="text-3xl font-semibold tracking-tight">
			{page.status === 404 ? 'This page took a different turn.' : 'Something interrupted the flow.'}
		</h1>
		<p class="text-sm text-muted-foreground">
			{page.status === 404
				? 'Check the address, or head back to your workspace.'
				: 'Please try again in a moment.'}
		</p>
		<Button href="/">Back to Brightloop</Button>
	</div>
</main>
