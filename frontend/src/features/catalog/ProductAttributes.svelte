<script>
	import { Plus, Pencil, Trash2 } from '@lucide/svelte';
	import { createForm } from '#lib/forms/form.js';
	import { createActionMutation } from '#src/api/resources.js';
	import { notify } from '#lib/notify.js';
	import { Form, TextField, MoneyField, MoneyCell, ConfirmDialog } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import * as Field from '#lib/components/ui/field/index.js';
	import { attributeSchema } from './forms.js';
	/** @type {{product:any,readonly?:boolean}} */
	let { product, readonly = false } = $props();
	let open = $state(false);
	let attributeId = $state('');
	let removing = $state('');
	const form = createForm({ schema: attributeSchema, initialValues: { name: '', values: [] } });
	const create = createActionMutation(
		'catalog',
		'POST',
		() => `/products/${product.id}/attributes`,
		() => {
			open = false;
			notify.success('Attribute added.');
		}
	);
	const update = createActionMutation(
		'catalog',
		'PATCH',
		() => `/products/${product.id}/attributes/${attributeId}`,
		() => {
			open = false;
			notify.success('Attribute saved.');
		}
	);
	const remove = createActionMutation(
		'catalog',
		'DELETE',
		() => `/products/${product.id}/attributes/${removing}`,
		() => notify.success('Attribute removed.')
	);
	function edit(/** @type {any} */ attribute) {
		attributeId = attribute?.id ?? '';
		form.reset({
			name: attribute?.name ?? '',
			values: (attribute?.values ?? [{ name: '', extra_price: '0.00' }]).map(
				(/** @type {any} */ value) => ({
					_key: value.id ?? crypto.randomUUID(),
					...(value.id ? { id: value.id } : {}),
					name: value.name,
					extra_price: value.extra_price
				})
			)
		});
		open = true;
	}
	function addValue() {
		form.setValue('values', [
			...$form.values.values,
			{ _key: crypto.randomUUID(), name: '', extra_price: '0.00' }
		]);
	}
	function removeValue(/** @type {number} */ index) {
		form.setValue(
			'values',
			$form.values.values.filter((/** @type {any} */ _, /** @type {number} */ i) => i !== index)
		);
	}
	async function submit(/** @type {any} */ values) {
		if (readonly) return;
		await (attributeId ? $update : $create).mutateAsync({ body: values });
	}
</script>

<section class="border-t pt-4" aria-labelledby="variant-options-heading">
	<div class="mb-4 flex items-center justify-between gap-3">
		<h3 id="variant-options-heading" class="text-sm font-medium">Variant attributes</h3>
		{#if !readonly}<Button variant="outline" onclick={() => edit(undefined)}
				><Plus data-icon="inline-start" />Add attribute</Button
			>{/if}
	</div>
	<div class="flex flex-col gap-4">
		{#each product.attributes ?? [] as attribute (attribute.id)}<div>
				<div class="mb-2 flex items-center justify-between gap-3">
					<p class="text-sm font-medium">{attribute.name}</p>
					{#if !readonly}<div class="flex gap-1">
							<Button
								size="icon"
								variant="ghost"
								aria-label={`Edit ${attribute.name}`}
								onclick={() => edit(attribute)}><Pencil /></Button
							><Button
								size="icon"
								variant="ghost"
								aria-label={`Delete ${attribute.name}`}
								onclick={() => (removing = attribute.id)}><Trash2 /></Button
							>
						</div>{/if}
				</div>
				<dl class="grid grid-cols-2 gap-2 text-sm">
					{#each attribute.values as value (value.id)}<dt class="text-muted-foreground">
							{value.name}
						</dt>
						<dd class="text-right"><MoneyCell value={value.extra_price} /></dd>{/each}
				</dl>
			</div>{:else}<p class="text-sm text-muted-foreground">No variant attributes.</p>{/each}
	</div>
</section>
<Dialog.Root bind:open
	><Dialog.Content class="max-h-[85svh] overflow-y-auto sm:max-w-xl"
		><Dialog.Header
			><Dialog.Title>{attributeId ? 'Edit' : 'Add'} attribute</Dialog.Title><Dialog.Description
				>Set the available values and their price adjustments.</Dialog.Description
			></Dialog.Header
		><Form {form} onSubmit={submit}
			><TextField name="name" label="Attribute name" required />
			<div class="flex items-center justify-between gap-3">
				<h4 class="text-sm font-medium">Values</h4>
				<Button variant="outline" onclick={addValue} disabled={$form.isSubmitting}
					><Plus data-icon="inline-start" />Add value</Button
				>
			</div>
			{#each $form.values.values as value, index (value._key)}<Field.FieldGroup
					class="grid grid-cols-[1fr_1fr_auto] items-start gap-3"
					><TextField name={`values.${index}.name`} label="Value name" required /><MoneyField
						name={`values.${index}.extra_price`}
						label="Extra price"
						required
					/><Button
						class="mt-7"
						size="icon"
						variant="ghost"
						aria-label={`Remove value ${index + 1}`}
						disabled={$form.isSubmitting}
						onclick={() => removeValue(index)}><Trash2 /></Button
					></Field.FieldGroup
				>{/each}{#if $form.errors.values}<Field.FieldError>{$form.errors.values}</Field.FieldError
				>{/if}
			<div class="flex justify-end border-t pt-4">
				<Button type="submit" disabled={!$form.isValid || $form.isSubmitting}
					>{$form.isSubmitting ? 'Saving…' : 'Save attribute'}</Button
				>
			</div></Form
		></Dialog.Content
	></Dialog.Root
>
<ConfirmDialog
	open={Boolean(removing)}
	onOpenChange={(value) => {
		if (!value) removing = '';
	}}
	title="Delete attribute?"
	description="This removes its variant values from the product. Existing subscription snapshots are retained."
	confirmLabel="Delete attribute"
	destructive
	onConfirm={() => $remove.mutateAsync({})}
/>
