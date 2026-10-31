<script>
	import { untrack } from 'svelte';
	import { Plus } from '@lucide/svelte';
	import { createForm } from '#lib/forms/form.js';
	import { createActionMutation } from '#src/api/resources.js';
	import { notify } from '#lib/notify.js';
	import {
		Form,
		TextField,
		TextAreaField,
		MoneyField,
		NumberField,
		DateField,
		SelectField,
		SwitchField,
		ErrorState,
		EmptyState,
		TableSkeleton
	} from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Field from '#lib/components/ui/field/index.js';
	import { schemaFor, initialValues, writeBody } from './forms.js';
	import { picker } from './api.js';
	import ProductAttributes from './ProductAttributes.svelte';
	import TemplateLine from './TemplateLine.svelte';
	/** @type {{kind:string,record?:any,readonly?:boolean,onSaved:(record:any)=>void}} */
	let { kind, record, readonly = false, onSaved } = $props();
	const form = createForm({
		schema: untrack(() => schemaFor(kind)),
		initialValues: untrack(() => initialValues(kind, record))
	});
	const taxes = picker('/taxes', () => kind !== 'payment-terms');
	const plans = picker('/plans', () => kind === 'quotation-templates');
	const products = picker('/products', () => kind === 'quotation-templates');
	const rawTaxes = $derived(Array.isArray($taxes.data) ? $taxes.data : ($taxes.data?.items ?? []));
	const taxOptions = $derived(
		[
			...rawTaxes,
			...(record?.tax &&
			!rawTaxes.some((/** @type {any} */ item) => item.id === record.tax.id)
				? [record.tax]
				: [])
		].map((/** @type {any} */ item) => ({
			value: item.id,
			label: item.name
		}))
	);
	const planOptions = $derived(
		[
			...($plans.data?.items ?? []),
			...(record?.plan &&
			!($plans.data?.items ?? []).some((/** @type {any} */ item) => item.id === record.plan.id)
				? [record.plan]
				: [])
		].map((/** @type {any} */ item) => ({
			value: item.id,
			label: item.name
		}))
	);
	const periods = ['daily', 'weekly', 'monthly', 'yearly'].map((value) => ({
		value,
		label: value[0].toUpperCase() + value.slice(1)
	}));
	const mutation = createActionMutation(
		'catalog',
		untrack(() => (record ? 'PATCH' : 'POST')),
		() => (record ? `/${kind}/${record.id}` : `/${kind}`),
		(data) => {
			notify.success(record ? 'Changes saved.' : 'Record created.');
			onSaved(data);
		}
	);
	async function submit(/** @type {any} */ values) {
		if (readonly) return;
		await $mutation.mutateAsync({ body: writeBody(kind, values, Boolean(record)) });
	}
	function addLine() {
		form.setValue('lines', [
			...$form.values.lines,
			{
				_key: crypto.randomUUID(),
				_product_name: '',
				_tax_name: '',
				product_id: '',
				quantity: 1,
				variant_value_ids: [],
				tax_id: null
			}
		]);
	}
	function removeLine(/** @type {number} */ index) {
		form.setValue(
			'lines',
			$form.values.lines.filter((/** @type {any} */ _, /** @type {number} */ i) => i !== index)
		);
	}
</script>

<Form {form} onSubmit={submit}>
	<Field.FieldGroup class="grid gap-4 sm:grid-cols-2">
		<div class="sm:col-span-2">
			<TextField
				name="name"
				label="Name"
				disabled={readonly}
				required
				maxlength={kind === 'payment-terms' ? 60 : 120}
			/>
		</div>
		{#if kind === 'products'}
			<TextField
				name="type"
				label="Type"
				hint="For example: physical, service, or digital."
				disabled={readonly}
				required
				maxlength={40}
			/><SelectField
				name="tax_id"
				label="Default tax"
				placeholder="No tax"
				options={taxOptions}
				disabled={readonly || $taxes.isPending}
			/>
			<MoneyField name="sales_price" label="Sales price" disabled={readonly} required /><MoneyField
				name="cost_price"
				label="Cost price"
				disabled={readonly}
				required
			/>
			<div class="sm:col-span-2">
				<TextAreaField name="notes" label="Notes" disabled={readonly} maxlength={2000} />
			</div>
		{:else if kind === 'plans'}
			<MoneyField name="price" label="Price per period" disabled={readonly} required /><SelectField
				name="billing_period"
				label="Billing period"
				options={periods}
				disabled={readonly}
				required
			/>
			<NumberField
				name="min_quantity"
				label="Minimum product quantity"
				min={1}
				disabled={readonly}
				required
			/><SelectField
				name="tax_id"
				label="Plan fee tax"
				placeholder="No tax"
				options={taxOptions}
				disabled={readonly || $taxes.isPending}
			/>
			<DateField
				name="valid_from"
				label="Available from"
				max={$form.values.valid_to || undefined}
				disabled={readonly}
			/><DateField
				name="valid_to"
				label="Available until"
				min={$form.values.valid_from || undefined}
				disabled={readonly}
			/>
			<div class="sm:col-span-2">
				<Field.FieldSet
					><Field.FieldLegend>Subscription rules</Field.FieldLegend><Field.FieldGroup
						class="grid gap-4 sm:grid-cols-2"
						><SwitchField
							name="auto_close"
							label="Auto-close at expiry"
							disabled={readonly}
						/><SwitchField
							name="allow_early_close"
							label="Allow early closing"
							disabled={readonly}
						/><SwitchField
							name="allow_pause"
							label="Allow pausing"
							disabled={readonly}
						/><SwitchField
							name="allow_renew"
							label="Allow renewal"
							disabled={readonly}
						/></Field.FieldGroup
					></Field.FieldSet
				>
			</div>
		{:else if kind === 'payment-terms'}<NumberField
				name="due_days"
				label="Due after (days)"
				hint="0 means payment is due immediately."
				min={0}
				max={365}
				disabled={readonly}
				required
			/>
		{:else}
			<SelectField
				name="plan_id"
				label="Recurring plan"
				options={planOptions}
				disabled={readonly || $plans.isPending}
				required
			/><NumberField
				name="validity_days"
				label="Quote validity (days)"
				min={1}
				max={365}
				disabled={readonly}
				required
			/>
		{/if}
		{#if record || kind === 'products' || kind === 'plans'}<SwitchField
				name="is_active"
				label="Active"
				disabled={readonly}
			/>{/if}
	</Field.FieldGroup>
	{#if kind !== 'payment-terms' && $taxes.isError}<ErrorState
			message="Taxes could not be loaded."
			onRetry={() => $taxes.refetch()}
		/>{/if}
	{#if kind === 'quotation-templates'}
		<div class="flex items-center justify-between gap-3 border-t pt-4">
			<h3 class="text-sm font-medium">Product lines</h3>
			{#if !readonly}<Button variant="outline" onclick={addLine} disabled={$form.isSubmitting}
					><Plus data-icon="inline-start" />Add line</Button
				>{/if}
		</div>
		{#if $plans.isError || $products.isError}<ErrorState
				message="Plans or products could not be loaded."
				onRetry={() => {
					void $plans.refetch();
					void $products.refetch();
				}}
			/>{:else if $products.isPending}<TableSkeleton />{:else}
			{#each $form.values.lines as line, index (line._key)}<TemplateLine
					{form}
					{index}
					products={$products.data?.items ?? []}
					taxes={rawTaxes}
					disabled={readonly}
					onRemove={() => removeLine(index)}
				/>{:else}<EmptyState
					title="No product lines"
					description="Add products to include them in subscriptions created from this template."
				/>{/each}
		{/if}
	{/if}
	{#if !readonly}<div class="flex justify-end border-t pt-4">
			<Button type="submit" disabled={!$form.isValid || $form.isSubmitting}
				>{$form.isSubmitting ? 'Saving…' : record ? 'Save changes' : 'Create'}</Button
			>
		</div>{/if}
</Form>
{#if kind === 'products'}{#if record}<ProductAttributes product={record} {readonly} />{:else}<p
			class="text-xs text-muted-foreground"
		>
			Save this product to add variant attributes.
		</p>{/if}{/if}
