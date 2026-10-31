<script>
	import { Trash2 } from '@lucide/svelte';
	import { createDetailQuery } from '#src/api/resources.js';
	import { NumberField, SelectField, ErrorState } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Field from '#lib/components/ui/field/index.js';
	import * as NativeSelect from '#lib/components/ui/native-select/index.js';
	/** @type {{form:ReturnType<typeof import('#lib/forms/form.js').createForm>,index:number,products:any[],taxes:any[],disabled?:boolean,onRemove:()=>void}} */
	let { form, index, products, taxes, disabled = false, onRemove } = $props();
	const uid = $props.id();
	const line = $derived($form.values.lines[index]);
	const detail = createDetailQuery(
		'catalog',
		() => `/products/${line?.product_id ?? ''}`,
		() => Boolean(line?.product_id)
	);
	const taxOptions = $derived(
		[
			...taxes,
			...(line.tax_id && !taxes.some((item) => item.id === line.tax_id)
				? [{ id: line.tax_id, name: line._tax_name || 'Current tax' }]
				: [])
		].map((item) => ({ value: item.id, label: item.name }))
	);
	let defaultFor = $state('');
	const variantError = $derived(
		Object.entries($form.errors)
			.filter(
				([path]) =>
					path === `lines.${index}.variant_value_ids` ||
					path.startsWith(`lines.${index}.variant_value_ids.`)
			)
			.map(([, message]) => message)
			.join(' ')
	);
	$effect(() => {
		const product = $detail.data;
		if (product && product.id === defaultFor) {
			defaultFor = '';
			form.setValue(`lines.${index}.tax_id`, product.tax_id ?? product.tax?.id ?? null);
		}
	});
	function changeProduct(/** @type {Event} */ event) {
		const id = /** @type {HTMLSelectElement} */ (event.currentTarget).value;
		defaultFor = id;
		form.setValue(`lines.${index}.product_id`, id);
		form.setValue(`lines.${index}.variant_value_ids`, []);
		const product = products.find((item) => item.id === id);
		form.setValue(`lines.${index}._product_name`, product?.name ?? '');
		form.setValue(`lines.${index}._tax_name`, product?.tax?.name ?? '');
		form.setValue(`lines.${index}.tax_id`, product?.tax_id ?? product?.tax?.id ?? null);
	}
	function changeVariant(/** @type {any} */ attribute, /** @type {Event} */ event) {
		const value = /** @type {HTMLSelectElement} */ (event.currentTarget).value;
		const ids = line.variant_value_ids.filter(
			(/** @type {string} */ id) =>
				!attribute.values.some((/** @type {any} */ option) => option.id === id)
		);
		form.setValue(`lines.${index}.variant_value_ids`, value ? [...ids, value] : ids);
	}
</script>

<section class="border-b pb-4" aria-label={`Template line ${index + 1}`}>
	<div class="mb-3 flex items-center justify-between gap-3">
		<h4 class="text-sm font-medium">Line {index + 1}</h4>
		{#if !disabled}<Button
				size="icon"
				variant="ghost"
				aria-label={`Remove line ${index + 1}`}
				disabled={$form.isSubmitting}
				onclick={onRemove}><Trash2 /></Button
			>{/if}
	</div>
	<Field.FieldGroup class="grid gap-4 sm:grid-cols-2">
		<Field.Field data-invalid={$form.errors[`lines.${index}.product_id`] ? true : undefined}
			><Field.FieldLabel for={`${uid}-product`}>Product *</Field.FieldLabel><NativeSelect.Root
				id={`${uid}-product`}
				value={line.product_id}
				disabled={disabled || $form.isSubmitting}
				onchange={changeProduct}
				required
				aria-invalid={Boolean($form.errors[`lines.${index}.product_id`])}
				><NativeSelect.Option value="">Choose a product</NativeSelect.Option
				>{#if line.product_id && !products.some((item) => item.id === line.product_id)}<NativeSelect.Option
						value={line.product_id}
						>{line._product_name || 'Current product'} (inactive)</NativeSelect.Option
					>{/if}{#each products as product (product.id)}<NativeSelect.Option value={product.id}
						>{product.name}</NativeSelect.Option
					>{/each}</NativeSelect.Root
			>{#if $form.errors[`lines.${index}.product_id`]}<Field.FieldError
					>{$form.errors[`lines.${index}.product_id`]}</Field.FieldError
				>{/if}</Field.Field
		>
		<NumberField name={`lines.${index}.quantity`} label="Quantity" min={1} {disabled} required />
		{#if $detail.isError}<div class="sm:col-span-2">
				<ErrorState
					message="Product options could not be loaded."
					onRetry={() => $detail.refetch()}
				/>
			</div>{/if}
		{#each $detail.data?.attributes ?? [] as attribute (attribute.id)}<Field.Field
				data-invalid={variantError ? true : undefined}
				><Field.FieldLabel for={`${uid}-${attribute.id}`}>{attribute.name}</Field.FieldLabel
				><NativeSelect.Root
					id={`${uid}-${attribute.id}`}
					value={line.variant_value_ids.find((/** @type {string} */ id) =>
						attribute.values.some((/** @type {any} */ value) => value.id === id)
					) ?? ''}
					disabled={disabled || $form.isSubmitting}
					aria-invalid={Boolean(variantError)}
					onchange={(/** @type {Event} */ event) => changeVariant(attribute, event)}
					><NativeSelect.Option value="">Standard</NativeSelect.Option
					>{#each attribute.values as value (value.id)}<NativeSelect.Option value={value.id}
							>{value.name}</NativeSelect.Option
						>{/each}</NativeSelect.Root
				></Field.Field
			>{/each}
		{#if variantError}<Field.FieldError>{variantError}</Field.FieldError>{/if}
		<SelectField
			name={`lines.${index}.tax_id`}
			label="Tax"
			placeholder="No tax"
			options={taxOptions}
			disabled={disabled || Boolean(line.product_id && $detail.isPending)}
		/>
	</Field.FieldGroup>
</section>
