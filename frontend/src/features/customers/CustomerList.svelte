<script>
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { Plus } from '@lucide/svelte';
	import { createListQuery } from '#src/api/resources.js';
	import { useListParams } from '#lib/use-list-params.js';
	import { formatDate } from '#lib/format.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { PageHeader, DataTable, FilterBar, SearchInput } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import CustomerDialog from './CustomerDialog.svelte';
	import { customerName } from './schemas.js';
	const list = useListParams();
	const customers = createListQuery('customers', '/customers', () => list.value);
	let adding = $state(false);
	const columns = [
		{ key: 'full_name', header: 'Customer', cell: nameCell },
		{ key: 'email', header: 'Email' },
		{ key: 'phone', header: 'Phone', cell: phoneCell },
		{ key: 'tax_id', header: 'Tax ID', cell: taxCell },
		{ key: 'created_at', header: 'Added', cell: dateCell }
	];
	function open(/** @type {any} */ customer) {
		void goto(resolve('/[...path]', { path: `app/customers/${customer.id}` }));
	}
</script>

<svelte:head><title>Customers · Brightloop</title></svelte:head>
{#snippet nameCell(row = /** @type {any} */ ({}))}<span class="font-medium"
		>{customerName(row)}</span
	>{/snippet}
{#snippet phoneCell(row = /** @type {any} */ ({}))}{row.phone || '—'}{/snippet}
{#snippet taxCell(row = /** @type {any} */ ({}))}{row.tax_id || '—'}{/snippet}
{#snippet dateCell(row = /** @type {any} */ ({}))}{formatDate(row.created_at)}{/snippet}
<main id="main-content" class="flex flex-col gap-4" {@attach reveal}>
	<div data-reveal>
		<PageHeader title="Customers" subtitle="Customer accounts and billing details."
			>{#snippet primaryAction()}<Button onclick={() => (adding = true)}
					><Plus data-icon="inline-start" />Add customer</Button
				>{/snippet}</PageHeader
		>
	</div>
	<div data-reveal>
		<DataTable
			{columns}
			data={$customers.data}
			isLoading={$customers.isPending}
			isError={$customers.isError}
			onRetry={() => void $customers.refetch()}
			params={list.value}
			onParamsChange={list.update}
			onRowClick={open}
			emptyTitle="No customers found"
			emptyDescription="Add a customer or adjust your search."
			>{#snippet toolbar()}<FilterBar
					><SearchInput
						value={list.value.q}
						onChange={(q) => list.update({ q })}
						placeholder="Search customers…"
					/></FilterBar
				>{/snippet}{#snippet mobileCard(row)}<div class="flex flex-col gap-2">
					<p class="font-medium">{customerName(row)}</p>
					<p class="text-sm text-muted-foreground">{row.email}</p>
					{#if row.phone}<p class="text-sm text-muted-foreground">{row.phone}</p>{/if}
				</div>{/snippet}</DataTable
		>
	</div>
</main>
{#if adding}<CustomerDialog onClose={() => (adding = false)} />{/if}
