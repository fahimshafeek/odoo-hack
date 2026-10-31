<script>
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { z } from 'zod';
	import { Plus, Files, ArrowUpRight, CalendarDays, Users, X } from '@lucide/svelte';
	import { createActionMutation } from '#src/api/resources.js';
	import { useListParams } from '#lib/use-list-params.js';
	import { createForm } from '#lib/forms/form.js';
	import { uuidSchema, dateSchema } from '#lib/validators.js';
	import { todayISO } from '#lib/navigation.js';
	import { formatDate } from '#lib/format.js';
	import { notify } from '#lib/notify.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { subscriptionsQuery, pickerQuery, customerOptions } from './api.js';
	import StatusStepper from './StatusStepper.svelte';
	import {
		PageHeader,
		DataTable,
		StatusBadge,
		MoneyCell,
		FilterBar,
		SearchInput,
		Form,
		SelectField,
		ComboboxField,
		DateField,
		ErrorState,
		EmptyState,
		TableSkeleton
	} from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as NativeSelect from '#lib/components/ui/native-select/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	/** @type {{portal?: boolean}} */
	let { portal = false } = $props();
	const params = useListParams();
	const list = subscriptionsQuery(
		() => portal,
		() => params.value
	);
	const plans = pickerQuery('/plans', () => !portal);
	const templates = pickerQuery('/quotation-templates', () => !portal);
	let templateOpen = $state(false);
	let customerOpen = $state(false);
	const templateForm = createForm({
		schema: z.object({ template_id: uuidSchema, customer_id: uuidSchema, start_date: dateSchema }),
		initialValues: { template_id: '', customer_id: '', start_date: todayISO() }
	});
	const customerForm = createForm({
		schema: z.object({ customer_id: uuidSchema }),
		initialValues: { customer_id: '' }
	});
	const fromTemplate = createActionMutation(
		'subscriptions',
		'POST',
		(variables) => `/subscriptions/from-template/${variables.id}`,
		async (data) => {
			templateOpen = false;
			notify.success('Draft created.');
			await goto(resolve('/[...path]', { path: `app/subscriptions/${data.id}` }));
		}
	);
	const columns = $derived([
		{ key: 'number', header: 'Subscription', sortKey: 'number', cell: numberCell },
		{ key: 'customer', header: 'Customer', cell: customerCell },
		{ key: 'plan', header: 'Plan', cell: planCell },
		{ key: 'status', header: 'Status', sortKey: 'status', cell: statusCell },
		{
			key: 'start_date',
			header: 'Start date',
			sortKey: 'start_date',
			cell: startCell,
			hideOnMobile: true
		},
		{ key: 'expiry_date', header: 'Expiry date', cell: expiryCell, hideOnMobile: true },
		{ key: 'next_billing_date', header: 'Next billing', cell: nextCell },
		{ key: 'estimated_total', header: 'Estimated / period', cell: totalCell }
	]);
	function openRecord(/** @type {any} */ row) {
		void goto(
			resolve('/[...path]', { path: `${portal ? 'portal' : 'app'}/subscriptions/${row.id}` })
		);
	}
	const planOptions = $derived(
		($plans.data?.items ?? []).map((/** @type {any} */ item) => ({
			value: item.id,
			label: item.name
		}))
	);
	const templateOptions = $derived(
		($templates.data?.items ?? []).map((/** @type {any} */ item) => ({
			value: item.id,
			label: item.name
		}))
	);
</script>

<svelte:head
	><title>{portal ? 'My subscriptions' : 'Subscriptions'} · Brightloop</title></svelte:head
>

{#snippet numberCell(row = /** @type {any} */ ({}))}<span class="font-medium">{row.number}</span
	>{/snippet}
{#snippet customerCell(row = /** @type {any} */ ({}))}<span>{row.customer?.name}</span>{/snippet}
{#snippet planCell(row = /** @type {any} */ ({}))}<span>{row.plan?.name}</span>{/snippet}
{#snippet statusCell(row = /** @type {any} */ ({}))}<StatusBadge
		kind="subscription"
		value={row.status}
	/>{/snippet}
{#snippet startCell(row = /** @type {any} */ ({}))}{formatDate(row.start_date)}{/snippet}
{#snippet expiryCell(row = /** @type {any} */ ({}))}{formatDate(row.expiry_date)}{/snippet}
{#snippet nextCell(row = /** @type {any} */ ({}))}{formatDate(row.next_billing_date)}{/snippet}
{#snippet totalCell(row = /** @type {any} */ ({}))}<MoneyCell
		value={row.estimated_total}
	/>{/snippet}

<main id="main-content" class="min-w-0" {@attach reveal}>
	<div data-reveal>
		<PageHeader
			title={portal ? 'My subscriptions' : 'Subscriptions'}
			subtitle={portal
				? 'View your plans and billing dates.'
				: 'Manage plans, billing dates, and subscription status.'}
		>
			{#snippet primaryAction()}{#if !portal}<Button
						href={resolve('/[...path]', { path: 'app/subscriptions/new' })}
						><Plus data-icon="inline-start" />New subscription</Button
					>{/if}{/snippet}
			{#snippet actions()}{#if !portal}<Button
						variant="outline"
						onclick={() => (templateOpen = true)}
						><Files data-icon="inline-start" />From template</Button
					>{/if}{/snippet}
		</PageHeader>
	</div>
	<div data-reveal class="mb-4">
		<FilterBar>
			<SearchInput
				value={params.value.q}
				placeholder="Search subscriptions…"
				onChange={(q) => params.update({ q })}
			/>
			<NativeSelect.Root
				aria-label="Filter by status"
				value={String(params.value.status ?? '')}
				onchange={(/** @type {Event} */ event) =>
					params.update({ status: /** @type {HTMLSelectElement} */ (event.currentTarget).value })}
				><NativeSelect.Option value="">All statuses</NativeSelect.Option
				>{#each ['draft', 'quotation', 'confirmed', 'active', 'paused', 'closed'].filter((status) => !portal || status !== 'draft') as status (status)}<NativeSelect.Option
						value={status}>{status[0].toUpperCase() + status.slice(1)}</NativeSelect.Option
					>{/each}</NativeSelect.Root
			>
			{#if !portal}<NativeSelect.Root
					aria-label="Filter by plan"
					value={String(params.value.plan_id ?? '')}
					onchange={(/** @type {Event} */ event) =>
						params.update({
							plan_id: /** @type {HTMLSelectElement} */ (event.currentTarget).value
						})}
					><NativeSelect.Option value="">All plans</NativeSelect.Option
					>{#each planOptions as option (option.value)}<NativeSelect.Option value={option.value}
							>{option.label}</NativeSelect.Option
						>{/each}</NativeSelect.Root
				>
				<Button
					variant="outline"
					onclick={() => {
						customerForm.reset({ customer_id: String(params.value.customer_id ?? '') });
						customerOpen = true;
					}}
					><Users data-icon="inline-start" />{params.value.customer_id
						? 'Customer selected'
						: 'Customer'}</Button
				>{#if params.value.customer_id}<Button
						variant="ghost"
						aria-label="Clear customer filter"
						size="icon"
						onclick={() => params.update({ customer_id: '' })}><X /></Button
					>{/if}
			{/if}
		</FilterBar>
	</div>
	{#if portal}
		{#if $list.isPending}<TableSkeleton />{:else if $list.isError}<ErrorState
				onRetry={() => $list.refetch()}
			/>{:else if !$list.data?.items?.length}<EmptyState
				title="No subscriptions yet"
				description="Subscriptions will appear here once created."
			/>{:else}
			<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
				{#each $list.data.items as subscription (subscription.id)}<Card.Root
						><Card.Header
							><Card.Description>{subscription.number}</Card.Description><Card.Title
								>{subscription.plan.name}</Card.Title
							><Card.Action
								><StatusBadge kind="subscription" value={subscription.status} /></Card.Action
							></Card.Header
						><Card.Content
							><div class="mb-5"><StatusStepper status={subscription.status} compact /></div>
							<dl class="grid grid-cols-2 gap-3 text-sm">
								<dt class="text-muted-foreground">Next billing</dt>
								<dd class="text-right">{formatDate(subscription.next_billing_date)}</dd>
								<dt class="text-muted-foreground">Estimated / period</dt>
								<dd><MoneyCell value={subscription.estimated_total} /></dd>
								<dt class="text-muted-foreground">Renews or ends</dt>
								<dd class="text-right">{formatDate(subscription.expiry_date)}</dd>
							</dl></Card.Content
						><Card.Footer
							><Button variant="outline" class="w-full" onclick={() => openRecord(subscription)}
								>View subscription<ArrowUpRight data-icon="inline-end" /></Button
							></Card.Footer
						></Card.Root
					>{/each}
			</div>
			<div class="mt-6 flex items-center justify-between text-xs text-muted-foreground">
				<span>{$list.data.total} subscriptions</span>
				<div class="flex gap-2">
					<Button
						variant="outline"
						disabled={params.value.page <= 1}
						onclick={() => params.update({ page: params.value.page - 1 })}>Previous</Button
					><Button
						variant="outline"
						disabled={params.value.page * params.value.page_size >= $list.data.total}
						onclick={() => params.update({ page: params.value.page + 1 })}>Next</Button
					>
				</div>
			</div>
		{/if}
	{:else}<DataTable
			{columns}
			data={$list.data}
			isLoading={$list.isPending}
			isError={$list.isError}
			onRetry={() => $list.refetch()}
			params={params.value}
			onParamsChange={params.update}
			onRowClick={openRecord}
			emptyTitle="No subscriptions"
			emptyDescription="Create a subscription or use a quotation template."
		>
			{#snippet mobileCard(row)}<div class="flex items-start justify-between gap-3">
					<div>
						<p class="font-medium">{row.number}</p>
						<p class="mt-1 text-sm text-muted-foreground">{row.customer?.name}</p>
					</div>
					<StatusBadge kind="subscription" value={row.status} />
				</div>
				<div class="mt-4 flex items-center justify-between text-sm">
					<span>{row.plan?.name}</span><MoneyCell value={row.estimated_total} />
				</div>
				<p class="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
					<CalendarDays class="size-3" />Next billing {formatDate(row.next_billing_date)}
				</p>{/snippet}
		</DataTable>{/if}
</main>

<Dialog.Root bind:open={templateOpen}
	><Dialog.Content
		><Dialog.Header
			><Dialog.Title>Create from template</Dialog.Title><Dialog.Description
				>Select a template, customer, and start date.</Dialog.Description
			></Dialog.Header
		>{#if $templates.isPending}<TableSkeleton />{:else if $templates.isError}<ErrorState
				message="We could not load quotation templates."
				onRetry={() => $templates.refetch()}
			/>{:else if !templateOptions.length}<EmptyState
				title="No active templates yet"
				description="Create a subscription using the New subscription button."
			/>{:else}<Form
				form={templateForm}
				onSubmit={(values) =>
					$fromTemplate.mutateAsync({
						id: values.template_id,
						body: { customer_id: values.customer_id, start_date: values.start_date }
					})}
				><SelectField
					name="template_id"
					label="Quotation template"
					options={templateOptions}
					required
				/><ComboboxField
					name="customer_id"
					label="Customer"
					loadOptions={customerOptions}
					required
				/><DateField name="start_date" label="Start date" required /><Button
					type="submit"
					disabled={!$templateForm.isValid || $templateForm.isSubmitting}
					>Create draft<Plus data-icon="inline-end" /></Button
				></Form
			>{/if}
		></Dialog.Content
	></Dialog.Root
>
<Dialog.Root bind:open={customerOpen}
	><Dialog.Content
		><Dialog.Header
			><Dialog.Title>Filter by customer</Dialog.Title><Dialog.Description
				>Select a customer.</Dialog.Description
			></Dialog.Header
		><Form
			form={customerForm}
			onSubmit={async (values) => {
				await params.update({ customer_id: values.customer_id });
				customerOpen = false;
			}}
			><ComboboxField
				name="customer_id"
				label="Customer"
				loadOptions={customerOptions}
				required
			/><Button type="submit" disabled={!$customerForm.isValid}>Apply filter</Button></Form
		></Dialog.Content
	></Dialog.Root
>
