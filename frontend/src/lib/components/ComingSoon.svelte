<script>
	import { ArrowLeft } from '@lucide/svelte';
	import { resolve } from '$app/paths';
	import { Button } from '#lib/components/ui/button/index.js';
	import { reveal } from '#lib/motion/reveal.js';
	let { title = 'Workspace', description = 'This page is not available yet.' } = $props();
</script>

<svelte:head><title>{title} · Brightloop</title></svelte:head>

<main id="main-content" class="px-4 py-8" {@attach reveal}>
	<div class="flex max-w-lg flex-col gap-4">
		<div data-reveal class="flex flex-col gap-2">
			<h1 class="text-2xl font-semibold tracking-tight">{title}</h1>
			<p class="text-sm text-muted-foreground">{description}</p>
		</div>
		<div data-reveal>
			<Button href={resolve('/')} variant="outline"
				><ArrowLeft data-icon="inline-start" />Back to Brightloop</Button
			>
		</div>
	</div>
</main>
