<script>
	import { Dialog as SheetPrimitive } from 'bits-ui';
	/** @type {any} */
	let { open = $bindable(false), ...restProps } = $props();
</script>

<SheetPrimitive.Root bind:open {...restProps} />
