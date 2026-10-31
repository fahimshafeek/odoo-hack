<script>
	import { ArrowLeft, Layers3 } from '@lucide/svelte';
	import { Button } from '#lib/components/ui/button/index.js';
	import { reveal } from '#lib/motion/reveal.js';
	let { title = 'Your workspace', description = 'This part of your workspace is being prepared.' } =
		$props();
</script>

<svelte:head><title>{title} · Brightloop</title></svelte:head>

<main id="main-content" class="grid min-h-svh place-items-center px-4 py-16" {@attach reveal}>
	<div class="flex max-w-md flex-col items-center gap-6 text-center">
		<div
			data-reveal
			class="flex size-16 items-center justify-center rounded-2xl bg-primary/10 text-primary"
		>
			<Layers3 aria-hidden="true" />
		</div>
		<div data-reveal class="flex flex-col gap-3">
			<p class="text-xs font-semibold tracking-widest text-muted-foreground uppercase">
				Brightloop workspace
			</p>
			<h1 class="text-3xl font-semibold tracking-tight">{title}</h1>
			<p class="text-sm leading-relaxed text-muted-foreground">{description}</p>
		</div>
		<div data-reveal>
			<Button href="/" variant="outline"
				><ArrowLeft data-icon="inline-start" />Back to Brightloop</Button
			>
		</div>
	</div>
</main>
