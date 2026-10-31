<script>
	import Form from '../Form.svelte';
	import TextField from '../TextField.svelte';
	import NumberField from '../NumberField.svelte';
	import { Button } from '../ui/button/index.js';
	/** @type {{form: ReturnType<typeof import('#lib/forms/form.js').createForm>, onSubmit: (values: any) => any}} */
	let { form, onSubmit } = $props();
</script>

<Form {form} {onSubmit}
	><TextField name="name" label="Name" required /><NumberField
		name="lines.0.quantity"
		label="Quantity"
		required
	/><Button type="submit" disabled={!$form.isValid || $form.isSubmitting}>Save</Button></Form
>
