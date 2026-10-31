<script>
	import { Popover as PopoverPrimitive } from 'bits-ui';
	/** @type {any} */
	let { ...restProps } = $props();
</script>

<PopoverPrimitive.Portal {...restProps} />
