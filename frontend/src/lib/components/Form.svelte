<script>
	import { tick } from 'svelte';
	import { setFormContext } from '#lib/forms/context.js';
	import * as Field from './ui/field/index.js';
	import ErrorState from './ErrorState.svelte';
	/** @type {{form: ReturnType<typeof import('#lib/forms/form.js').createForm>, onSubmit: (values: any) => any | Promise<any>, children: import('svelte').Snippet, isSubmitting?: boolean}} */
	let { form, onSubmit, children, isSubmitting = false } = $props();
	setFormContext(() => form);
	async function submit(/** @type {SubmitEvent} */ event) {
		event.preventDefault();
		const element = /** @type {HTMLFormElement} */ (event.currentTarget);
		if (isSubmitting) return;
		const accepted = await form.submit(onSubmit);
		if (!accepted) {
			await tick();
			/** @type {HTMLElement | null} */ (element.querySelector('[aria-invalid="true"]'))?.focus();
		}
	}
</script>

<form onsubmit={submit} novalidate aria-busy={$form.isSubmitting || isSubmitting}>
	<Field.FieldGroup
		>{#if $form.formError}<ErrorState
				message={$form.formError}
			/>{/if}{@render children()}</Field.FieldGroup
	>
</form>
