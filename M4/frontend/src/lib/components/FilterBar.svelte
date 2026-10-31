<script>
	import { X } from '@lucide/svelte';
	import { Button } from './ui/button/index.js';
	/** @type {{children: import('svelte').Snippet, params?: Record<string, any>, onChange?: (patch: Record<string, string>) => any}} */
	let { children, params = {}, onChange } = $props();
	const names = /** @type {Record<string, string>} */ ({
		q: 'Search',
		status: 'Status',
		method: 'Method',
		customer_id: 'Customer',
		plan_id: 'Plan',
		date_from: 'From',
		date_to: 'Through',
		payment_filter: 'Payment'
	});
	const active = $derived(
		Object.entries(params).filter(
			([key, value]) => names[key] && value !== '' && value != null && value !== 'all'
		)
	);
	function label(/** @type {string} */ key, /** @type {any} */ value) {
		return key.endsWith('_id')
			? `${names[key]} selected`
			: `${names[key]}: ${String(value).replaceAll('_', ' ')}`;
	}
</script>

<div class="filter-bar flex flex-col gap-3">
	<div class="flex flex-col gap-3 md:flex-row md:flex-wrap md:items-center">
		{@render children()}
	</div>
	{#if active.length && onChange}
		<div class="flex flex-wrap items-center gap-2" aria-label="Active filters">
			<span class="text-xs font-medium text-muted-foreground"
				>{active.length} active {active.length === 1 ? 'filter' : 'filters'}</span
			>
			{#each active as [key, value] (key)}<Button
					variant="secondary"
					size="sm"
					aria-label={`Remove ${label(key, value)} filter`}
					onclick={() => onChange?.({ [key]: '' })}
					>{label(key, value)}<X data-icon="inline-end" /></Button
				>{/each}
			<Button
				variant="ghost"
				size="sm"
				onclick={() => onChange?.(Object.fromEntries(active.map(([key]) => [key, ''])))}
				>Clear all</Button
			>
		</div>
	{/if}
</div>

<style>
	.filter-bar :global([data-active='true']) {
		border-color: var(--foreground);
		background: var(--secondary);
		box-shadow: 0 0 0 1px var(--foreground);
	}
</style>
