<script>
	import { TextField, TextAreaField } from '#lib/components/index.js';
	/** @type {{creating?: boolean}} */
	let { creating = false } = $props();
</script>

{#if creating}<TextField
		name="full_name"
		label="Full name"
		autocomplete="name"
		required
	/><TextField name="email" type="email" label="Email" autocomplete="email" required />{/if}
<TextField name="company_name" label="Company" autocomplete="organization" />
<TextField name="phone" type="tel" label="Phone" autocomplete="tel" />
<TextAreaField
	name="billing_address"
	label="Billing address"
	autocomplete="street-address"
	rows={3}
/>
<TextField name="tax_id" label="Tax ID" />
