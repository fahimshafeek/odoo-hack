<script>
	/** @type {{title: string, subtitle?: string, primaryAction?: import('svelte').Snippet, actions?: import('svelte').Snippet}} */
	let { title, subtitle, primaryAction, actions } = $props();
</script>

<div class="mb-8 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
	<div class="flex min-w-0 flex-col gap-2">
		<h1 class="text-2xl font-semibold tracking-tight md:text-3xl">{title}</h1>
		{#if subtitle}<p class="text-sm leading-relaxed text-muted-foreground">{subtitle}</p>{/if}
	</div>
	{#if actions || primaryAction}<div class="page-actions flex flex-wrap items-center gap-2">
			{@render actions?.()}{@render primaryAction?.()}
		</div>{/if}
</div>
