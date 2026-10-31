<script>
	import { untrack } from 'svelte';
	import { z } from 'zod';
	import { useQueryClient } from '@tanstack/svelte-query';
	import { emailSchema, personNameSchema } from '#lib/validators.js';
	import { createForm } from '#lib/forms/form.js';
	import { Form, TextField, SwitchField } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import { request } from '#src/api/resources.js';
	import { notify } from '#lib/notify.js';
	/** @type {{staff?:any,onClose:()=>void}} */
	let { staff, onClose } = $props();
	const client = useQueryClient();
	const editing = untrack(() => Boolean(staff));
	const form = untrack(() =>
		createForm({
			schema: editing
				? z.object({ full_name: personNameSchema, is_active: z.boolean() })
				: z.object({ full_name: personNameSchema, email: emailSchema }),
			initialValues: editing
				? { full_name: staff.full_name, is_active: staff.is_active }
				: { full_name: '', email: '' }
		})
	);
	async function save(/** @type {any} */ values) {
		await request(editing ? 'PATCH' : 'POST', editing ? `/staff/${staff.id}` : '/staff', {
			body: values
		});
		await client.invalidateQueries({ queryKey: ['staff'] });
		notify.success(editing ? 'Staff account updated.' : 'Invitation sent.');
		onClose();
	}
</script>

<Dialog.Root
	open
	onOpenChange={(/** @type {boolean} */ open) => {
		if (!open && !$form.isSubmitting) onClose();
	}}
	><Dialog.Content showCloseButton={!$form.isSubmitting}
		><Dialog.Header
			><Dialog.Title>{editing ? 'Edit staff account' : 'Invite staff'}</Dialog.Title
			><Dialog.Description
				>{editing
					? 'Inactive staff cannot sign in.'
					: 'An email invitation lets them set their password.'}</Dialog.Description
			></Dialog.Header
		><Form {form} onSubmit={save}
			><TextField name="full_name" label="Full name" autocomplete="name" required />{#if editing}<p
					class="text-sm text-muted-foreground"
				>
					{staff.email}
				</p>
				<SwitchField name="is_active" label="Account active" />{:else}<TextField
					name="email"
					label="Email"
					type="email"
					autocomplete="email"
					required
				/>{/if}<Dialog.Footer
				><Button variant="outline" disabled={$form.isSubmitting} onclick={onClose}>Cancel</Button
				><Button type="submit" disabled={!$form.isValid || $form.isSubmitting}
					>{$form.isSubmitting ? 'Saving…' : editing ? 'Save changes' : 'Send invitation'}</Button
				></Dialog.Footer
			></Form
		></Dialog.Content
	></Dialog.Root
>
