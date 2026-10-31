<script>
	/** @type {{title: string, subtitle?: string, primaryAction?: import('svelte').Snippet, actions?: import('svelte').Snippet}} */
	let { title, subtitle, primaryAction, actions } = $props();
</script>

<div class="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
	<div class="flex min-w-0 flex-col gap-1">
		<h1 class="text-2xl font-semibold tracking-tight">{title}</h1>
		{#if subtitle}<p class="max-w-2xl text-sm text-muted-foreground">{subtitle}</p>{/if}
	</div>
	{#if actions || primaryAction}<div class="page-actions flex flex-wrap items-center gap-2">
			{@render actions?.()}{@render primaryAction?.()}
		</div>{/if}
</div>
