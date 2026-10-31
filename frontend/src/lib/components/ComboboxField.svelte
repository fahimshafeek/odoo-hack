<script>
	import { tick } from 'svelte';
	import { ChevronDown } from '@lucide/svelte';
	import { getFormContext } from '#lib/forms/context.js';
	import { getFieldValue } from '#lib/forms/form.js';
	import FieldFrame from './FieldFrame.svelte';
	import { Button } from './ui/button/index.js';
	import * as Popover from './ui/popover/index.js';
	import * as Command from './ui/command/index.js';
	/** @typedef {{value: string, label: string}} Option */
	/** @type {import('#lib/forms/field-types.js').FieldProps & {loadOptions: (query: string) => Promise<Option[]>, initialLabel?: string}} */
	let {
		name,
		label,
		hint,
		required,
		disabled,
		placeholder = 'Choose an option',
		loadOptions,
		initialLabel = ''
	} = $props();
	const form = getFormContext()();
	let open = $state(false);
	let search = $state('');
	let pending = $state(false);
	let error = $state('');
	/** @type {Option[]} */
	let options = $state([]);
	let selected = $state({ value: '', label: '' });
	/** @type {HTMLButtonElement | null} */
	let trigger = $state(null);
	const value = $derived(String(getFieldValue($form.values, name) ?? ''));
	const selectedLabel = $derived(
		options.find((option) => option.value === value)?.label ||
			(selected.value === value ? selected.label : initialLabel)
	);
	$effect(() => {
		if (!open) return;
		const query = search;
		let active = true;
		pending = true;
		error = '';
		const timer = setTimeout(() => {
			loadOptions(query)
				.then((result) => {
					if (active) options = result;
				})
				.catch(() => {
					if (active) {
						options = [];
						error = 'Could not load options. Try searching again.';
					}
				})
				.finally(() => {
					if (active) pending = false;
				});
		}, 300);
		return () => {
			active = false;
			clearTimeout(timer);
		};
	});
	async function choose(/** @type {Option} */ option) {
		selected = option;
		form.setValue(name, option.value);
		open = false;
		await tick();
		trigger?.focus();
	}
</script>

<FieldFrame {name} {label} {hint} {required} {disabled}>
	{#snippet children(control)}
		<Popover.Root bind:open
			><Popover.Trigger bind:ref={trigger}>
				{#snippet child({ props })}<Button
						{...props}
						id={control.id}
						variant="outline"
						class="w-full justify-between"
						disabled={control.disabled}
						role="combobox"
						aria-expanded={open}
						aria-invalid={Boolean(control.error)}
						aria-describedby={control.describedBy}
						>{selectedLabel || placeholder}<ChevronDown data-icon="inline-end" /></Button
					>{/snippet}
			</Popover.Trigger><Popover.Content class="w-(--bits-popover-anchor-width) p-0">
				<Command.Root shouldFilter={false}
					><Command.Input
						bind:value={search}
						aria-label={`Search ${label.toLowerCase()}`}
						placeholder="Search…"
					/><Command.List aria-busy={pending}>
						{#if pending}<div role="status" class="p-4 text-sm text-muted-foreground">
								Loading options…
							</div>{:else if error}<div role="alert" class="p-4 text-sm text-destructive">
								{error}
							</div>{:else}<Command.Empty>No matching options</Command.Empty><Command.Group
								>{#each options as option (option.value)}<Command.Item
										value={option.value}
										data-checked={value === option.value}
										onSelect={() => choose(option)}>{option.label}</Command.Item
									>{/each}</Command.Group
							>{/if}
					</Command.List></Command.Root
				>
			</Popover.Content></Popover.Root
		>
	{/snippet}
</FieldFrame>
