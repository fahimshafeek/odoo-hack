<script>
	import FieldFrame from './FieldFrame.svelte';
	import { Input } from './ui/input/index.js';
	import { Textarea } from './ui/textarea/index.js';
	import { Switch } from './ui/switch/index.js';
	import * as NativeSelect from './ui/native-select/index.js';
	/** @type {import('#lib/forms/field-types.js').FieldProps & {kind?: 'text' | 'textarea' | 'number' | 'money' | 'date' | 'select' | 'switch'}} */
	let {
		name,
		label,
		hint,
		required,
		disabled,
		kind = 'text',
		options = [],
		placeholder,
		type = 'text',
		min,
		max,
		step,
		autocomplete,
		rows = 4
	} = $props();
	function inputValue(
		/** @type {Event} */ event,
		/** @type {(value: any) => void} */ update,
		/** @type {any} */ previousValue
	) {
		const target = /** @type {HTMLInputElement} */ (event.currentTarget);
		if (kind === 'money' && !/^\d*(?:\.\d{0,2})?$/.test(target.value)) {
			target.value = String(previousValue ?? '');
			return;
		}
		update(kind === 'number' && target.value !== '' ? Number(target.value) : target.value);
	}
</script>

<FieldFrame {name} {label} {hint} {required} {disabled}>
	{#snippet children(control)}
		{#if kind === 'textarea'}
			<Textarea
				id={control.id}
				{name}
				value={control.value ?? ''}
				{placeholder}
				{required}
				disabled={control.disabled}
				{rows}
				aria-invalid={Boolean(control.error)}
				aria-describedby={control.describedBy}
				oninput={(/** @type {Event} */ event) =>
					control.update(/** @type {HTMLTextAreaElement} */ (event.currentTarget).value)}
			/>
		{:else if kind === 'select'}
			<NativeSelect.Root
				id={control.id}
				{name}
				value={control.value ?? ''}
				{required}
				disabled={control.disabled}
				aria-invalid={Boolean(control.error)}
				aria-describedby={control.describedBy}
				onchange={(/** @type {Event} */ event) =>
					control.update(/** @type {HTMLSelectElement} */ (event.currentTarget).value)}
			>
				<NativeSelect.Option value="">{placeholder ?? 'Choose an option'}</NativeSelect.Option
				>{#each options as option (option.value)}<NativeSelect.Option value={option.value}
						>{option.label}</NativeSelect.Option
					>{/each}
			</NativeSelect.Root>
		{:else if kind === 'switch'}
			<Switch
				id={control.id}
				{name}
				checked={Boolean(control.value)}
				disabled={control.disabled}
				{required}
				aria-invalid={Boolean(control.error)}
				aria-describedby={control.describedBy}
				onCheckedChange={(/** @type {boolean} */ next) => control.update(next)}
			/>
		{:else}
			<Input
				id={control.id}
				{name}
				type={kind === 'number' ? 'number' : kind === 'date' ? 'date' : type}
				value={control.value ?? ''}
				{placeholder}
				{required}
				disabled={control.disabled}
				{min}
				{max}
				step={kind === 'number' ? (step ?? 1) : step}
				{autocomplete}
				inputmode={kind === 'money' ? 'decimal' : undefined}
				aria-invalid={Boolean(control.error)}
				aria-describedby={control.describedBy}
				oninput={(/** @type {Event} */ event) => inputValue(event, control.update, control.value)}
			/>
		{/if}
	{/snippet}
</FieldFrame>
