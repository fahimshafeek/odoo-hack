<script>
	import { createQuery } from '@tanstack/svelte-query';
	import { toStore } from 'svelte/store';
	import { Play, LoaderCircle } from '@lucide/svelte';
	import { request } from '#src/api/resources.js';
	import { useListParams } from '#lib/use-list-params.js';
	import { formatDate } from '#lib/format.js';
	import { notify } from '#lib/notify.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { PageHeader, DataTable, CardSkeleton, ErrorState } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Progress } from '#lib/components/ui/progress/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import { useBillingRuns, useBillingInvalidation } from './api.js';
	const list = useListParams();
	const history = useBillingRuns(() => list.value);
	const invalidate = useBillingInvalidation();
	let activeId = $state('');
	let starting = $state(false);
	let completedId = $state('');
	const active = createQuery(
		toStore(
			() =>
				/** @type {import('@tanstack/svelte-query').CreateQueryOptions<any>} */ ({
					queryKey: ['billing', 'run-progress', activeId],
					enabled: Boolean(activeId),
					queryFn: ({ signal }) => request('GET', `/billing/runs/${activeId}`, { signal }),
					refetchInterval: (query) => (query.state.data?.status === 'running' ? 1000 : false),
					refetchIntervalInBackground: false
				})
		)
	);
	const run = $derived($active.data);
	const running = $derived(
		starting || run?.status === 'running' || Boolean(activeId && $active.isPending)
	);
	const processed = $derived(Number(run?.processed ?? 0));
	const total = $derived(Number(run?.total_due ?? 0));
	const counts = $derived({
		created: run?.created ?? run?.created_count ?? 0,
		skipped: run?.skipped ?? run?.skipped_count ?? 0,
		failed: run?.failed ?? run?.failed_count ?? 0
	});
	const columns = [
		{ key: 'run_date', header: 'Run date', cell: dateCell },
		{ key: 'status', header: 'Status', cell: statusCell },
		{ key: 'processed', header: 'Processed', cell: processedCell },
		{ key: 'created', header: 'Created', cell: createdCell },
		{ key: 'skipped', header: 'Skipped', cell: skippedCell },
		{ key: 'failed', header: 'Failed', cell: failedCell },
		{ key: 'triggered_by', header: 'Started by', cell: actorCell }
	];
	$effect(() => {
		if (!run || run.status === 'running' || run.id === completedId) return;
		completedId = run.id;
		void invalidate();
	});
	async function start() {
		if (running) return;
		starting = true;
		try {
			const result = await request('POST', '/billing/run');
			activeId = result.billing_run_id ?? result.id ?? result.run_id;
			if (!activeId)
				throw new Error(
					'The billing run could not be tracked. Refresh the run history to check its status.'
				);
			notify.success('Billing run started.');
			await $history.refetch();
		} catch (error) {
			notify.error(error);
		} finally {
			starting = false;
		}
	}
	function statusLabel(/** @type {string} */ status) {
		return status ? status[0].toUpperCase() + status.slice(1) : 'Unknown';
	}
</script>

<svelte:head><title>Billing runs · Brightloop</title></svelte:head>
{#snippet dateCell(row = /** @type {any} */ ({}))}{formatDate(
		row.run_date ?? row.started_at
	)}{/snippet}
{#snippet statusCell(row = /** @type {any} */ ({}))}<Badge
		variant={row.status === 'failed' ? 'destructive' : 'secondary'}>{statusLabel(row.status)}</Badge
	>{/snippet}
{#snippet processedCell(row = /** @type {any} */ ({}))}{row.processed ?? 0} / {row.total_due ??
		0}{/snippet}
{#snippet createdCell(row = /** @type {any} */ ({}))}{row.created ??
		row.created_count ??
		0}{/snippet}
{#snippet skippedCell(row = /** @type {any} */ ({}))}{row.skipped ??
		row.skipped_count ??
		0}{/snippet}
{#snippet failedCell(row = /** @type {any} */ ({}))}{row.failed ?? row.failed_count ?? 0}{/snippet}
{#snippet actorCell(row = /** @type {any} */ ({}))}{row.triggered_by?.name ??
		'Scheduled run'}{/snippet}
<main id="main-content" class="flex flex-col gap-4" {@attach reveal}>
	<div data-reveal>
		<PageHeader title="Billing runs" subtitle="Generate invoices for subscriptions due for billing."
			>{#snippet primaryAction()}<Button onclick={start} disabled={running} aria-busy={running}
					>{#if running}<LoaderCircle
							data-icon="inline-start"
							class="motion-safe:animate-spin"
						/>{:else}<Play data-icon="inline-start" />{/if}{starting
						? 'Starting…'
						: running
							? 'Billing in progress'
							: 'Run billing'}</Button
				>{/snippet}</PageHeader
		>
	</div>
	{#if activeId}<section aria-label="Current billing run" aria-live="polite" data-reveal>
			{#if $active.isPending}<CardSkeleton />{:else if $active.isError}<ErrorState
					message="The run may still be processing. Retry to get its latest progress."
					onRetry={() => void $active.refetch()}
				/>{:else if run}<Card.Root
					><Card.Header
						><Card.Title
							>{run.status === 'running'
								? 'Billing in progress'
								: run.status === 'failed'
									? 'Billing run failed'
									: 'Billing run complete'}</Card.Title
						><Card.Description>{processed} of {total} due subscriptions processed</Card.Description
						></Card.Header
					><Card.Content class="flex flex-col gap-4"
						><Progress
							value={processed}
							max={Math.max(total, 1)}
							aria-label="Subscriptions processed"
						/>
						<dl class="grid grid-cols-3 divide-x text-sm">
							<div class="pr-4">
								<dt class="text-xs text-muted-foreground">Created</dt>
								<dd class="mt-1 font-medium tabular-nums">{counts.created}</dd>
							</div>
							<div class="px-4">
								<dt class="text-xs text-muted-foreground">Skipped</dt>
								<dd class="mt-1 font-medium tabular-nums">{counts.skipped}</dd>
							</div>
							<div class="pl-4">
								<dt class="text-xs text-muted-foreground">Failed</dt>
								<dd class="mt-1 font-medium tabular-nums">{counts.failed}</dd>
							</div>
						</dl>
						{#if run.status !== 'running' && Number(counts.created) === 0 && Number(counts.failed) === 0}<p
								class="text-sm text-muted-foreground"
							>
								No invoices created. Already billed subscriptions were skipped.
							</p>{/if}{#if run.error}<p class="text-sm text-destructive">
								{run.error}
							</p>{/if}</Card.Content
					></Card.Root
				>{/if}
		</section>{/if}
	<div data-reveal>
		<DataTable
			{columns}
			data={$history.data}
			isLoading={$history.isPending}
			isError={$history.isError}
			onRetry={() => void $history.refetch()}
			params={list.value}
			onParamsChange={list.update}
			emptyTitle="No billing runs yet"
			emptyDescription="Run billing to generate invoices for due subscriptions."
		>
			{#snippet mobileCard(row)}<div class="flex flex-col gap-4">
					<div class="flex items-center justify-between gap-3">
						<span class="font-medium">{formatDate(row.run_date ?? row.started_at)}</span><Badge
							variant={row.status === 'failed' ? 'destructive' : 'secondary'}
							>{statusLabel(row.status)}</Badge
						>
					</div>
					<p class="text-sm text-muted-foreground">
						{row.processed ?? 0} of {row.total_due ?? 0} processed
					</p>
					<dl class="grid grid-cols-3 gap-3 text-sm">
						<div>
							<dt class="text-xs text-muted-foreground">Created</dt>
							<dd>{row.created ?? row.created_count ?? 0}</dd>
						</div>
						<div>
							<dt class="text-xs text-muted-foreground">Skipped</dt>
							<dd>{row.skipped ?? row.skipped_count ?? 0}</dd>
						</div>
						<div>
							<dt class="text-xs text-muted-foreground">Failed</dt>
							<dd>{row.failed ?? row.failed_count ?? 0}</dd>
						</div>
					</dl>
				</div>{/snippet}
		</DataTable>
	</div>
</main>
