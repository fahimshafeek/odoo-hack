<script>
	import { Popover as PopoverPrimitive } from 'bits-ui';
	/** @type {any} */
	let { open = $bindable(false), ...restProps } = $props();
</script>

<PopoverPrimitive.Root bind:open {...restProps} />
