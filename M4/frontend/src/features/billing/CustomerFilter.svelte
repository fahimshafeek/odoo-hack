<script>
	import { z } from 'zod';
	import { createForm } from '#lib/forms/form.js';
	import { Form, ComboboxField } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { loadCustomers } from './api.js';
	/** @type {{value?: string, onChange: (value: string) => void}} */
	let { value = '', onChange } = $props();
	const form = createForm({
		schema: z.object({ customer_id: z.string() }),
		initialValues: { customer_id: '' }
	});
	$effect(() => form.reset({ customer_id: value }));
</script>

<div class="w-full md:max-w-xs">
	<Form {form} onSubmit={(values) => onChange(values.customer_id)}
		><ComboboxField
			name="customer_id"
			label="Customer"
			placeholder="All customers"
			initialLabel={value ? 'Selected customer' : ''}
			loadOptions={loadCustomers}
		/>
		<div class="flex items-center gap-2">
			<Button data-active={Boolean(value)} variant="outline" type="submit" size="sm"
				>Apply customer</Button
			>{#if value}<Button
					variant="ghost"
					size="sm"
					onclick={() => {
						form.reset({ customer_id: '' });
						onChange('');
					}}>Clear</Button
				>{/if}
		</div></Form
	>
</div>
