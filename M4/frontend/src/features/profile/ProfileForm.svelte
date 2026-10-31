<script>
	import { untrack } from 'svelte';
	import { useQueryClient } from '@tanstack/svelte-query';
	import { createForm } from '#lib/forms/form.js';
	import { Form } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { notify } from '#lib/notify.js';
	import { request } from '#src/api/resources.js';
	import CustomerFields from '../customers/CustomerFields.svelte';
	import { customerSchema, customerValues } from '../customers/schemas.js';
	/** @type {{profile:any}} */ let { profile } = $props();
	const client = useQueryClient();
	const form = untrack(() =>
		createForm({ schema: customerSchema, initialValues: customerValues(profile) })
	);
	async function save(/** @type {any} */ values) {
		const updated = await request('PATCH', '/me/profile', { body: values });
		form.reset(customerValues(updated));
		await client.invalidateQueries({ queryKey: ['profile'] });
		notify.success('Profile updated.');
	}
</script>

<Form {form} onSubmit={save}
	><div class="grid gap-4 text-sm sm:grid-cols-2">
		<div>
			<p class="mb-1 text-muted-foreground">Name</p>
			<p>{profile.full_name || '—'}</p>
		</div>
		<div>
			<p class="mb-1 text-muted-foreground">Email</p>
			<p class="break-all">{profile.email || '—'}</p>
		</div>
	</div>
	<CustomerFields />
	<div>
		<Button type="submit" disabled={!$form.isValid || $form.isSubmitting}
			>{$form.isSubmitting ? 'Saving…' : 'Save changes'}</Button
		>
	</div></Form
>
