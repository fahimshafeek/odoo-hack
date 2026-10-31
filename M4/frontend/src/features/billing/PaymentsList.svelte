<script>
	import { resolve } from '$app/paths';
	import { useListParams } from '#lib/use-list-params.js';
	import { formatDate } from '#lib/format.js';
	import { reveal } from '#lib/motion/reveal.js';
	import {
		PageHeader,
		DataTable,
		FilterBar,
		SearchInput,
		MoneyCell
	} from '#lib/components/index.js';
	import DatePicker from '#lib/components/DatePicker.svelte';
	import * as NativeSelect from '#lib/components/ui/native-select/index.js';
	import CustomerFilter from './CustomerFilter.svelte';
	import { usePayments } from './api.js';
	const list = useListParams();
	const payments = usePayments(() => list.value);
	const columns = [
		{ key: 'invoice', header: 'Invoice', cell: invoiceCell },
		{ key: 'customer', header: 'Customer', cell: customerCell },
		{ key: 'amount', header: 'Amount', cell: amountCell },
		{ key: 'method', header: 'Method', cell: methodCell },
		{ key: 'paid_on', header: 'Payment date', cell: dateCell, sortKey: 'paid_on' },
		{ key: 'note', header: 'Note', cell: noteCell },
		{ key: 'recorded_by', header: 'Recorded by', cell: actorCell }
	];
	function methodLabel(/** @type {string} */ method) {
		return method === 'upi' ? 'UPI' : method?.replaceAll('_', ' ');
	}
</script>

<svelte:head><title>Payments · Brightloop</title></svelte:head>
{#snippet invoiceCell(row = /** @type {any} */ ({}))}<a
		href={resolve('/[...path]', { path: `app/invoices/${row.invoice?.id ?? row.invoice_id}` })}
		class="font-medium underline-offset-4 hover:underline"
		>{row.invoice?.number ?? 'View invoice'}</a
	>{/snippet}
{#snippet customerCell(row = /** @type {any} */ ({}))}{row.customer?.name ?? 'Customer'}{/snippet}
{#snippet amountCell(row = /** @type {any} */ ({}))}<MoneyCell value={row.amount} />{/snippet}
{#snippet methodCell(row = /** @type {any} */ ({}))}<span class="capitalize"
		>{methodLabel(row.method)}</span
	>{/snippet}
{#snippet dateCell(row = /** @type {any} */ ({}))}{formatDate(row.paid_on)}{/snippet}
{#snippet noteCell(row = /** @type {any} */ ({}))}<span
		class="block max-w-xs truncate"
		title={row.note ?? ''}>{row.note || '—'}</span
	>{/snippet}
{#snippet actorCell(row = /** @type {any} */ ({}))}{row.recorded_by?.name ??
		(row.method === 'online' ? 'Customer payment' : '—')}{/snippet}
<main id="main-content" class="flex flex-col gap-4" {@attach reveal}>
	<div data-reveal>
		<PageHeader title="Payments" subtitle="Recorded customer payments." />
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
			emptyDescription="Try adjusting your filters."
		>
			{#snippet toolbar()}<FilterBar
					><SearchInput
						value={list.value.q}
						onChange={(q) => list.update({ q })}
						placeholder="Search payments…"
					/><NativeSelect.Root
						value={String(list.value.method ?? '')}
						aria-label="Payment method"
						onchange={(/** @type {Event} */ event) =>
							list.update({ method: /** @type {HTMLSelectElement} */ (event.currentTarget).value })}
						><NativeSelect.Option value="">All methods</NativeSelect.Option
						>{#each ['cash', 'bank_transfer', 'card', 'upi', 'cheque', 'online'] as method (method)}<NativeSelect.Option
								value={method}>{methodLabel(method)}</NativeSelect.Option
							>{/each}</NativeSelect.Root
					><DatePicker
						label="Payments from"
						value={String(list.value.date_from ?? '')}
						onChange={(value) => list.update({ date_from: value })}
					/><DatePicker
						label="Payments through"
						value={String(list.value.date_to ?? '')}
						onChange={(value) => list.update({ date_to: value })}
					/><CustomerFilter
						value={String(list.value.customer_id ?? '')}
						onChange={(customer_id) => list.update({ customer_id })}
					/></FilterBar
				>{/snippet}
			{#snippet mobileCard(row)}<div class="flex flex-col gap-3">
					<div class="flex items-center justify-between gap-3">
						<a
							href={resolve('/[...path]', {
								path: `app/invoices/${row.invoice?.id ?? row.invoice_id}`
							})}
							class="font-medium underline-offset-4 hover:underline"
							>{row.invoice?.number ?? 'View invoice'}</a
						><MoneyCell value={row.amount} />
					</div>
					<p class="text-sm text-muted-foreground">{row.customer?.name ?? 'Customer'}</p>
					<div class="flex items-center justify-between gap-3 text-xs text-muted-foreground">
						<span class="capitalize">{methodLabel(row.method)}</span><span
							>{formatDate(row.paid_on)}</span
						>
					</div>
					{#if row.note}<p class="text-sm">{row.note}</p>{/if}{#if row.recorded_by?.name}<p
							class="text-xs text-muted-foreground"
						>
							Recorded by {row.recorded_by.name}
						</p>{/if}
				</div>{/snippet}
		</DataTable>
	</div>
</main>
