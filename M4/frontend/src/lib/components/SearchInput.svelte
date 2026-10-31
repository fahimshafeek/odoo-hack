<script>
	import { Input } from './ui/input/index.js';
	/** @type {{value: string, onChange: (value: string) => void, placeholder?: string, label?: string}} */
	let { value, onChange, placeholder = 'Search…', label = 'Search records' } = $props();
	/** @type {ReturnType<typeof setTimeout> | undefined} */
	let timer;
	// Each mounted input owns its debounce timer; navigation cancels pending searches.
	function debounce(/** @type {Event} */ event) {
		clearTimeout(timer);
		const next = /** @type {HTMLInputElement} */ (event.currentTarget).value;
		timer = setTimeout(() => onChange(next), 300);
	}
	import { onDestroy } from 'svelte';
	onDestroy(() => clearTimeout(timer));
</script>

<Input
	type="search"
	{value}
	oninput={debounce}
	{placeholder}
	aria-label={label}
	class="w-full md:max-w-xs"
/>
