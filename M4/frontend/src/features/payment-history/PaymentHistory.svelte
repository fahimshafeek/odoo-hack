<script>
	import { resolve } from '$app/paths';
	import { createListQuery } from '#src/api/resources.js';
	import { useListParams } from '#lib/use-list-params.js';
	import { formatDate } from '#lib/format.js';
	import { reveal } from '#lib/motion/reveal.js';
	import {
		PageHeader,
		DataTable,
		MoneyCell,
		FilterBar,
		SearchInput
	} from '#lib/components/index.js';
	import { Input } from '#lib/components/ui/input/index.js';
	import * as NativeSelect from '#lib/components/ui/native-select/index.js';
	const list = useListParams();
	const payments = createListQuery('payments', '/me/payments', () => list.value);
	const columns = [
		{ key: 'invoice', header: 'Invoice', cell: invoiceCell },
		{ key: 'paid_on', header: 'Date', cell: dateCell },
		{ key: 'method', header: 'Method', cell: methodCell },
		{ key: 'amount', header: 'Amount', cell: amountCell },
		{ key: 'note', header: 'Note', cell: noteCell }
	];
	function methodLabel(/** @type {string} */ method) {
		return method === 'upi' ? 'UPI' : method?.replaceAll('_', ' ');
	}
</script>

<svelte:head><title>Payment history · Brightloop</title></svelte:head>
{#snippet invoiceCell(row = /** @type {any} */ ({}))}<a
		href={resolve('/[...path]', { path: `portal/invoices/${row.invoice?.id ?? row.invoice_id}` })}
		class="font-medium underline-offset-4 hover:underline"
		>{row.invoice?.number ?? 'View invoice'}</a
	>{/snippet}
{#snippet dateCell(row = /** @type {any} */ ({}))}{formatDate(row.paid_on)}{/snippet}
{#snippet methodCell(row = /** @type {any} */ ({}))}<span class="capitalize"
		>{methodLabel(row.method)}</span
	>{/snippet}
{#snippet amountCell(row = /** @type {any} */ ({}))}<MoneyCell value={row.amount} />{/snippet}
{#snippet noteCell(row = /** @type {any} */ ({}))}<span
		class="block max-w-xs truncate"
		title={row.note ?? ''}>{row.note || '—'}</span
	>{/snippet}
<main id="main-content" class="flex flex-col gap-4" {@attach reveal}>
	<div data-reveal>
		<PageHeader title="Payment history" subtitle="Payments recorded against your invoices." />
	</div>
	<div data-reveal>
		<DataTable
			{columns}
			data={$payments.data}
			isLoading={$payments.isPending}
			isError={$payments.isError}
			onRetry={() => void $payments.refetch()}
			params={list.value}
			onParamsChange={list.update}
			emptyTitle="No payments found"
			emptyDescription="Payments appear here after they are recorded."
			>{#snippet toolbar()}<FilterBar
					><SearchInput
						value={list.value.q}
						onChange={(q) => list.update({ q })}
						placeholder="Search payments…"
					/><NativeSelect.Root
						aria-label="Payment method"
						value={String(list.value.method ?? '')}
						onchange={(/** @type {Event} */ event) =>
							list.update({ method: /** @type {HTMLSelectElement} */ (event.currentTarget).value })}
						><NativeSelect.Option value="">All methods</NativeSelect.Option
						>{#each ['cash', 'bank_transfer', 'card', 'upi', 'cheque', 'online'] as method (method)}<NativeSelect.Option
								value={method}>{methodLabel(method)}</NativeSelect.Option
							>{/each}</NativeSelect.Root
					><Input
						type="date"
						aria-label="Payments from"
						value={String(list.value.date_from ?? '')}
						onchange={(/** @type {Event} */ event) =>
							list.update({
								date_from: /** @type {HTMLInputElement} */ (event.currentTarget).value
							})}
					/><Input
						type="date"
						aria-label="Payments through"
						value={String(list.value.date_to ?? '')}
						onchange={(/** @type {Event} */ event) =>
							list.update({ date_to: /** @type {HTMLInputElement} */ (event.currentTarget).value })}
					/></FilterBar
				>{/snippet}{#snippet mobileCard(row)}<div class="flex flex-col gap-3">
					<div class="flex items-center justify-between gap-3">
						<a
							href={resolve('/[...path]', {
								path: `portal/invoices/${row.invoice?.id ?? row.invoice_id}`
							})}
							class="font-medium underline-offset-4 hover:underline"
							>{row.invoice?.number ?? 'View invoice'}</a
						><MoneyCell value={row.amount} />
					</div>
					<div class="flex justify-between gap-3 text-xs text-muted-foreground">
						<span>{formatDate(row.paid_on)}</span><span class="capitalize"
							>{methodLabel(row.method)}</span
						>
					</div>
					{#if row.note}<p class="text-sm">{row.note}</p>{/if}
				</div>{/snippet}</DataTable
		>
	</div>
</main>
