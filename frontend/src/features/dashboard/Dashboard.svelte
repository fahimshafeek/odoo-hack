<script>
	import { resolve } from '$app/paths';
	import { Download } from '@lucide/svelte';
	import { createDetailQuery, createListQuery } from '#src/api/resources.js';
	import { formatMoney, formatDate } from '#lib/format.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { downloadReportCsv } from '#lib/export.js';
	import {
		PageHeader,
		StatCard,
		CardSkeleton,
		TableSkeleton,
		ErrorState,
		EmptyState,
		MoneyCell
	} from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Table from '#lib/components/ui/table/index.js';
	import * as DropdownMenu from '#lib/components/ui/dropdown-menu/index.js';
	import * as NativeSelect from '#lib/components/ui/native-select/index.js';
	import RevenueChart from './RevenueChart.svelte';

	let months = $state(6);
	const summary = createDetailQuery('dashboard', '/reports/summary');
	const revenue = createListQuery('dashboard', '/reports/revenue-by-month', () => ({ months }));
	const overdue = createListQuery('dashboard', '/reports/overdue-invoices', () => ({
		page: 1,
		page_size: 5
	}));
	const renewals = createListQuery('dashboard', '/reports/upcoming-renewals', () => ({
		page: 1,
		page_size: 5,
		days: 30
	}));

	const stats = $derived($summary.data);
	const revenueRows = $derived(Array.isArray($revenue.data) ? $revenue.data : []);
	const overdueRows = $derived($overdue.data?.items ?? []);
	const renewalRows = $derived($renewals.data?.items ?? []);
</script>

<svelte:head><title>Overview · Brightloop</title></svelte:head>
<main id="main-content" class="flex flex-col gap-4" {@attach reveal}>
	<div data-reveal>
		<PageHeader
			title="Overview"
			subtitle={stats?.as_of
				? `As of ${formatDate(stats.as_of)}`
				: 'Subscription and billing summary.'}
		>
			{#snippet actions()}
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						<Button variant="outline"><Download data-icon="inline-start" />Export CSV</Button>
					</DropdownMenu.Trigger>
					<DropdownMenu.Content align="end" class="w-56">
						<DropdownMenu.Group>
							<DropdownMenu.GroupHeading>CSV Reports</DropdownMenu.GroupHeading>
							<DropdownMenu.Item onclick={() => downloadReportCsv('overdue')}>Overdue invoices</DropdownMenu.Item>
							<DropdownMenu.Item onclick={() => downloadReportCsv('upcoming_renewals')}>Upcoming renewals</DropdownMenu.Item>
							<DropdownMenu.Item onclick={() => downloadReportCsv('subscriptions')}>All subscriptions</DropdownMenu.Item>
						</DropdownMenu.Group>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
				<Button
					href={resolve('/[...path]', { path: 'app/invoices' })}
					variant="outline">View invoices</Button
				>
			{/snippet}
		</PageHeader>
	</div>

	<section aria-label="Billing summary" data-reveal>
		{#if $summary.isPending}<div
				class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
				role="status"
				aria-label="Loading summary"
			>
				{#each [1, 2, 3, 4] as card (card)}<CardSkeleton />{/each}
			</div>{:else if $summary.isError}<ErrorState
				onRetry={() => void $summary.refetch()}
			/>{:else if stats}<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
				<StatCard
					title="Revenue collected"
					value={formatMoney(stats.revenue_collected)}
					hint="This month"
				/><StatCard
					title="Outstanding"
					value={formatMoney(stats.outstanding_total)}
					hint="Unpaid invoice balances"
				/><StatCard
					title="Active subscriptions"
					value={stats.active_subscriptions}
					hint={`${formatMoney(stats.mrr)} monthly recurring revenue`}
				/><StatCard
					title="Overdue invoices"
					value={stats.overdue_count}
					hint={`${formatMoney(stats.overdue_total)} overdue`}
				/>
			</div>{:else}<EmptyState
				title="No summary available"
				description="Summary figures will appear when billing data is available."
			/>{/if}
	</section>

	<Card.Root data-reveal>
		<Card.Header>
			<Card.Title>Revenue</Card.Title>
			<Card.Description>Collected payments and confirmed invoices by month.</Card.Description>
			<Card.Action>
				<NativeSelect.Root
					value={String(months)}
					aria-label="Revenue period"
					onchange={(/** @type {Event} */ event) =>
						(months = Number(/** @type {HTMLSelectElement} */ (event.currentTarget).value))}
				>
					<NativeSelect.Option value="6">Last 6 months</NativeSelect.Option>
					<NativeSelect.Option value="12">Last 12 months</NativeSelect.Option>
				</NativeSelect.Root>
			</Card.Action>
		</Card.Header>
		<Card.Content>
			{#if $revenue.isPending}
				<div class="flex h-72 items-center justify-center" role="status">
					<span class="text-sm text-muted-foreground">Loading revenue…</span>
				</div>
			{:else if $revenue.isError}
				<ErrorState onRetry={() => void $revenue.refetch()} />
			{:else if !revenueRows.length}
				<EmptyState
					title="No revenue data"
					description="Monthly totals appear as invoices and payments are recorded."
				/>
			{:else}
				<div aria-busy={$revenue.isFetching}><RevenueChart rows={revenueRows} /></div>
			{/if}
		</Card.Content>
	</Card.Root>

	<div class="grid gap-4 xl:grid-cols-2">
		<!-- Overdue Invoices -->
		<Card.Root data-reveal>
			<Card.Header>
				<Card.Title>Overdue invoices</Card.Title>
				<Card.Description>Oldest balances requiring follow-up.</Card.Description>
				<Card.Action>
					<Button
						variant="outline"
						size="sm"
						href={`${resolve('/[...path]', { path: 'app/invoices' })}?payment_filter=overdue`}
					>View all</Button>
				</Card.Action>
			</Card.Header>
			<Card.Content>
				{#if $overdue.isPending}
					<TableSkeleton />
				{:else if $overdue.isError}
					<ErrorState onRetry={() => void $overdue.refetch()} />
				{:else if !overdueRows.length}
					<p class="py-4 text-sm text-muted-foreground">No overdue invoices.</p>
				{:else}
					<Table.Root>
						<Table.Header>
							<Table.Row>
								<Table.Head>Invoice</Table.Head>
								<Table.Head>Customer</Table.Head>
								<Table.Head>Due date</Table.Head>
								<Table.Head class="text-right">Days</Table.Head>
								<Table.Head class="text-right">Balance</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each overdueRows as invoice (invoice.invoice_id)}
								<Table.Row>
									<Table.Cell>
										<a
											href={resolve('/[...path]', { path: `app/invoices/${invoice.invoice_id}` })}
											class="font-medium underline-offset-4 hover:underline"
										>{invoice.number}</a>
									</Table.Cell>
									<Table.Cell class="max-w-[120px] truncate">{invoice.customer_name}</Table.Cell>
									<Table.Cell class="whitespace-nowrap">{formatDate(invoice.due_date)}</Table.Cell>
									<Table.Cell class="text-right tabular-nums text-destructive font-medium">{invoice.days_overdue}d</Table.Cell>
									<Table.Cell class="text-right"><MoneyCell value={invoice.balance} /></Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				{/if}
			</Card.Content>
		</Card.Root>

		<!-- Upcoming Renewals -->
		<Card.Root data-reveal>
			<Card.Header>
				<Card.Title>Upcoming renewals</Card.Title>
				<Card.Description>Subscriptions expiring within 30 days.</Card.Description>
				<Card.Action>
					<Button
						variant="outline"
						size="sm"
						href={resolve('/[...path]', { path: 'app/subscriptions' })}
					>View all</Button>
				</Card.Action>
			</Card.Header>
			<Card.Content>
				{#if $renewals.isPending}
					<TableSkeleton />
				{:else if $renewals.isError}
					<ErrorState onRetry={() => void $renewals.refetch()} />
				{:else if !renewalRows.length}
					<p class="py-4 text-sm text-muted-foreground">No subscriptions expiring within the next 30 days.</p>
				{:else}
					<Table.Root>
						<Table.Header>
							<Table.Row>
								<Table.Head>Subscription</Table.Head>
								<Table.Head>Customer</Table.Head>
								<Table.Head>Expires</Table.Head>
								<Table.Head class="text-right">Days</Table.Head>
								<Table.Head class="text-right">Status</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each renewalRows as renewal (renewal.subscription_id)}
								<Table.Row>
									<Table.Cell>
										<a
											href={resolve('/[...path]', { path: `app/subscriptions/${renewal.subscription_id}` })}
											class="font-medium underline-offset-4 hover:underline"
										>{renewal.number}</a>
									</Table.Cell>
									<Table.Cell class="max-w-[120px] truncate">{renewal.customer_name}</Table.Cell>
									<Table.Cell class="whitespace-nowrap">{formatDate(renewal.expiry_date)}</Table.Cell>
									<Table.Cell class="text-right">
										<Badge variant={renewal.days_left <= 7 ? 'destructive' : 'secondary'}>
											{renewal.days_left}d
										</Badge>
									</Table.Cell>
									<Table.Cell class="text-right">
										<Badge variant={renewal.allow_renew ? 'outline' : 'secondary'}>
											{renewal.allow_renew ? 'Eligible' : 'Manual'}
										</Badge>
									</Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				{/if}
			</Card.Content>
		</Card.Root>
	</div>
</main>
