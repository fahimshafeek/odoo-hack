<script>
	import { Check, Circle, Minus } from '@lucide/svelte';
	import { cn } from '#lib/utils.js';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	/** @type {{status: string, history?: any[], compact?: boolean}} */
	let { status, history, compact = false } = $props();
	const steps = ['draft', 'quotation', 'confirmed', 'active', 'closed'];
	const current = $derived(steps.indexOf(status === 'paused' ? 'active' : status));
	const visited = $derived(
		new Set((history ?? []).flatMap((item) => [item.from_status, item.to_status]))
	);
</script>

<ol
	aria-label="Subscription progress"
	class={cn('grid gap-3', compact ? 'grid-cols-5' : 'sm:grid-cols-5')}
>
	{#each steps as step, index (step)}
		{@const complete =
			status === 'closed' ? index < 4 && (visited.has(step) || step === 'draft') : index < current}
		{@const skipped =
			status === 'closed' && history !== undefined && index > 0 && index < 4 && !visited.has(step)}
		<li
			aria-current={index === current ? 'step' : undefined}
			aria-label={`${step}: ${index === current ? 'current' : complete ? 'completed' : skipped ? 'skipped' : 'upcoming'}`}
			class={cn('flex min-w-0 items-center gap-3', !compact && 'sm:flex-col sm:items-start')}
		>
			<span
				class={cn(
					'flex size-8 shrink-0 items-center justify-center rounded-full border',
					index === current
						? 'border-primary bg-primary text-primary-foreground'
						: complete
							? 'border-status-active/20 bg-status-active/10 text-status-active'
							: 'border-border bg-muted text-muted-foreground',
					compact && 'size-6'
				)}
			>
				{#if complete}<Check class="size-3" aria-hidden="true" />{:else if skipped}<Minus
						class="size-3"
						aria-hidden="true"
					/>{:else}<Circle class="size-3" aria-hidden="true" />{/if}
			</span>
			<span
				class={cn(
					'text-xs font-medium capitalize',
					index === current ? 'text-primary' : 'text-muted-foreground',
					skipped && 'line-through',
					compact && 'sr-only'
				)}
				>{step}{#if step === 'active' && status === 'paused'}<span class="ml-2"
						><StatusBadge kind="subscription" value="paused" /></span
					>{/if}</span
			>
		</li>
	{/each}
</ol>
