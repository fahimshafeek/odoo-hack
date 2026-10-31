<script>
	import { getFormContext } from '#lib/forms/context.js';
	import { getFieldValue } from '#lib/forms/form.js';
	import * as Field from './ui/field/index.js';
	/** @type {{name: string, label: string, hint?: string, required?: boolean, disabled?: boolean, children: import('svelte').Snippet<[{id: string, value: any, error: string | undefined, describedBy: string | undefined, disabled: boolean, update: (value: any) => void}]>}} */
	let { name, label, hint, required = false, disabled = false, children } = $props();
	const form = getFormContext()();
	const uid = $props.id();
	const id = $derived(`${uid}-${name.replaceAll('.', '-')}`);
	const error = $derived($form.errors[name]);
	const value = $derived(getFieldValue($form.values, name));
	const describedBy = $derived(
		[hint ? `${id}-hint` : '', error ? `${id}-error` : ''].filter(Boolean).join(' ') || undefined
	);
</script>

<Field.Field
	data-invalid={error ? true : undefined}
	data-disabled={disabled || $form.isSubmitting ? true : undefined}
>
	<Field.FieldLabel for={id}
		>{label}{#if required}<span aria-hidden="true"> *</span>{/if}</Field.FieldLabel
	>
	{@render children({
		id,
		value,
		error,
		describedBy,
		disabled: disabled || $form.isSubmitting,
		update: (next) => form.setValue(name, next)
	})}
	{#if hint}<Field.FieldDescription id={`${id}-hint`}>{hint}</Field.FieldDescription>{/if}
	{#if error}<Field.FieldError id={`${id}-error`} aria-live="polite">{error}</Field.FieldError>{/if}
</Field.Field>
