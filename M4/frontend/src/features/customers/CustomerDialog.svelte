<script>
	import { untrack } from 'svelte';
	import { useQueryClient } from '@tanstack/svelte-query';
	import { createForm } from '#lib/forms/form.js';
	import { Form } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import { request } from '#src/api/resources.js';
	import { notify } from '#lib/notify.js';
	import CustomerFields from './CustomerFields.svelte';
	import { customerSchema, createCustomerSchema, customerValues } from './schemas.js';
	/** @type {{customer?:any,onClose:()=>void,onSaved?:(customer:any)=>void|Promise<void>}} */
	let { customer, onClose, onSaved } = $props();
	const client = useQueryClient();
	const creating = untrack(() => !customer);
	const form = untrack(() =>
		createForm({
			schema: creating ? createCustomerSchema : customerSchema,
			initialValues: {
				...customerValues(customer),
				...(creating ? { full_name: '', email: '' } : {})
			}
		})
	);
	async function save(/** @type {any} */ values) {
		const result = await request(
			creating ? 'POST' : 'PATCH',
			creating ? '/customers' : `/customers/${customer.id}`,
			{ body: values }
		);
		await client.invalidateQueries({ queryKey: ['customers'] });
		await onSaved?.(result);
		notify.success(creating ? 'Customer created.' : 'Customer updated.');
		onClose();
	}
</script>

<Dialog.Root
	open
	onOpenChange={(/** @type {boolean} */ open) => {
		if (!open && !$form.isSubmitting) onClose();
	}}
	><Dialog.Content
		class="max-h-[90svh] overflow-y-auto sm:max-w-lg"
		showCloseButton={!$form.isSubmitting}
		><Dialog.Header
			><Dialog.Title>{creating ? 'Add customer' : 'Edit customer'}</Dialog.Title><Dialog.Description
				>{creating
					? 'An invitation will be emailed to the customer.'
					: 'Update billing and contact information.'}</Dialog.Description
			></Dialog.Header
		><Form {form} onSubmit={save}
			><CustomerFields {creating} /><Dialog.Footer
				><Button variant="outline" disabled={$form.isSubmitting} onclick={onClose}>Cancel</Button
				><Button type="submit" disabled={!$form.isValid || $form.isSubmitting}
					>{$form.isSubmitting ? 'Saving…' : creating ? 'Add customer' : 'Save changes'}</Button
				></Dialog.Footer
			></Form
		></Dialog.Content
	></Dialog.Root
>
