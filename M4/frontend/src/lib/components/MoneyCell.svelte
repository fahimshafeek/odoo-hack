<script>
	import { formatMoney } from '#lib/format.js';
	/** @type {{value: string | number | null}} */
	let { value } = $props();
</script>

<span class="block text-right tabular-nums">{formatMoney(value)}</span>
