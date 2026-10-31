<script>
	import FormField from './FormField.svelte';
	/** @type {import('#lib/forms/field-types.js').FieldProps} */
	let props = $props();
</script>

<FormField {...props} kind="date" />
