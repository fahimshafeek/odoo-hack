<script>
	import { z } from 'zod';
	import { useQueryClient } from '@tanstack/svelte-query';
	import { auth } from '#lib/auth/session.js';
	import { createListQuery, request } from '#src/api/resources.js';
	import { useListParams } from '#lib/use-list-params.js';
	import { createForm } from '#lib/forms/form.js';
	import { dateSchema, moneySchema, percentSchema } from '#lib/validators.js';
	import { todayISO } from '#lib/navigation.js';
	import { notify } from '#lib/notify.js';
	import { reveal } from '#lib/motion/reveal.js';
	import {
		PageHeader,
		DataTable,
		FilterBar,
		SearchInput,
		Form,
		TextField,
		MoneyField,
		NumberField,
		SelectField,
		DateField,
		SwitchField,
		StatusBadge
	} from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import ConfirmDialog from '#lib/components/ConfirmDialog.svelte';
	/** @type {{kind: 'taxes' | 'discounts'}} */ let { kind } = $props();
	const discount = $derived(kind === 'discounts');
	const title = $derived(discount ? 'Discounts' : 'Taxes');
	const params = useListParams();
	const queryClient = useQueryClient();
	const list = createListQuery(
		'rules',
		() => '/' + kind,
		() => params.value
	);
	const products = createListQuery('catalog', '/products', () => ({
		page_size: 100,
		active: true
	}));
	const subscriptions = createListQuery('subscriptions', '/subscriptions', () => ({
		page_size: 100
	}));
	let open = $state(false);
	let editing = $state(/** @type {any} */ (null));
	let removal = $state(/** @type {any} */ (null));
	const optionalInt = z.union([z.literal(''), z.coerce.number().int().min(1)]);
	const form = createForm({
		schema: z
			.object({
				name: z.string().trim().min(1).max(120),
				rate_percent: percentSchema,
				type: z.enum(['fixed', 'percent']),
				value: moneySchema,
				scope: z.enum(['product', 'subscription']),
				start_date: dateSchema,
				end_date: dateSchema,
				min_purchase: z.union([z.literal(''), moneySchema]),
				min_quantity: optionalInt,
				usage_limit: optionalInt,
				target_id: z.string(),
				is_active: z.boolean()
			})
			.superRefine((v, ctx) => {
				if (kind !== 'discounts') {
					if (v.name.length > 60)
						ctx.addIssue({ code: 'custom', path: ['name'], message: 'Use up to 60 characters.' });
					return;
				}
				if (v.usage_limit !== '' && Number(v.usage_limit) < Number(editing?.used_count ?? 0))
					ctx.addIssue({
						code: 'custom',
						path: ['usage_limit'],
						message: 'The limit cannot be below the number already used.'
					});
				if (Number(v.value) <= 0)
					ctx.addIssue({
						code: 'custom',
						path: ['value'],
						message: 'Enter a value greater than zero.'
					});
				if (v.type === 'percent' && Number(v.value) > 100)
					ctx.addIssue({ code: 'custom', path: ['value'], message: 'Use a percentage up to 100.' });
				if (v.end_date < v.start_date)
					ctx.addIssue({
						code: 'custom',
						path: ['end_date'],
						message: 'End date must follow start date.'
					});
			}),
		initialValues: {
			name: '',
			rate_percent: 0,
			type: 'percent',
			value: '10.00',
			scope: 'product',
			start_date: todayISO(),
			end_date: todayISO(),
			min_purchase: '',
			min_quantity: '',
			usage_limit: '',
			target_id: '',
			is_active: true
		}
	});
	const columns = $derived([
		{ key: 'name', header: 'Name', cell: nameCell },
		{
			key: discount ? 'value' : 'rate_percent',
			header: discount ? 'Discount' : 'Rate',
			cell: valueCell
		},
		...(discount
			? [
					{ key: 'scope', header: 'Applies to' },
					{ key: 'end_date', header: 'Ends' },
					{ key: 'used_count', header: 'Uses' }
				]
			: []),
		{ key: 'is_active', header: 'Status', cell: statusCell },
		{ key: 'actions', header: 'Actions', cell: actionsCell }
	]);
	const page = $derived(
		Array.isArray($list.data)
			? { items: $list.data, total: $list.data.length, page: 1, page_size: 100 }
			: $list.data
	);
	const targets = $derived(
		($form.values.scope === 'product'
			? ($products.data?.items ?? [])
			: ($subscriptions.data?.items ?? [])
		).map((/** @type {any} */ row) => ({ value: row.id, label: row.name ?? row.number }))
	);
	function edit(/** @type {any} */ row = null) {
		editing = row;
		form.reset({
			name: row?.name ?? '',
			rate_percent: row?.rate_percent ?? 0,
			type: row?.type ?? 'percent',
			value: row?.value ?? '10.00',
			scope: row?.scope ?? 'product',
			start_date: row?.start_date ?? todayISO(),
			end_date: row?.end_date ?? todayISO(),
			min_purchase: row?.min_purchase ?? '',
			min_quantity: row?.min_quantity ?? '',
			usage_limit: row?.usage_limit ?? '',
			target_id: row?.targets?.[0]?.product_id ?? row?.targets?.[0]?.subscription_id ?? '',
			is_active: row?.is_active ?? true
		});
		open = true;
	}
	function locked(/** @type {string} */ field) {
		return Boolean(editing?.used_count > 0 && !editing?.editable_fields?.includes(field));
	}
	async function save(/** @type {any} */ values) {
		const body = discount
			? {
					...values,
					min_purchase: values.min_purchase || null,
					min_quantity: values.min_quantity || null,
					usage_limit: values.usage_limit || null,
					targets: values.target_id
						? [
								{
									[values.scope === 'product' ? 'product_id' : 'subscription_id']: values.target_id
								}
							]
						: []
				}
			: {
					name: values.name,
					rate_percent: String(values.rate_percent),
					is_active: values.is_active
				};
		if (
			discount &&
			editing &&
			values.scope === editing.scope &&
			values.target_id ===
				(editing.targets?.[0]?.product_id ?? editing.targets?.[0]?.subscription_id ?? '')
		)
			body.targets = (editing.targets ?? []).map((/** @type {any} */ target) =>
				target.product_id
					? { product_id: target.product_id }
					: { subscription_id: target.subscription_id }
			);
		delete body.target_id;
		delete body.rate_percent;
		if (!discount) body.rate_percent = String(values.rate_percent);
		if (editing?.used_count > 0)
			for (const key of Object.keys(body))
				if (!editing.editable_fields?.includes(key)) delete body[key];
		await request(editing ? 'PATCH' : 'POST', '/' + kind + (editing ? '/' + editing.id : ''), {
			body
		});
		await listRefetch();
		open = false;
		notify.success(discount ? 'Discount saved.' : 'Tax saved.');
	}
	async function listRefetch() {
		await Promise.all([$list.refetch(), queryClient.invalidateQueries({ queryKey: ['catalog'] })]);
	}
</script>

<svelte:head><title>{title} ? Brightloop</title></svelte:head>
{#snippet nameCell(row = /** @type {any} */ ({}))}<span class="font-medium">{row.name}</span
	>{/snippet}
{#snippet valueCell(row = /** @type {any} */ ({}))}{discount
		? row.type === 'percent'
			? row.value + '%'
			: '?' + row.value
		: row.rate_percent + '%'}{/snippet}
{#snippet statusCell(row = /** @type {any} */ ({}))}<StatusBadge
		kind="active_flag"
		value={row.is_active}
	/>{/snippet}
{#snippet actionsCell(row = /** @type {any} */ ({}))}{#if $auth.user?.role === 'admin'}<div
			class="flex gap-2"
		>
			<Button variant="ghost" size="sm" onclick={() => edit(row)}>Edit</Button><Button
				variant="ghost"
				size="sm"
				onclick={() => (removal = row)}>Deactivate</Button
			>
		</div>{:else}<span class="text-xs text-muted-foreground">View only</span>{/if}{/snippet}
<main id="main-content" class="flex flex-col gap-4" {@attach reveal}>
	<div data-reveal>
		<PageHeader
			{title}
			subtitle={discount
				? 'Manage discount eligibility and validity.'
				: 'Manage tax rates used on product and plan lines.'}
			>{#snippet primaryAction()}{#if $auth.user?.role === 'admin'}<Button onclick={() => edit()}
						>Add {discount ? 'discount' : 'tax'}</Button
					>{/if}{/snippet}</PageHeader
		>
	</div>
	<div data-reveal>
		<DataTable
			{columns}
			data={page}
			isLoading={$list.isPending}
			isError={$list.isError}
			onRetry={listRefetch}
			params={params.value}
			onParamsChange={params.update}
			>{#snippet toolbar()}<FilterBar params={params.value} onChange={params.update}
					><SearchInput
						value={params.value.q}
						onChange={(q) => params.update({ q })}
						placeholder={discount ? 'Search discounts?' : 'Search taxes?'}
					/></FilterBar
				>{/snippet}</DataTable
		>
	</div>
</main>
<Dialog.Root bind:open
	><Dialog.Content class="max-h-[90svh] overflow-y-auto"
		><Dialog.Header
			><Dialog.Title>{editing ? 'Edit' : 'Add'} {discount ? 'discount' : 'tax'}</Dialog.Title
			><Dialog.Description
				>{discount
					? 'Discounts apply when invoices are generated.'
					: 'Tax changes apply to new or edited lines.'}</Dialog.Description
			></Dialog.Header
		><Form {form} onSubmit={save}
			><TextField name="name" label="Name" required />{#if discount}<SelectField
					name="type"
					label="Discount type"
					options={[
						{ value: 'percent', label: 'Percentage' },
						{ value: 'fixed', label: 'Fixed amount' }
					]}
					disabled={locked('type')}
				/><MoneyField
					name="value"
					label={$form.values.type === 'percent' ? 'Percentage' : 'Amount'}
					required
					disabled={locked('value')}
				/><SelectField
					name="scope"
					label="Scope"
					options={[
						{ value: 'product', label: 'Product lines' },
						{ value: 'subscription', label: 'Subscription' }
					]}
					disabled={locked('scope')}
				/><SelectField
					name="target_id"
					label="Target"
					hint="Leave empty to apply to all eligible records."
					options={targets}
					disabled={locked('targets')}
				/><MoneyField
					name="min_purchase"
					label="Minimum purchase"
					disabled={locked('min_purchase')}
				/><NumberField
					name="min_quantity"
					label="Minimum quantity"
					min={1}
					disabled={locked('min_quantity')}
				/><DateField
					name="start_date"
					label="Starts"
					disabled={locked('start_date')}
					required
				/><DateField
					name="end_date"
					label="Ends"
					min={$form.values.start_date}
					required
				/><NumberField
					name="usage_limit"
					label="Usage limit"
					hint="Leave empty for unlimited use."
					min={Math.max(1, editing?.used_count ?? 1)}
				/>{:else}<NumberField
					name="rate_percent"
					label="Rate (%)"
					min={0}
					max={100}
					step="0.01"
					required
				/>{/if}<SwitchField name="is_active" label="Active" /><Dialog.Footer
				><Button variant="outline" onclick={() => (open = false)} disabled={$form.isSubmitting}
					>Cancel</Button
				><Button type="submit" disabled={!$form.isValid || $form.isSubmitting}
					>{$form.isSubmitting ? 'Saving?' : 'Save'}</Button
				></Dialog.Footer
			></Form
		></Dialog.Content
	></Dialog.Root
>
<ConfirmDialog
	open={Boolean(removal)}
	onOpenChange={(value) => {
		if (!value) removal = null;
	}}
	title="Deactivate rule?"
	description="Existing invoice and subscription snapshots are preserved."
	confirmLabel="Deactivate"
	destructive
	onConfirm={async () => {
		await request('DELETE', '/' + kind + '/' + removal.id);
		await listRefetch();
		notify.success('Rule deactivated.');
	}}
/>
