<script>
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { useListParams } from '#lib/use-list-params.js';
	import { formatDate } from '#lib/format.js';
	import { reveal } from '#lib/motion/reveal.js';
	import {
		PageHeader,
		DataTable,
		FilterBar,
		SearchInput,
		StatusBadge,
		MoneyCell
	} from '#lib/components/index.js';
	import DatePicker from '#lib/components/DatePicker.svelte';
	import * as NativeSelect from '#lib/components/ui/native-select/index.js';
	import * as Tabs from '#lib/components/ui/tabs/index.js';
	import CustomerFilter from './CustomerFilter.svelte';
	import { useInvoices } from './api.js';
	/** @type {{portal?: boolean}} */
	let { portal = false } = $props();
	const list = useListParams();
	const invoices = useInvoices(
		() => portal,
		() => list.value
	);
	const columns = $derived([
		{ key: 'number', header: 'Invoice', sortKey: 'number' },
		...(!portal ? [{ key: 'customer', header: 'Customer', cell: customerCell }] : []),
		{ key: 'period_start', header: 'Period', cell: periodCell },
		{ key: 'due_date', header: 'Due date', sortKey: 'due_date', cell: dueCell },
		{ key: 'total', header: 'Total', cell: totalCell },
		{ key: 'amount_paid', header: 'Paid', cell: paidCell },
		{ key: 'balance', header: 'Balance', cell: balanceCell },
		{ key: 'payment_state', header: 'Payment', cell: stateCell }
	]);
	function open(/** @type {any} */ invoice) {
		void goto(
			resolve('/[...path]', { path: `${portal ? 'portal' : 'app'}/invoices/${invoice.id}` })
		);
	}
</script>

<svelte:head><title>{portal ? 'My invoices' : 'Invoices'} · Brightloop</title></svelte:head>
{#snippet customerCell(row = /** @type {any} */ ({}))}<span class="font-medium"
		>{row.customer?.name ?? 'Customer'}</span
	>{/snippet}
{#snippet periodCell(row = /** @type {any} */ ({}))}<span class="text-xs whitespace-nowrap"
		>{formatDate(row.period_start)} – {formatDate(row.period_end)}</span
	>{/snippet}
{#snippet dueCell(row = /** @type {any} */ ({}))}<div class="flex flex-col gap-1">
		<span>{formatDate(row.due_date)}</span>{#if row.is_overdue}<span
				class="text-xs text-destructive">{row.days_overdue} days overdue</span
			>{/if}
	</div>{/snippet}
{#snippet totalCell(row = /** @type {any} */ ({}))}<MoneyCell value={row.total} />{/snippet}
{#snippet paidCell(row = /** @type {any} */ ({}))}<MoneyCell value={row.amount_paid} />{/snippet}
{#snippet balanceCell(row = /** @type {any} */ ({}))}<MoneyCell value={row.balance} />{/snippet}
{#snippet stateCell(row = /** @type {any} */ ({}))}<StatusBadge
		kind="payment_state"
		value={row.payment_state ?? 'not_applicable'}
	/>{/snippet}

<main id="main-content" class="flex flex-col gap-4" {@attach reveal}>
	<div data-reveal>
		<PageHeader
			title={portal ? 'My invoices' : 'Invoices'}
			subtitle={portal
				? 'View invoices and make payments.'
				: 'Review invoices and outstanding balances.'}
		/>
	</div>
	<div data-reveal>
		<Tabs.Root
			value={String(list.value.payment_filter || 'all')}
			onValueChange={(/** @type {string} */ value) =>
				list.update({ payment_filter: value === 'all' ? '' : value })}
			><Tabs.List aria-label="Payment filter"
				><Tabs.Trigger value="all">All invoices</Tabs.Trigger><Tabs.Trigger value="paid"
					>Paid</Tabs.Trigger
				><Tabs.Trigger value="outstanding">Outstanding</Tabs.Trigger><Tabs.Trigger value="overdue"
					>Overdue</Tabs.Trigger
				></Tabs.List
			></Tabs.Root
		>
	</div>
	<div data-reveal>
		<DataTable
			{columns}
			data={$invoices.data}
			isLoading={$invoices.isPending}
			isError={$invoices.isError}
			onRetry={() => void $invoices.refetch()}
			params={list.value}
			onParamsChange={list.update}
			onRowClick={open}
			emptyTitle="No invoices found"
			emptyDescription="Invoices appear when subscriptions are billed."
		>
			{#snippet toolbar()}<FilterBar params={list.value} onChange={list.update}
					><SearchInput
						value={list.value.q}
						onChange={(q) => list.update({ q })}
						placeholder="Search invoices or customers…"
					/><NativeSelect.Root
						value={String(list.value.status ?? '')}
						aria-label="Invoice status"
						onchange={(/** @type {Event} */ event) =>
							list.update({ status: /** @type {HTMLSelectElement} */ (event.currentTarget).value })}
						><NativeSelect.Option value="">All statuses</NativeSelect.Option
						>{#each portal ? ['confirmed', 'paid'] : ['draft', 'confirmed', 'paid', 'cancelled'] as status (status)}<NativeSelect.Option
								value={status}>{status[0].toUpperCase() + status.slice(1)}</NativeSelect.Option
							>{/each}</NativeSelect.Root
					><DatePicker
						label="Issued from"
						value={String(list.value.date_from ?? '')}
						onChange={(value) => list.update({ date_from: value })}
					/><DatePicker
						label="Issued through"
						value={String(list.value.date_to ?? '')}
						onChange={(value) => list.update({ date_to: value })}
					/>{#if !portal}<CustomerFilter
							value={String(list.value.customer_id ?? '')}
							onChange={(customer_id) => list.update({ customer_id })}
						/>{/if}</FilterBar
				>{/snippet}
			{#snippet mobileCard(row)}<div class="flex flex-col gap-3">
					<div class="flex items-center justify-between gap-3">
						<span class="font-medium">{row.number}</span>
						<StatusBadge kind="invoice" value={row.status} />
					</div>
					{#if !portal}<p class="text-sm text-muted-foreground">
							{row.customer?.name ?? 'Customer'}
						</p>{/if}
					<div class="grid grid-cols-2 gap-3 text-sm">
						<span class="text-muted-foreground">Due {formatDate(row.due_date)}</span><MoneyCell
							value={row.balance}
						/>
					</div>
					<div class="flex items-center justify-between gap-2">
						<StatusBadge kind="payment_state" value={row.payment_state} />{#if row.is_overdue}<span
								class="text-xs text-destructive">{row.days_overdue} days overdue</span
							>{/if}
					</div>
				</div>{/snippet}
		</DataTable>
	</div>
</main>
