<script>
	import { Trash2 } from '@lucide/svelte';
	import { createDetailQuery } from '#src/api/resources.js';
	import { NumberField, SelectField, MoneyCell, ErrorState } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as NativeSelect from '#lib/components/ui/native-select/index.js';
	import * as Field from '#lib/components/ui/field/index.js';
	/** @type {{form: ReturnType<typeof import('#lib/forms/form.js').createForm>, index: number, products: any[], taxes: any[], minimum: number, preview?: any, disabled?: boolean, onRemove: () => void}} */
	let { form, index, products, taxes, minimum, preview, disabled = false, onRemove } = $props();
	const line = $derived($form.values.lines[index]);
	const product = createDetailQuery(
		'catalog',
		() => `/products/${line?.product_id ?? ''}`,
		() => Boolean(line?.product_id)
	);
	let resetting = $state('');
	let hydrated = $state(false);
	const uid = $props.id();
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
	const taxOptions = $derived(
		taxes.map((/** @type {any} */ tax) => ({
			value: tax.id,
			label: `${tax.name} (${tax.rate_percent}%)`
		}))
	);
	$effect(() => {
		const detail = $product.data;
		if (!detail || detail.id !== line?.product_id) return;
		if (resetting === detail.id) {
			resetting = '';
			form.setValue(`lines.${index}.tax_id`, detail.tax_id ?? detail.tax?.id ?? null);
		}
		if (!hydrated && line?._snapshot?.length && !line.variant_value_ids.length) {
			hydrated = true;
			const ids = line._snapshot.flatMap((/** @type {any} */ selection) => {
				const attribute = (detail.attributes ?? []).find(
					(/** @type {any} */ item) => item.name === selection.attribute
				);
				const value = attribute?.values?.find(
					(/** @type {any} */ item) => item.name === selection.value
				);
				return value ? [value.id] : [];
			});
			form.setValue(`lines.${index}.variant_value_ids`, ids);
		}
	});
	function changeProduct(/** @type {Event} */ event) {
		const id = /** @type {HTMLSelectElement} */ (event.currentTarget).value;
		resetting = id;
		hydrated = true;
		form.setValue(`lines.${index}.product_id`, id);
		form.setValue(`lines.${index}.variant_value_ids`, []);
		form.setValue(`lines.${index}.tax_id`, null);
	}
	function changeVariant(/** @type {any} */ attribute, /** @type {Event} */ event) {
		const selected = /** @type {HTMLSelectElement} */ (event.currentTarget).value;
		const previous = line.variant_value_ids.filter(
			(/** @type {string} */ id) =>
				!attribute.values.some((/** @type {any} */ option) => option.id === id)
		);
		form.setValue(
			`lines.${index}.variant_value_ids`,
			selected ? [...previous, selected] : previous
		);
	}
</script>

<section aria-label={`Product line ${index + 1}`} class="border-b pb-4">
	<div class="mb-3 flex items-center justify-between gap-3">
		<h3 class="text-sm font-medium">Line {index + 1}</h3>
		<Button
			variant="ghost"
			size="icon"
			aria-label={`Remove line ${index + 1}`}
			disabled={disabled || $form.isSubmitting}
			onclick={onRemove}><Trash2 /></Button
		>
	</div>
	<Field.FieldGroup class="grid gap-4 md:grid-cols-2">
		<Field.Field
			data-invalid={$form.errors[`lines.${index}.product_id`] ? true : undefined}
			data-disabled={disabled || $form.isSubmitting ? true : undefined}
			><Field.FieldLabel for={`${uid}-product`}>Product *</Field.FieldLabel><NativeSelect.Root
				id={`${uid}-product`}
				value={line?.product_id ?? ''}
				disabled={disabled || $form.isSubmitting}
				aria-invalid={Boolean($form.errors[`lines.${index}.product_id`])}
				aria-describedby={$form.errors[`lines.${index}.product_id`]
					? `${uid}-product-error`
					: undefined}
				required
				onchange={changeProduct}
				><NativeSelect.Option value="">Choose a product</NativeSelect.Option
				>{#each products as item (item.id)}<NativeSelect.Option value={item.id}
						>{item.name}</NativeSelect.Option
					>{/each}</NativeSelect.Root
			>{#if $form.errors[`lines.${index}.product_id`]}<Field.FieldError id={`${uid}-product-error`}
					>{$form.errors[`lines.${index}.product_id`]}</Field.FieldError
				>{/if}</Field.Field
		>
		<NumberField
			name={`lines.${index}.quantity`}
			label="Quantity"
			min={minimum}
			hint={`Minimum ${minimum} for this plan.`}
			{disabled}
			required
		/>
		{#if $product.isError}<div class="md:col-span-2">
				<ErrorState
					message="We could not load this product’s options."
					onRetry={() => $product.refetch()}
				/>
			</div>{/if}
		{#each $product.data?.attributes ?? [] as attribute (attribute.id)}<Field.Field
				data-invalid={variantError ? true : undefined}
				data-disabled={disabled || $form.isSubmitting ? true : undefined}
				><Field.FieldLabel for={`${uid}-${attribute.id}`}>{attribute.name}</Field.FieldLabel
				><NativeSelect.Root
					id={`${uid}-${attribute.id}`}
					disabled={disabled || $form.isSubmitting}
					value={line.variant_value_ids.find((/** @type {string} */ id) =>
						attribute.values.some((/** @type {any} */ option) => option.id === id)
					) ?? ''}
					onchange={(/** @type {Event} */ event) => changeVariant(attribute, event)}
					aria-invalid={Boolean(variantError)}
					aria-describedby={variantError ? `${uid}-variant-error` : undefined}
					><NativeSelect.Option value="">Standard</NativeSelect.Option
					>{#each attribute.values as option (option.id)}<NativeSelect.Option value={option.id}
							>{option.name}</NativeSelect.Option
						>{/each}</NativeSelect.Root
				></Field.Field
			>{/each}
		{#if variantError}<div class="md:col-span-2">
				<Field.FieldError id={`${uid}-variant-error`}>{variantError}</Field.FieldError>
			</div>{/if}
		<SelectField
			name={`lines.${index}.tax_id`}
			label="Tax"
			placeholder="No tax"
			options={taxOptions}
			disabled={disabled || Boolean(line?.product_id && $product.isPending)}
		/>
	</Field.FieldGroup>
	<dl class="mt-4 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
		<div>
			<dt class="text-muted-foreground">Unit price</dt>
			<dd class="mt-1 text-sm"><MoneyCell value={preview?.unit_price} /></dd>
		</div>
		<div>
			<dt class="text-muted-foreground">Amount</dt>
			<dd class="mt-1 text-sm"><MoneyCell value={preview?.amount} /></dd>
		</div>
		<div>
			<dt class="text-muted-foreground">Tax</dt>
			<dd class="mt-1 text-sm"><MoneyCell value={preview?.tax_amount} /></dd>
		</div>
		<div>
			<dt class="text-muted-foreground">Line total</dt>
			<dd class="mt-1 text-sm font-medium"><MoneyCell value={preview?.total} /></dd>
		</div>
	</dl>
</section>
