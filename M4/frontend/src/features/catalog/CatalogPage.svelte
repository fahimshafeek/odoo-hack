<script>
	import { Plus } from '@lucide/svelte';
	import { auth } from '#lib/auth/session.js';
	import { createActionMutation, createDetailQuery, createListQuery } from '#src/api/resources.js';
	import { useListParams } from '#lib/use-list-params.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { formatDate } from '#lib/format.js';
	import { notify } from '#lib/notify.js';
	import {
		PageHeader,
		DataTable,
		FilterBar,
		SearchInput,
		MoneyCell,
		ErrorState,
		CardSkeleton,
		ConfirmDialog
	} from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import * as NativeSelect from '#lib/components/ui/native-select/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import CatalogEditor from './CatalogEditor.svelte';
	import { catalog } from './forms.js';
	/** @type {{kind?: string}} */
	let { kind = 'products' } = $props();
	const config = $derived(/** @type {Record<string,any>} */ (catalog)[kind]);
	const admin = $derived($auth.user?.role === 'admin');
	const params = useListParams({ sort: 'name' });
	const list = createListQuery(
		'catalog',
		() => `/${kind}`,
		() => params.value
	);
	let open = $state(false);
	let selected = $state('');
	let removing = $state(false);
	let closing = $state(false);
	const detail = createDetailQuery(
		'catalog',
		() => `/${kind}/${selected}`,
		() => open && Boolean(selected)
	);
	const remove = createActionMutation(
		'catalog',
		'DELETE',
		() => `/${kind}/${selected}`,
		() => {
			open = false;
			notify.success('Record removed or deactivated.');
		}
	);
	const closePlan = createActionMutation(
		'catalog',
		'POST',
		() => `/plans/${selected}/close`,
		() => {
			open = false;
			notify.success('Plan closed.');
		}
	);
	const columns = $derived.by(() => {
		/** @type {{key:string,header:string,sortKey?:string,cell?:import('svelte').Snippet<[any]>}[]} */
		const base = [
			{ key: 'name', header: 'Name', sortKey: 'name' },
			{ key: 'is_active', header: 'Status', cell: activeCell }
		];
		if (kind === 'products')
			base.splice(
				1,
				0,
				{ key: 'type', header: 'Type', cell: typeCell },
				{ key: 'sales_price', header: 'Sales price', cell: salesCell },
				{ key: 'cost_price', header: 'Cost price', cell: costCell },
				{ key: 'tax', header: 'Tax', cell: taxCell }
			);
		if (kind === 'plans')
			base.splice(
				1,
				0,
				{ key: 'price', header: 'Price / period', cell: priceCell },
				{ key: 'billing_period', header: 'Billing period', cell: periodCell },
				{ key: 'min_quantity', header: 'Min. quantity' },
				{ key: 'availability', header: 'Availability', cell: datesCell }
			);
		if (kind === 'payment-terms')
			base.splice(1, 0, { key: 'due_days', header: 'Payment due', cell: dueCell });
		if (kind === 'quotation-templates')
			base.splice(
				1,
				0,
				{ key: 'plan', header: 'Plan', cell: planCell },
				{ key: 'validity_days', header: 'Quote validity', cell: validityCell },
				{ key: 'lines_count', header: 'Product lines' }
			);
		return base;
	});
	function edit(/** @type {any} */ record) {
		selected = record.id;
		open = true;
	}
	function saved(/** @type {any} */ record) {
		if (kind === 'products' && !selected && record?.id) {
			selected = record.id;
		} else open = false;
	}
</script>

<svelte:head><title>{config.title} · Brightloop</title></svelte:head>
{#snippet activeCell(row = /** @type {any} */ ({}))}<Badge
		variant={row.is_active ? 'active' : 'draft'}>{row.is_active ? 'Active' : 'Inactive'}</Badge
	>{/snippet}
{#snippet typeCell(row = /** @type {any} */ ({}))}<span class="capitalize">{row.type}</span
	>{/snippet}
{#snippet salesCell(row = /** @type {any} */ ({}))}<MoneyCell value={row.sales_price} />{/snippet}
{#snippet costCell(row = /** @type {any} */ ({}))}<MoneyCell value={row.cost_price} />{/snippet}
{#snippet taxCell(row = /** @type {any} */ ({}))}{row.tax?.name ?? 'No tax'}{/snippet}
{#snippet priceCell(row = /** @type {any} */ ({}))}<MoneyCell value={row.price} />{/snippet}
{#snippet periodCell(row = /** @type {any} */ ({}))}<span class="capitalize"
		>{row.billing_period}</span
	>{/snippet}
{#snippet datesCell(row = /** @type {any} */ ({}))}{row.valid_from || row.valid_to
		? `${formatDate(row.valid_from)} – ${formatDate(row.valid_to)}`
		: 'No date restrictions'}{/snippet}
{#snippet dueCell(row = /** @type {any} */ ({}))}{row.due_days === 0
		? 'Immediate'
		: `${row.due_days} days`}{/snippet}
{#snippet planCell(row = /** @type {any} */ ({}))}{row.plan?.name}{/snippet}
{#snippet validityCell(row = /** @type {any} */ ({}))}{row.validity_days} days{/snippet}

<main id="main-content" class="min-w-0" {@attach reveal}>
	<div data-reveal>
		<PageHeader title={config.title} subtitle={config.description}
			>{#snippet primaryAction()}{#if admin}<Button
						onclick={() => {
							selected = '';
							open = true;
						}}><Plus data-icon="inline-start" />New {config.singular}</Button
					>{/if}{/snippet}</PageHeader
		>
	</div>
	<div data-reveal class="mb-4">
		<FilterBar
			><SearchInput
				value={params.value.q}
				placeholder={`Search ${config.title.toLowerCase()}…`}
				onChange={(q) => params.update({ q })}
			/><NativeSelect.Root
				aria-label="Filter by active status"
				value={String(params.value.active ?? '')}
				onchange={(/** @type {Event} */ event) =>
					params.update({ active: /** @type {HTMLSelectElement} */ (event.currentTarget).value })}
				><NativeSelect.Option value="">All statuses</NativeSelect.Option><NativeSelect.Option
					value="true">Active</NativeSelect.Option
				><NativeSelect.Option value="false">Inactive</NativeSelect.Option></NativeSelect.Root
			>{#if kind === 'products'}<NativeSelect.Root
					aria-label="Filter by product type"
					value={String(params.value.type ?? '')}
					onchange={(/** @type {Event} */ event) =>
						params.update({ type: /** @type {HTMLSelectElement} */ (event.currentTarget).value })}
					><NativeSelect.Option value="">All types</NativeSelect.Option><NativeSelect.Option
						value="physical">Physical</NativeSelect.Option
					><NativeSelect.Option value="service">Service</NativeSelect.Option><NativeSelect.Option
						value="digital">Digital</NativeSelect.Option
					></NativeSelect.Root
				>{/if}</FilterBar
		>
	</div>
	<DataTable
		{columns}
		data={$list.data}
		isLoading={$list.isPending}
		isError={$list.isError}
		onRetry={() => $list.refetch()}
		params={params.value}
		onParamsChange={params.update}
		onRowClick={edit}
		emptyTitle={`No ${config.title.toLowerCase()} found`}
		emptyDescription={admin
			? `Use New ${config.singular} to add one.`
			: 'Change your search or filters.'}
		>{#snippet mobileCard(row)}<div class="flex items-center justify-between gap-3">
				<span class="font-medium">{row.name}</span>{@render activeCell(row)}
			</div>
			<div class="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
				{#if kind === 'products'}<span class="capitalize">{row.type}</span><MoneyCell
						value={row.sales_price}
					/>{:else if kind === 'plans'}<MoneyCell value={row.price} /><span
						>{row.billing_period}</span
					>{:else if kind === 'payment-terms'}{@render dueCell(row)}{:else}<span
						>{row.plan?.name}</span
					>{@render validityCell(row)}{/if}
			</div>{/snippet}</DataTable
	>
</main>
<Dialog.Root bind:open
	><Dialog.Content class="max-h-[88svh] overflow-y-auto sm:max-w-3xl"
		><Dialog.Header
			><Dialog.Title>{selected ? (admin ? 'Edit' : 'View') : 'New'} {config.singular}</Dialog.Title
			><Dialog.Description
				>{admin
					? 'Update the details below.'
					: 'Catalog details are read-only for staff.'}</Dialog.Description
			></Dialog.Header
		>
		{#if selected && $detail.isPending}<CardSkeleton
			/>{:else if selected && $detail.isError}<ErrorState
				onRetry={() => $detail.refetch()}
			/>{:else}{#key `${kind}:${selected}`}<CatalogEditor
					{kind}
					record={selected ? $detail.data : undefined}
					readonly={!admin}
					onSaved={saved}
				/>{/key}{/if}
		{#if admin && selected && $detail.isSuccess}<div
				class="flex justify-between gap-3 border-t pt-4"
			>
				<Button variant="destructive" onclick={() => (removing = true)}
					>Delete {config.singular}</Button
				>{#if kind === 'plans' && $detail.data.is_active}<Button
						variant="outline"
						onclick={() => (closing = true)}>Close plan</Button
					>{/if}
			</div>{/if}
	</Dialog.Content></Dialog.Root
>
<ConfirmDialog
	open={removing}
	onOpenChange={(value) => (removing = value)}
	title={`Delete ${config.singular}?`}
	description="Referenced records will be deactivated instead of deleted."
	confirmLabel="Delete"
	destructive
	onConfirm={() => $remove.mutateAsync({})}
/>
<ConfirmDialog
	open={closing}
	onOpenChange={(value) => (closing = value)}
	title="Close plan?"
	description="This prevents new subscriptions from using the plan. Existing subscriptions are retained."
	confirmLabel="Close plan"
	onConfirm={() => $closePlan.mutateAsync({})}
/>
